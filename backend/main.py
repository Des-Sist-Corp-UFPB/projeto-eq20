"""Proxy para o módulo app modularizado, mantendo compatibilidade com testes e servidores."""

from app.database.session import get_db
from app.main import app
from app.models.base import Base
from app.models.feature_toggle import FeatureToggleModel
from app.models.user import UserModel
from app.security.password import get_password_hash

__all__ = [
    "app",
    "get_db",
    "Base",
    "FeatureToggleModel",
    "UserModel",
    "get_password_hash",
]
