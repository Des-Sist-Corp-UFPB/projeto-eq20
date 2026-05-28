"""Schemas Pydantic de usuário e autenticação."""

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


class TokenResponse(BaseModel):
    """Schema de resposta do token JWT."""

    access_token: str
    token_type: str
    email: str
    role: str


class ForgotPasswordRequest(BaseModel):
    """Schema para solicitação de redefinição de senha."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema para redefinição de senha."""

    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=6)
