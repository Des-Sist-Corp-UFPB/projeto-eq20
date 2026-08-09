"""Schemas Pydantic de feature toggle."""

from pydantic import BaseModel, ConfigDict


class ToggleResponse(BaseModel):
    """Schema de resposta de feature toggle."""

    model_config = ConfigDict(from_attributes=True)

    key: str
    value: bool
