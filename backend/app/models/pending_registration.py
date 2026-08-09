"""Modelo para registro pendente de verificação."""

from sqlalchemy import Column, Integer, String, DateTime
from app.models.base import Base


class PendingRegistrationModel(Base):
    """Modelo SQLAlchemy para a tabela de registros pendentes."""

    __tablename__ = "pending_registrations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
