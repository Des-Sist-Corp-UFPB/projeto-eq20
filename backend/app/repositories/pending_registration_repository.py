from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy.orm import Session

from app.models.pending_registration import PendingRegistrationModel


class PendingRegistrationRepository:
    """Operações de banco de dados para a entidade PendingRegistration."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> Optional[PendingRegistrationModel]:
        """Busca um registro pendente pelo e-mail."""
        return (
            self.db.query(PendingRegistrationModel)
            .filter(PendingRegistrationModel.email == email)
            .first()
        )

    def create_or_update(
        self, email: str, password_hash: str, code: str
    ) -> PendingRegistrationModel:
        """Cria ou atualiza um registro de cadastro pendente."""
        existing = self.get_by_email(email)
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        if existing:
            existing.hashed_password = password_hash
            existing.code = code
            existing.expires_at = expires_at
            self.db.commit()
            self.db.refresh(existing)
            return existing

        pending = PendingRegistrationModel(
            email=email,
            hashed_password=password_hash,
            code=code,
            expires_at=expires_at,
        )
        self.db.add(pending)
        self.db.commit()
        self.db.refresh(pending)
        return pending

    def delete(self, pending: PendingRegistrationModel) -> None:
        """Exclui um registro pendente do banco."""
        self.db.delete(pending)
        self.db.commit()
