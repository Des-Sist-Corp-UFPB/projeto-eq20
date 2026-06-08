"""Modelo de ocorrência."""

from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class OcorrenciaModel(Base):
    """Modelo SQLAlchemy para a tabela de ocorrências."""

    __tablename__ = "ocorrencias"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    status = Column(String(30), default="pendente", nullable=False)
    photo = Column(String(500), nullable=True)
    type = Column(String(30), default="urbana", nullable=False)  # "urbana" or "pessoal"
    date = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    owner = relationship("UserModel", back_populates="ocorrencias")
