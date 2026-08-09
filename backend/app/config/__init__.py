"""Configurações centralizadas da aplicação."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/riou",
    )
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "SUPER_SECRET_KEY_CHANGEME_IN_PRODUCTION_2026",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Configurações do Object Storage (S3 / MinIO)
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "https://s3.dsc.rodrigor.com")
    S3_PUBLIC_ENDPOINT: str = os.getenv("S3_PUBLIC_ENDPOINT", "https://s3.dsc.rodrigor.com")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "eq20")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "eq20")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "2qMwQDKJ9je55RVcK0YIkd2A")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")


settings = Settings()

