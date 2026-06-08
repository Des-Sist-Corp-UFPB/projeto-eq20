"""Serviço de autenticação e gestão de usuários."""

from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRegister, TokenResponse
from app.security.jwt import create_access_token
from app.security.password import verify_password


class AuthService:
    """Lógica de negócio de autenticação."""

    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)

    def register(self, user_data: UserRegister) -> UserModel:
        """Registra um novo usuário."""
        existing = self.user_repo.get_by_email(user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este e-mail já está cadastrado.",
            )

        return self.user_repo.create(
            email=user_data.email,
            password=user_data.password,
            role="user",
        )

    def login(self, email: str, password: str) -> dict:
        """Autentica um usuário e retorna o token JWT."""
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.banned_until:
            from datetime import datetime, UTC, timezone
            banned_until = user.banned_until
            if banned_until.tzinfo is None:
                banned_until = banned_until.replace(tzinfo=timezone.utc)
            if banned_until > datetime.now(UTC):
                ban_str = banned_until.strftime("%d/%m/%Y %H:%M:%S")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Sua conta está temporariamente banida até {ban_str}.",
                )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }

    def forgot_password(self, email: str) -> dict:
        """Gera um token de redefinição de senha (mock)."""
        user = self.user_repo.get_by_email(email)
        if not user:
            # Avoid user enumeration, pretend it was sent anyway
            return {"message": "Caso o e-mail exista, um código de redefinição foi gerado."}

        # Generate mock reset token
        reset_token = f"reset-{int(datetime.now(UTC).timestamp())}"
        self.user_repo.set_reset_token(user, reset_token)

        # PRINT IN CONTAINER LOG FOR USER ACCESS
        print("\n" + "=" * 80)
        print(f"MOCK PASSWORD RESET LINK FOR: {user.email}")
        print(f"Use the token: {reset_token}")
        print(f"Redefinition parameters: ?email={user.email}&token={reset_token}")
        print("=" * 80 + "\n")

        return {
            "message": "Caso o e-mail exista, um código de redefinição foi gerado. Verifique os logs do Docker para resgatar seu link.",
            "debug_token": reset_token,  # Send directly for UI developer ease
        }

    def reset_password(self, email: str, token: str, new_password: str) -> dict:
        """Redefine a senha do usuário usando o token de reset."""
        user = self.user_repo.get_by_email(email)
        if not user or user.reset_token != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de redefinição inválido ou e-mail inválido.",
            )

        self.user_repo.update_password(user, new_password)
        return {"message": "Senha redefinida com sucesso."}
