"""Serviço de lógica de negócio para logs de auditoria."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.audit_log import AuditLogModel


class AuditLogService:
    """Serviço para gerenciamento dos logs de auditoria."""

    def __init__(self, db: Session) -> None:
        self.repo = AuditLogRepository(db)

    def log(
        self,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuditLogModel:
        """Grava uma entrada de auditoria de forma isolada."""
        return self.repo.create(
            action=action,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            user_email=user_email,
            details=details,
        )

    def list_logs(self) -> List[AuditLogModel]:
        """Lista todos os logs de auditoria."""
        return self.repo.list_all()
