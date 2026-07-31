"""Módulo exclusivo para centralização da configuração do OpenTelemetry.

Concentra todas as rotinas de instrumentação automática (FastAPI, SQLAlchemy, Psycopg2,
Requests, HTTPX e Logging) e configuração da telemetria e correlação de logs.
"""

import logging
import os
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    HAS_HTTPX_INSTRUMENTOR = True
except ImportError:
    HAS_HTTPX_INSTRUMENTOR = False

logger = logging.getLogger("app.telemetry")

_initialized = False


def setup_log_correlation() -> None:
    """Configura a instrumentação de logs garantindo a injeção de trace_id e span_id."""
    try:
        log_format = "%(asctime)s %(levelname)s [%(name)s] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s"
        LoggingInstrumentor().instrument(set_logging_format=True, logging_format=log_format)
        logger.info("OpenTelemetry LoggingInstrumentor ativado com sucesso.")
    except Exception as e:
        logger.warning(f"Aviso ao inicializar LoggingInstrumentor: {e}")


def instrument_db_engine(engine) -> None:
    """Instrumenta uma instância do engine SQLAlchemy para rastreamento de queries no banco PostgreSQL."""
    if engine is None:
        return
    try:
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy engine instrumentado com sucesso.")
    except Exception as e:
        logger.warning(f"Aviso ao instrumentar SQLAlchemy engine: {e}")


def init_telemetry(app=None, engine=None) -> None:
    """Inicializa toda a configuração e instrumentação do OpenTelemetry no sistema.

    Evita execução duplicada e garante a instrumentação de FastAPI, SQLAlchemy,
    PostgreSQL (psycopg2), HTTP clients (requests/httpx) e Logging.
    """
    global _initialized
    if _initialized:
        if app is not None:
            try:
                FastAPIInstrumentor().instrument_app(app)
            except Exception:
                pass
        if engine is not None:
            instrument_db_engine(engine)
        return

    # 1. Configurar correlação de logs
    setup_log_correlation()

    # 2. Instrumentar Psycopg2 / PostgreSQL
    try:
        Psycopg2Instrumentor().instrument()
        logger.info("Psycopg2 instrumentado com sucesso.")
    except Exception as e:
        logger.warning(f"Aviso ao instrumentar Psycopg2: {e}")

    # 3. Instrumentar Requests HTTP client
    try:
        RequestsInstrumentor().instrument()
        logger.info("Requests instrumentado com sucesso.")
    except Exception as e:
        logger.warning(f"Aviso ao instrumentar Requests: {e}")

    # 4. Instrumentar HTTPX Client caso disponível
    if HAS_HTTPX_INSTRUMENTOR:
        try:
            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPXClient instrumentado com sucesso.")
        except Exception as e:
            logger.warning(f"Aviso ao instrumentar HTTPXClient: {e}")

    # 5. Instrumentar FastAPI app se fornecida
    if app is not None:
        try:
            FastAPIInstrumentor().instrument_app(app)
            logger.info("FastAPI app instrumentado com sucesso.")
        except Exception as e:
            logger.warning(f"Aviso ao instrumentar FastAPI: {e}")

    # 6. Instrumentar SQLAlchemy se engine fornecida
    if engine is not None:
        instrument_db_engine(engine)

    _initialized = True


def get_tracer(name: str = "riou_backend") -> trace.Tracer:
    """Retorna uma instância de Tracer configurada para instrumentação manual."""
    return trace.get_tracer(name)
