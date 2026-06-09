"""Serviço de lógica de negócio de ocorrências."""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ocorrencia import OcorrenciaModel
from app.models.user import UserModel
from app.repositories.feature_toggle_repository import FeatureToggleRepository
from app.repositories.ocorrencia_repository import OcorrenciaRepository
from app.schemas.ocorrencia import OcorrenciaCreate, OcorrenciaStatusUpdate


class OcorrenciaService:
    """Lógica de negócio para gerenciamento de ocorrências."""

    def __init__(self, db: Session) -> None:
        self.ocorrencia_repo = OcorrenciaRepository(db)
        self.toggle_repo = FeatureToggleRepository(db)

    def list_ocorrencias(
        self,
        category: Optional[str] = None,
        status_filter: Optional[str] = None,
        current_user: Optional[UserModel] = None,
    ) -> list[OcorrenciaModel]:
        """Lista ocorrências aplicando filtros, regras de toggle, populando campos dinâmicos e ordenando por urgência se admin."""
        allow_personal = self.toggle_repo.get_value("allow_personal_occurrences", True)

        exclude_category = None
        if not allow_personal:
            exclude_category = "segurança pública"

        occurrences = self.ocorrencia_repo.list_all(
            category=category,
            status=status_filter,
            exclude_category=exclude_category,
        )

        # Preenche os campos dinâmicos para cada ocorrência
        self._populate_dynamic_fields(occurrences, current_user)

        # Se o usuário logado for administrador, ordena a lista por urgência decrescente
        if current_user and current_user.role == "admin":
            occurrences.sort(key=lambda o: o.urgency_score or 0.0, reverse=True)

        return occurrences

    def _populate_dynamic_fields(
        self,
        ocorrencias: list[OcorrenciaModel],
        current_user: Optional[UserModel],
    ) -> list[OcorrenciaModel]:
        """Popula os campos dinâmicos que dependem do contexto de autenticação e permissões."""
        for o in ocorrencias:
            # 1. is_affected: true se o usuário logado declarou-se afetado
            if current_user:
                o.is_affected = any(u.id == current_user.id for u in o.afetados) if o.afetados else False
            else:
                o.is_affected = False

            # 2. affected_count & urgency_score: exibidos apenas para administradores
            if current_user and current_user.role == "admin":
                o.affected_count = len(o.afetados) if o.afetados else 0
                o.urgency_score = o.get_urgency_score()
            else:
                o.affected_count = None
                o.urgency_score = None
        return ocorrencias

    def create_ocorrencia(
        self,
        ocorrencia: OcorrenciaCreate,
        current_user: UserModel,
    ) -> OcorrenciaModel:
        """Cria uma nova ocorrência com verificações de toggles e permissões."""
        # Check Read-Only Mode toggle
        read_only = self.toggle_repo.get_value("read_only_mode", False)
        if read_only and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A plataforma está no modo SOMENTE LEITURA por ordem administrativa.",
            )

        # Check Personal Occurrences toggle
        allow_personal = self.toggle_repo.get_value("allow_personal_occurrences", True)
        if ocorrencia.category == "segurança pública" and not allow_personal:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O cadastro de ocorrências de segurança pública foi desativado temporariamente.",
            )

        db_occ = self.ocorrencia_repo.create(
            title=ocorrencia.title,
            category=ocorrencia.category,
            description=ocorrencia.description,
            lat=ocorrencia.lat,
            lng=ocorrencia.lng,
            photo=ocorrencia.photo,
            type=ocorrencia.type,
            user_id=current_user.id,
        )
        return self._populate_dynamic_fields([db_occ], current_user)[0]

    def update_status(
        self,
        ocorrencia_id: int,
        status_update: OcorrenciaStatusUpdate,
        current_user: UserModel,
    ) -> OcorrenciaModel:
        """Atualiza o status de uma ocorrência com verificação de permissões."""
        # Check Read-Only Mode toggle
        read_only = self.toggle_repo.get_value("read_only_mode", False)
        if read_only and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A plataforma está no modo SOMENTE LEITURA por ordem administrativa.",
            )

        db_ocorrencia = self.ocorrencia_repo.get_by_id(ocorrencia_id)
        if not db_ocorrencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ocorrência não encontrada.",
            )

        # Only the admin can update occurrence status
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o administrador pode alterar o estado de uma ocorrência.",
            )

        updated_occ = self.ocorrencia_repo.update_status(db_ocorrencia, status_update.status)
        return self._populate_dynamic_fields([updated_occ], current_user)[0]

    def delete_ocorrencia(
        self,
        ocorrencia_id: int,
        current_user: UserModel,
    ) -> None:
        """Remove uma ocorrência com verificação de permissões."""
        # Check Read-Only Mode toggle
        read_only = self.toggle_repo.get_value("read_only_mode", False)
        if read_only and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A plataforma está no modo SOMENTE LEITURA por ordem administrativa.",
            )

        db_ocorrencia = self.ocorrencia_repo.get_by_id(ocorrencia_id)
        if not db_ocorrencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ocorrência não encontrada.",
            )

        # Only owner or admin can delete
        if db_ocorrencia.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para excluir esta ocorrência.",
            )

        self.ocorrencia_repo.delete(db_ocorrencia)

    def toggle_afetado(
        self,
        ocorrencia_id: int,
        current_user: UserModel,
    ) -> OcorrenciaModel:
        """Adiciona ou remove o usuário logado da lista de afetados da ocorrência."""
        # Check Read-Only Mode toggle
        read_only = self.toggle_repo.get_value("read_only_mode", False)
        if read_only and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A plataforma está no modo SOMENTE LEITURA por ordem administrativa.",
            )

        db_ocorrencia = self.ocorrencia_repo.get_by_id(ocorrencia_id)
        if not db_ocorrencia:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ocorrência não encontrada.",
            )

        # O criador da ocorrência não pode se declarar afetado
        if db_ocorrencia.user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O criador da ocorrência não pode declarar-se afetado por ela.",
            )

        # Toggle da relação
        if current_user in db_ocorrencia.afetados:
            db_ocorrencia.afetados.remove(current_user)
        else:
            db_ocorrencia.afetados.append(current_user)

        self.ocorrencia_repo.db.commit()
        self.ocorrencia_repo.db.refresh(db_ocorrencia)

        return self._populate_dynamic_fields([db_ocorrencia], current_user)[0]

