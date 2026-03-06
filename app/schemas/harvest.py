from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class HarvestQueueBase(BaseModel):
    plant_id: int
    status: str = "pending"

class HarvestQueueCreate(HarvestQueueBase):
    pass

class HarvestQueueUpdate(BaseModel):
    status: Optional[str] = None

class HarvestQueue(HarvestQueueBase):
    id: int
    scheduled_time: datetime
    model_config = ConfigDict(from_attributes=True)
