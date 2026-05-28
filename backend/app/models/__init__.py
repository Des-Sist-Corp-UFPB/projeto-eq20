"""Modelos SQLAlchemy da aplicação.

Re-exporta Base e todos os models para facilitar imports e
garantir que todos os models sejam registrados no metadata.
"""

from app.models.base import Base
from app.models.user import UserModel
from app.models.ocorrencia import OcorrenciaModel
from app.models.feature_toggle import FeatureToggleModel

__all__ = [
    "Base",
    "UserModel",
    "OcorrenciaModel",
    "FeatureToggleModel",
]
