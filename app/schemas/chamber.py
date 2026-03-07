from pydantic import BaseModel, ConfigDict
from typing import Optional

class ChamberBase(BaseModel):
    name: str
    x: float
    y: float
    z: float

class ChamberCreate(ChamberBase):
    pass

class ChamberUpdate(BaseModel):
    name: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

class Chamber(ChamberBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
