from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class ActuatorLogBase(BaseModel):
    chamber_id: Optional[int] = None
    actuator_type: str
    action: str
    parameters: Optional[Dict[str, Any]] = None

class ActuatorLogCreate(ActuatorLogBase):
    pass

class ActuatorLog(ActuatorLogBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
