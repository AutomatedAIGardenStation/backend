from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class HarvestQueue(Base):
    __tablename__ = "harvest_queue"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey("plants.id"), index=True)
    status: Mapped[str] = mapped_column(String, default="pending", index=True) # pending, completed, failed
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    plant: Mapped["Plant"] = relationship(back_populates="harvest_queue")
