import enum

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class AircraftStatus(enum.Enum):

    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    INACTIVE = "INACTIVE"


class Aircraft(Base):

    __tablename__ = "aircraft"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    registration_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    manufacturer: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    seat_capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    status: Mapped[AircraftStatus] = mapped_column(
        Enum(AircraftStatus),
        nullable=False,
        default=AircraftStatus.ACTIVE
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    seats = relationship(
        "Seat",
        back_populates="aircraft",
        cascade="all, delete-orphan"
    )

    flights = relationship(
        "Flight",
        back_populates="aircraft"
    )