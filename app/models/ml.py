from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=True, index=True)
    prediction_type: Mapped[str] = mapped_column(String, index=True)
    confidence: Mapped[float] = mapped_column(Float)
    result_data: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
