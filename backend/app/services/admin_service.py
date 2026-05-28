"""Serviço de lógica de negócio do painel administrativo."""

from sqlalchemy.orm import Session

from app.models.feature_toggle import FeatureToggleModel
from app.models.user import UserModel
from app.repositories.feature_toggle_repository import FeatureToggleRepository
from app.repositories.ocorrencia_repository import OcorrenciaRepository
from app.repositories.user_repository import UserRepository


class AdminService:
    """Lógica de negócio para funcionalidades administrativas."""

    def __init__(self, db: Session) -> None:
        self.toggle_repo = FeatureToggleRepository(db)
        self.ocorrencia_repo = OcorrenciaRepository(db)
        self.user_repo = UserRepository(db)

    def get_toggles(self) -> list[FeatureToggleModel]:
        """Retorna todos os feature toggles."""
        return self.toggle_repo.get_all()

    def update_toggle(self, key: str, value: bool) -> FeatureToggleModel:
        """Cria ou atualiza um feature toggle."""
        return self.toggle_repo.upsert(key, value)

    def batch_resolve(self) -> dict:
        """Resolve todas as ocorrências pendentes."""
        affected = self.ocorrencia_repo.batch_resolve()
        return {"message": f"Ação executada com sucesso. {affected} ocorrências foram resolvidas."}

    def list_users(self) -> list[UserModel]:
        """Lista todos os usuários."""
        return self.user_repo.list_all()
