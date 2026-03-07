from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

class MLPredictionBase(BaseModel):
    plant_id: Optional[int] = None
    prediction_type: str
    confidence: float
    result_data: Dict[str, Any]

class MLPredictionCreate(MLPredictionBase):
    pass

class MLPrediction(MLPredictionBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
