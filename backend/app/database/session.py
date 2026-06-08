"""Configuração do engine e sessão do banco de dados."""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings

# Limita o pool de conexões para evitar esgotar o banco compartilhado.
# SQLite não suporta pool_size e max_overflow, por isso aplicamos apenas se não for SQLite.
engine_args = {}
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_args["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_args["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

engine = create_engine(settings.DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency que fornece uma sessão de banco de dados por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
