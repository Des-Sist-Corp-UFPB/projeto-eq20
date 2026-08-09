import json
import logging
from typing import Dict, Any, Optional
import redis

from app.config.settings import settings

logger = logging.getLogger("riou_queue")

class QueueService:
    """Serviço de mensageria usando Redis para processamento em background."""
    
    _client: Optional[redis.Redis] = None
    _disabled: bool = False
    QUEUE_NAME = "riou_tasks"

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        if cls._disabled:
            return None
        if cls._client is None:
            try:
                cls._client = redis.Redis.from_url(
                    settings.REDIS_URL,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0
                )
                cls._client.ping()
            except Exception as e:
                logger.warning(f"Redis para fila indisponível: {e}. Executando tarefas de forma síncrona.")
                cls._client = None
                cls._disabled = True
        return cls._client

    @classmethod
    def enqueue(cls, task_type: str, payload: Dict[str, Any]) -> bool:
        """Adiciona uma tarefa à fila. Retorna True se enfileirada, False se falhou."""
        client = cls.get_client()
        if not client:
            return False
        try:
            job = {
                "type": task_type,
                "payload": payload
            }
            client.rpush(cls.QUEUE_NAME, json.dumps(job))
            return True
        except Exception as e:
            logger.error(f"Erro ao enfileirar tarefa ({task_type}): {e}")
            return False
