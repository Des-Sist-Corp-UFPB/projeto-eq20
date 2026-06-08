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
    ) -> list[OcorrenciaModel]:
        """Lista ocorrências aplicando filtros e regras de toggle."""
        allow_personal = self.toggle_repo.get_value("allow_personal_occurrences", True)

        exclude_category = None
        if not allow_personal:
            exclude_category = "segurança pública"

        return self.ocorrencia_repo.list_all(
            category=category,
            status=status_filter,
            exclude_category=exclude_category,
        )

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

        return self.ocorrencia_repo.create(
            title=ocorrencia.title,
            category=ocorrencia.category,
            description=ocorrencia.description,
            lat=ocorrencia.lat,
            lng=ocorrencia.lng,
            photo=ocorrencia.photo,
            type=ocorrencia.type,
            user_id=current_user.id,
        )

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

        return self.ocorrencia_repo.update_status(db_ocorrencia, status_update.status)

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
