from pydantic import BaseModel, Field, ConfigDict


class ItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    titre: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    tarif_jour: float = Field(gt=0)
    disponible: bool = True


class ItemRead(BaseModel):
    id: int
    titre: str
    description: str | None
    tarif_jour: float
    disponible: bool