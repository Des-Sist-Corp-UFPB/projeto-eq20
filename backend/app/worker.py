import json
import logging
import time
from typing import Optional
import redis

from app.config.settings import settings
from app.database.session import SessionLocal
from app.repositories.audit_log_repository import AuditLogRepository
from app.telemetry import init_telemetry, get_tracer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

init_telemetry()
tracer = get_tracer("riou_worker")
logger = logging.getLogger("riou_worker")

def process_audit_log(payload: dict) -> None:
    """Processa a persistência de um log de auditoria no banco de dados com span de telemetria."""
    with tracer.start_as_current_span("processar_log_auditoria") as span:
        action = payload.get("action")
        resource = payload.get("resource")
        user_email = payload.get("user_email")
        
        span.set_attribute("audit.action", action or "")
        span.set_attribute("audit.resource", resource or "")
        if user_email:
            span.set_attribute("audit.user_email", user_email)

        db = SessionLocal()
        try:
            repo = AuditLogRepository(db)
            repo.create(
                action=action,
                resource=resource,
                resource_id=payload.get("resource_id"),
                user_id=payload.get("user_id"),
                user_email=user_email,
                details=payload.get("details"),
            )
            logger.info(f"Log de auditoria gravado no BD: {action} - {resource}")
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Erro ao processar log de auditoria no worker: {e}")
        finally:
            db.close()


def main():
    logger.info("Iniciando o Worker RIOU...")
    
    # Loop de conexão com o Redis
    client = None
    while client is None:
        try:
            client = redis.Redis.from_url(settings.REDIS_URL)
            client.ping()
            logger.info("Conectado ao Redis com sucesso!")
        except Exception as e:
            logger.warning(f"Aguardando Redis iniciar ({e}). Tentando novamente em 3 segundos...")
            time.sleep(3)
            client = None

    queue_name = "riou_tasks"
    
    while True:
        try:
            # BLPOP bloqueia até receber um item na fila ou estourar o timeout (5s)
            result = client.blpop(queue_name, timeout=5)
            if result:
                _, data = result
                job = json.loads(data)
                task_type = job.get("type")
                payload = job.get("payload", {})
                
                logger.info(f"Tarefa recebida: {task_type}")
                if task_type == "audit_log":
                    process_audit_log(payload)
                else:
                    logger.warning(f"Tipo de tarefa desconhecido: {task_type}")
        except redis.RedisError as re:
            logger.error(f"Erro de conexão com o Redis no loop: {re}. Reconectando em 2 segundos...")
            time.sleep(2)
        except Exception as e:
            logger.error(f"Erro inesperado no worker: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
