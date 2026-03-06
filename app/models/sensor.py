from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Float, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class SensorReading(Base):
    """Time-series table for sensor logs."""
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), nullable=True, index=True)
    sensor_type: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    plant: Mapped["Plant"] = relationship(back_populates="sensor_readings")
