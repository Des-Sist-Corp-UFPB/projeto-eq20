"""Configurações centralizadas da aplicação."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/urbanacare",
    )
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "SUPER_SECRET_KEY_CHANGEME_IN_PRODUCTION_2026",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day


settings = Settings()
