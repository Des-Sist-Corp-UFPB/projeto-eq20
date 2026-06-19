"""Modelo de log de auditoria."""

from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text

from app.models.base import Base


class AuditLogModel(Base):
    """Modelo SQLAlchemy para a tabela de logs de auditoria."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(100), nullable=True)
    action = Column(String(50), nullable=False)
    resource = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
