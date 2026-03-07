from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class ActuatorLog(Base):
    __tablename__ = "actuator_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    chamber_id: Mapped[int] = mapped_column(ForeignKey("chambers.id"), nullable=True, index=True)
    actuator_type: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String)
    parameters: Mapped[dict] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
