"""Repositório de logs de auditoria."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLogModel


class AuditLogRepository:
    """Operações de banco de dados para a entidade AuditLog."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        details: Optional[str] = None,
    ) -> AuditLogModel:
        """Cria e salva um novo log de auditoria."""
        log = AuditLogModel(
            action=action,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            user_email=user_email,
            details=details,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def list_all(self) -> List[AuditLogModel]:
        """Retorna todos os logs de auditoria ordenados por timestamp decrescente."""
        return self.db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).all()
