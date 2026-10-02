import enum

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class BookingStatus(enum.Enum):

    UNPAID = "UNPAID"
    CONFIRMED = "CONFIRMED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REFUND_REQUESTED = "REFUND_REQUESTED"
    REFUNDED = "REFUNDED"


class Booking(Base):

    __tablename__ = "bookings"

    __table_args__ = (
        Index(
            "unique_active_flight_seat",
            "flight_id",
            "seat_id",
            unique=True,
            postgresql_where=text(
                "status NOT IN ('CANCELLED', 'REFUNDED')"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    booking_reference: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )

    passenger_id: Mapped[int] = mapped_column(
        ForeignKey("passengers.id"),
        nullable=False,
        index=True
    )

    flight_id: Mapped[int] = mapped_column(
        ForeignKey("flights.id"),
        nullable=False,
        index=True
    )

    seat_id: Mapped[int] = mapped_column(
        ForeignKey("seats.id"),
        nullable=False
    )

    fare_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    refund_amount: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus),
        nullable=False,
        default=BookingStatus.UNPAID
    )

    booked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    passenger = relationship(
        "Passenger",
        back_populates="bookings"
    )

    flight = relationship(
        "Flight",
        back_populates="bookings"
    )

    seat = relationship(
        "Seat",
        back_populates="bookings"
    )

    checkin = relationship(
        "CheckIn",
        back_populates="booking",
        uselist=False
    )

    boarding_pass = relationship(
        "BoardingPass",
        back_populates="booking",
        uselist=False
    )