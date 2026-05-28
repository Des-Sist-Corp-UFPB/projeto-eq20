"""Modelo de usuário."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserModel(Base):
    """Modelo SQLAlchemy para a tabela de usuários."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(30), default="user", nullable=False)  # "user" or "admin"
    reset_token = Column(String(100), nullable=True)  # Mock reset token for password recovery

    ocorrencias = relationship("OcorrenciaModel", back_populates="owner")
