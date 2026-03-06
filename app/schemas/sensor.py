from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class SensorReadingBase(BaseModel):
    plant_id: Optional[int] = None
    sensor_type: str
    value: float

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReading(SensorReadingBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
