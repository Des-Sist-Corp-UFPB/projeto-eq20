from fastapi import HTTPException, status
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

    def delete_user(self, user_id: int) -> None:
        """Exclui um usuário do sistema."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        if user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível excluir um administrador.",
            )
        self.user_repo.delete(user)

    def ban_user(self, user_id: int, duration_minutes: int) -> UserModel:
        """Bane temporariamente ou desbane um usuário."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        if user.role == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível banir um administrador.",
            )

        if duration_minutes <= 0:
            banned_until = None
        else:
            from datetime import datetime, UTC, timedelta
            banned_until = datetime.now(UTC) + timedelta(minutes=duration_minutes)

        return self.user_repo.update_ban(user, banned_until)
