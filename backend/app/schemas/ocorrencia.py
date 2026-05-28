"""Schemas Pydantic de ocorrência."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.utils.constants import CATEGORIES_AND_TYPES


class OcorrenciaBase(BaseModel):
    """Schema base de ocorrência com validação de categoria e tipo."""

    title: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    description: str
    lat: float
    lng: float
    photo: Optional[str] = Field(None, max_length=500)
    type: str = Field(..., max_length=30)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORIES_AND_TYPES:
            raise ValueError(f"Categoria inválida: {v}")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str, info: ValidationInfo) -> str:
        category = info.data.get("category")
        if not category:
            return v
        valid_types = CATEGORIES_AND_TYPES.get(category, [])
        if v not in valid_types:
            raise ValueError(f"Tipo de ocorrência '{v}' não pertence à categoria '{category}'")
        return v


class OcorrenciaCreate(OcorrenciaBase):
    """Schema para criação de ocorrência."""

    pass


class OcorrenciaStatusUpdate(BaseModel):
    """Schema para atualização de status de ocorrência."""

    status: str = Field(..., max_length=30)


class OcorrenciaResponse(OcorrenciaBase):
    """Schema de resposta de ocorrência."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    date: datetime
    user_id: Optional[int] = None
