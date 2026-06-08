from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """Schema para registro de novo usuário."""

    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema para login de usuário."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema de resposta com dados públicos do usuário."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    banned_until: Optional[datetime] = None


class TokenResponse(BaseModel):
    """Schema de resposta do token JWT."""

    access_token: str
    token_type: str
    id: int
    email: str
    role: str


class BanUserRequest(BaseModel):
    """Schema para requisição de banimento de usuário."""

    duration_minutes: int


class ForgotPasswordRequest(BaseModel):
    """Schema para solicitação de redefinição de senha."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema para redefinição de senha."""

    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=6)
