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

default_s3_endpoint = (
    "http://minio:9000"
    if is_docker
    else "https://s3.dsc.rodrigor.com"
)


class Settings:
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", default_db_url)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "0"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", default_secret_key)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Configurações do Object Storage (S3 / MinIO)
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", default_s3_endpoint)
    S3_PUBLIC_ENDPOINT: str = os.getenv("S3_PUBLIC_ENDPOINT", "https://s3.dsc.rodrigor.com")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "eq20")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "eq20")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "2qMwQDKJ9je55RVcK0YIkd2A")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")

    # Configurações do Resend
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "re_2pvQyR2q_AMjiTpUmCbV95RUG7828SjHp")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "verificacao@riou <onboarding@resend.dev>")


settings = Settings()


