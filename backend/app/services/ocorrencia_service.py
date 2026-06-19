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
        current_user: Optional[UserModel],
    ) -> OcorrenciaModel:
        """Cria uma nova ocorrência com verificações de toggles e permissões."""
        # Check Read-Only Mode toggle
        read_only = self.toggle_repo.get_value("read_only_mode", False)
        is_admin = current_user and current_user.role == "admin"
        if read_only and not is_admin:
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
            user_id=current_user.id if current_user else None,
        )

        # Loga na auditoria
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.ocorrencia_repo.db)
            audit_service.log(
                action="OCORRENCIA_CREATE",
                resource="ocorrencia",
                resource_id=str(db_occ.id),
                user_id=current_user.id if current_user else None,
                user_email=current_user.email if current_user else "Anônimo",
                details=f"Ocorrência '{db_occ.title}' criada com sucesso."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (criação de ocorrência): {e}")

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

        # Loga na auditoria
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.ocorrencia_repo.db)
            audit_service.log(
                action="OCORRENCIA_STATUS_UPDATE",
                resource="ocorrencia",
                resource_id=str(updated_occ.id),
                user_id=current_user.id,
                user_email=current_user.email,
                details=f"Status da ocorrência alterado para '{status_update.status}'."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (atualização de status): {e}")

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

        occ_id = db_ocorrencia.id
        occ_title = db_ocorrencia.title
        self.ocorrencia_repo.delete(db_ocorrencia)

        # Loga na auditoria
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.ocorrencia_repo.db)
            audit_service.log(
                action="OCORRENCIA_DELETE",
                resource="ocorrencia",
                resource_id=str(occ_id),
                user_id=current_user.id,
                user_email=current_user.email,
                details=f"Ocorrência '{occ_title}' deletada com sucesso."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (exclusão de ocorrência): {e}")

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
        is_now_affected = False
        if current_user in db_ocorrencia.afetados:
            db_ocorrencia.afetados.remove(current_user)
        else:
            db_ocorrencia.afetados.append(current_user)
            is_now_affected = True

        self.ocorrencia_repo.db.commit()
        self.ocorrencia_repo.db.refresh(db_ocorrencia)

        # Loga na auditoria
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.ocorrencia_repo.db)
            action_desc = "declarou-se afetado por" if is_now_affected else "removeu declaração de afetado de"
            audit_service.log(
                action="OCORRENCIA_TOGGLE_AFETADO",
                resource="ocorrencia",
                resource_id=str(db_ocorrencia.id),
                user_id=current_user.id,
                user_email=current_user.email,
                details=f"Usuário {action_desc} ocorrência '{db_ocorrencia.title}'."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (toggle afetado): {e}")

        return self._populate_dynamic_fields([db_ocorrencia], current_user)[0]

