"""Schemas de resposta comuns."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Schema padrão para respostas de mensagem simples."""

    message: str


class MessageWithDebugResponse(BaseModel):
    """Schema para respostas de mensagem com token de debug."""

    message: str
    debug_token: str | None = None
