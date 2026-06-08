"""Configurações centralizadas da aplicação."""

import os
from dotenv import load_dotenv

load_dotenv()


# Detecta se está rodando dentro de um contêiner Docker (produção)
is_docker = os.path.exists("/.dockerenv")

default_db_url = (
    "postgresql://eq20:0rl0ajunSM4HFlUCC2Ha@postgres:5432/eq20"
    if is_docker
    else "postgresql://postgres:postgres@localhost:5432/riou"
)

default_secret_key = (
    "0rl0ajunSM4HFlUCC2Ha_SECRET_KEY_PROD"
    if is_docker
    else "SUPER_SECRET_KEY_CHANGEME_IN_PRODUCTION_2026"
)


class Settings:
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", default_db_url)
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "0"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", default_secret_key)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day


settings = Settings()
