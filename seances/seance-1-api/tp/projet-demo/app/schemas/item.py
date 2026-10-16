from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator


def reject_boolean_price(value):
    if isinstance(value, bool):
        raise ValueError("tarif_jour must be a positive finite number, not a boolean")
    return value


DailyRate = Annotated[
    float,
    Field(gt=0, allow_inf_nan=False),
    BeforeValidator(reject_boolean_price),
]


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titre: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    tarif_jour: DailyRate
    disponible: bool = True


class ItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    titre: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    tarif_jour: DailyRate | None = None
    disponible: bool | None = None

    @field_validator("titre", "tarif_jour", "disponible")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class ItemRead(BaseModel):
    id: int
    titre: str
    description: str | None
    tarif_jour: float
    disponible: bool
