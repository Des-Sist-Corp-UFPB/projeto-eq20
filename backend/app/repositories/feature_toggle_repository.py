"""Repositório de acesso a dados de feature toggles."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.feature_toggle import FeatureToggleModel


class FeatureToggleRepository:
    """Operações de banco de dados para a entidade FeatureToggle."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_value(self, key: str, default: bool = True) -> bool:
        """Retorna o valor de um toggle, ou o default se não existir."""
        from app.services.cache_service import CacheService
        cache_key = f"toggle:{key}"
        cached_val = CacheService.get(cache_key)
        if cached_val is not None:
            return cached_val

        toggle = self.db.query(FeatureToggleModel).filter(
            FeatureToggleModel.key == key
        ).first()
        val = default if not toggle else toggle.value
        CacheService.set(cache_key, val, ttl=60)
        return val

    def get_all(self) -> list[FeatureToggleModel]:
        """Lista todos os feature toggles."""
        return self.db.query(FeatureToggleModel).all()

    def upsert(self, key: str, value: bool) -> FeatureToggleModel:
        """Cria ou atualiza um feature toggle."""
        toggle = self.db.query(FeatureToggleModel).filter(
            FeatureToggleModel.key == key
        ).first()
        if not toggle:
            toggle = FeatureToggleModel(key=key, value=value)
            self.db.add(toggle)
        else:
            toggle.value = value

        self.db.commit()
        self.db.refresh(toggle)

        from app.services.cache_service import CacheService
        CacheService.delete(f"toggle:{key}")
        
        # Também limpamos o cache de ocorrências, pois os toggles podem mudar as regras de exibição/criação
        CacheService.clear_pattern("occurrences:*")

        return toggle
