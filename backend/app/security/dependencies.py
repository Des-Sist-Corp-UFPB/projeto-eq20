"""Dependencies de autenticação e autorização para injeção no FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import jwt as pyjwt

from app.config.settings import settings
from app.database.session import get_db
from app.models.user import UserModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    """Dependency que retorna o usuário autenticado a partir do token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível autenticar o token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except pyjwt.PyJWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user is None:
        raise credentials_exception

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

    return user


def get_current_admin(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Dependency que verifica se o usuário autenticado é administrador."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita a administradores",
        )
    return current_user


from typing import Optional
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    """Dependency opcional que retorna o usuário autenticado a partir do token JWT se fornecido."""
    if not token:
        return None
    try:
        payload = pyjwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except pyjwt.PyJWTError:
        return None

    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user is None:
        return None

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

    return user

