from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    chamber_id: Mapped[int] = mapped_column(ForeignKey("chambers.id"))
    species: Mapped[str] = mapped_column(String, index=True)
    planted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    chamber: Mapped["Chamber"] = relationship(back_populates="plants")
    sensor_readings: Mapped[list["SensorReading"]] = relationship(back_populates="plant")
    harvest_queue: Mapped[list["HarvestQueue"]] = relationship(back_populates="plant")
