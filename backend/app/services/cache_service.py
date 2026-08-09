import json
import logging
from typing import Any, Optional
import redis

from app.config.settings import settings

logger = logging.getLogger("riou_cache")

class CacheService:
    """Serviço de cache baseado em Redis com fallback gracioso se estiver indisponível."""
    
    _client: Optional[redis.Redis] = None
    _disabled: bool = False

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        """Obtém ou inicializa o cliente Redis."""
        if cls._disabled:
            return None
        if cls._client is None:
            try:
                cls._client = redis.Redis.from_url(
                    settings.REDIS_URL, 
                    decode_responses=True,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0
                )
                # Testa a conexão
                cls._client.ping()
            except Exception as e:
                logger.warning(f"Redis indisponível: {e}. Fallback sem cache ativado.")
                cls._client = None
                cls._disabled = True
        return cls._client

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Recupera um valor do cache, deserializando de JSON."""
        client = cls.get_client()
        if not client:
            return None
        try:
            val = client.get(key)
            if val is not None:
                return json.loads(val)
        except Exception as e:
            logger.error(f"Erro ao ler do cache (chave: {key}): {e}")
        return None

    @classmethod
    def set(cls, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Salva um valor no cache, serializando para JSON."""
        client = cls.get_client()
        if not client:
            return False
        try:
            serialized = json.dumps(value)
            if ttl:
                client.setex(key, ttl, serialized)
            else:
                client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar no cache (chave: {key}): {e}")
            return False

    @classmethod
    def delete(cls, key: str) -> bool:
        """Exclui uma chave específica do cache."""
        client = cls.get_client()
        if not client:
            return False
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar chave do cache ({key}): {e}")
            return False

    @classmethod
    def clear_pattern(cls, pattern: str) -> bool:
        """Remove todas as chaves que correspondem ao padrão."""
        client = cls.get_client()
        if not client:
            return False
        try:
            # Busca as chaves de forma eficiente usando scan_iter
            keys = list(client.scan_iter(match=pattern, count=100))
            if keys:
                client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar padrão no cache ({pattern}): {e}")
            return False
