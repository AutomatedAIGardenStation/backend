from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Chamber(Base):
    __tablename__ = "chambers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    z: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    plants: Mapped[list["Plant"]] = relationship(back_populates="chamber")
