from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.feature_toggle import FeatureToggleModel
from app.models.user import UserModel
from app.repositories.feature_toggle_repository import FeatureToggleRepository
from app.repositories.ocorrencia_repository import OcorrenciaRepository
from app.repositories.user_repository import UserRepository


class AdminService:
    """Lógica de negócio para funcionalidades administrativas."""

    def __init__(self, db: Session) -> None:
        self.toggle_repo = FeatureToggleRepository(db)
        self.ocorrencia_repo = OcorrenciaRepository(db)
        self.user_repo = UserRepository(db)

    def get_toggles(self) -> list[FeatureToggleModel]:
        """Retorna todos os feature toggles."""
        return self.toggle_repo.get_all()

    def update_toggle(self, key: str, value: bool, admin_user: UserModel) -> FeatureToggleModel:
        """Cria ou atualiza um feature toggle."""
        toggle = self.toggle_repo.upsert(key, value)
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.toggle_repo.db)
            audit_service.log(
                action="ADMIN_TOGGLE_UPDATE",
                resource="feature_toggle",
                resource_id=key,
                user_id=admin_user.id,
                user_email=admin_user.email,
                details=f"Toggle '{key}' alterado para {value}."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (toggle update): {e}")
        return toggle

    def batch_resolve(self, admin_user: UserModel) -> dict:
        """Resolve todas as ocorrências pendentes."""
        affected = self.ocorrencia_repo.batch_resolve()
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.ocorrencia_repo.db)
            audit_service.log(
                action="ADMIN_BATCH_RESOLVE",
                resource="ocorrencia",
                resource_id="all",
                user_id=admin_user.id,
                user_email=admin_user.email,
                details=f"Batch resolve executado. {affected} ocorrências resolvidas."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (batch resolve): {e}")
        return {"message": f"Ação executada com sucesso. {affected} ocorrências foram resolvidas."}

    def list_users(self) -> list[UserModel]:
        """Lista todos os usuários."""
        return self.user_repo.list_all()

    def delete_user(self, user_id: int, admin_user: UserModel) -> None:
        """Exclui um usuário do sistema."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="ADMIN_DELETE_USER_FAILURE",
                    resource="user",
                    resource_id=str(user_id),
                    user_id=admin_user.id,
                    user_email=admin_user.email,
                    details=f"Falha ao excluir usuário {user_id}: usuário não encontrado."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha delete user - não encontrado): {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        if user.role == "admin":
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="ADMIN_DELETE_USER_FAILURE",
                    resource="user",
                    resource_id=str(user_id),
                    user_id=admin_user.id,
                    user_email=admin_user.email,
                    details=f"Falha ao excluir usuário '{user.email}': não é possível excluir um administrador."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha delete user - administrador): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível excluir um administrador.",
            )
        user_email = user.email
        self.user_repo.delete(user)
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.user_repo.db)
            audit_service.log(
                action="ADMIN_DELETE_USER",
                resource="user",
                resource_id=str(user_id),
                user_id=admin_user.id,
                user_email=admin_user.email,
                details=f"Usuário '{user_email}' excluído do sistema pelo administrador."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (delete user): {e}")

    def ban_user(self, user_id: int, duration_minutes: int, admin_user: UserModel) -> UserModel:
        """Bane temporariamente ou desbane um usuário."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="ADMIN_BAN_USER_FAILURE",
                    resource="user",
                    resource_id=str(user_id),
                    user_id=admin_user.id,
                    user_email=admin_user.email,
                    details=f"Falha ao banir/desbanir usuário {user_id}: usuário não encontrado."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha ban user - não encontrado): {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        if user.role == "admin":
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="ADMIN_BAN_USER_FAILURE",
                    resource="user",
                    resource_id=str(user_id),
                    user_id=admin_user.id,
                    user_email=admin_user.email,
                    details=f"Falha ao banir/desbanir usuário '{user.email}': não é possível banir um administrador."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha ban user - administrador): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível banir um administrador.",
            )

        if duration_minutes <= 0:
            banned_until = None
            action_name = "ADMIN_UNBAN_USER"
            log_details = f"Usuário '{user.email}' desbanido pelo administrador."
        else:
            from datetime import datetime, UTC, timedelta
            banned_until = datetime.now(UTC) + timedelta(minutes=duration_minutes)
            action_name = "ADMIN_BAN_USER"
            log_details = f"Usuário '{user.email}' banido por {duration_minutes} minutos."

        updated_user = self.user_repo.update_ban(user, banned_until)
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.user_repo.db)
            audit_service.log(
                action=action_name,
                resource="user",
                resource_id=str(user_id),
                user_id=admin_user.id,
                user_email=admin_user.email,
                details=log_details
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (ban user): {e}")
        return updated_user
