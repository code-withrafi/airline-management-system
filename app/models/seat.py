import enum

from sqlalchemy import (
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class SeatClass(enum.Enum):

    ECONOMY = "ECONOMY"
    BUSINESS = "BUSINESS"


class SeatPosition(enum.Enum):

    WINDOW = "WINDOW"
    MIDDLE = "MIDDLE"
    AISLE = "AISLE"


class Seat(Base):

    __tablename__ = "seats"

    __table_args__ = (
        UniqueConstraint(
            "aircraft_id",
            "seat_number",
            name="unique_aircraft_seat"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    aircraft_id: Mapped[int] = mapped_column(
        ForeignKey("aircraft.id", ondelete="CASCADE"),
        nullable=False
    )

    seat_number: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    seat_class: Mapped[SeatClass] = mapped_column(
        Enum(SeatClass),
        nullable=False
    )

    row_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    position: Mapped[SeatPosition] = mapped_column(
        Enum(SeatPosition),
        nullable=False
    )

    aircraft = relationship(
        "Aircraft",
        back_populates="seats"
    )

    bookings = relationship(
        "Booking",
        back_populates="seat"
    )