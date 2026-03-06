from pydantic import BaseModel, ConfigDict
from typing import Optional

class SystemConfigBase(BaseModel):
    key: str
    value: str

class SystemConfigCreate(SystemConfigBase):
    pass

class SystemConfigUpdate(BaseModel):
    value: Optional[str] = None

class SystemConfig(SystemConfigBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
