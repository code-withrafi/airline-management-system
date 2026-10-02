import enum

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    CheckConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class FlightStatus(enum.Enum):

    SCHEDULED = "SCHEDULED"
    BOARDING = "BOARDING"
    DEPARTED = "DEPARTED"
    ARRIVED = "ARRIVED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class Flight(Base):

    __tablename__ = "flights"

    __table_args__ = (
        CheckConstraint(
            "departure_time < arrival_time",
            name="check_flight_times"
        ),
        CheckConstraint(
            "base_fare >= 0",
            name="check_positive_fare"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    flight_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )

    route_id: Mapped[int] = mapped_column(
        ForeignKey("routes.id"),
        nullable=False
    )

    aircraft_id: Mapped[int] = mapped_column(
        ForeignKey("aircraft.id"),
        nullable=False
    )

    departure_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )

    arrival_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    base_fare: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    status: Mapped[FlightStatus] = mapped_column(
        Enum(FlightStatus),
        nullable=False,
        default=FlightStatus.SCHEDULED,
        index=True
    )

    boarding_gate: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
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

    route = relationship(
        "Route",
        back_populates="flights"
    )

    aircraft = relationship(
        "Aircraft",
        back_populates="flights"
    )

    staff_assignments = relationship(
        "FlightStaff",
        back_populates="flight",
        cascade="all, delete-orphan"
    )

    bookings = relationship(
        "Booking",
        back_populates="flight"
    )