from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class PlantBase(BaseModel):
    chamber_id: int
    species: str

class PlantCreate(PlantBase):
    pass

class PlantUpdate(BaseModel):
    chamber_id: Optional[int] = None
    species: Optional[str] = None

class Plant(PlantBase):
    id: int
    planted_at: datetime
    model_config = ConfigDict(from_attributes=True)
