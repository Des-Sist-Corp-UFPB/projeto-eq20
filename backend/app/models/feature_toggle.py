"""Modelo de feature toggle."""

from sqlalchemy import Column, String, Boolean

from app.models.base import Base


class FeatureToggleModel(Base):
    """Modelo SQLAlchemy para a tabela de feature toggles."""

    __tablename__ = "feature_toggles"

    key = Column(String(50), primary_key=True, index=True)
    value = Column(Boolean, default=True, nullable=False)
