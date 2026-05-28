"""Repositório de acesso a dados de usuários."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import UserModel
from app.security.password import get_password_hash


class UserRepository:
    """Operações de banco de dados para a entidade User."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> Optional[UserModel]:
        """Busca um usuário pelo e-mail."""
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    def create(self, email: str, password: str, role: str = "user") -> UserModel:
        """Cria um novo usuário no banco."""
        user = UserModel(
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_reset_token(self, user: UserModel, token: str) -> None:
        """Define o token de reset de senha."""
        user.reset_token = token
        self.db.commit()

    def update_password(self, user: UserModel, new_password: str) -> None:
        """Atualiza a senha e limpa o reset token."""
        user.hashed_password = get_password_hash(new_password)
        user.reset_token = None
        self.db.commit()

    def list_all(self) -> list[UserModel]:
        """Lista todos os usuários ordenados por ID."""
        return self.db.query(UserModel).order_by(UserModel.id.asc()).all()
