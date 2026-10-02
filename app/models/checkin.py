import enum

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class CheckInMethod(enum.Enum):

    ONLINE = "ONLINE"
    STAFF = "STAFF"


class CheckInStatus(enum.Enum):

    CHECKED_IN = "CHECKED_IN"
    CANCELLED = "CANCELLED"


class CheckIn(Base):

    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    checked_in_by: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id"),
        nullable=True
    )

    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    method: Mapped[CheckInMethod] = mapped_column(
        Enum(CheckInMethod),
        nullable=False
    )

    status: Mapped[CheckInStatus] = mapped_column(
        Enum(CheckInStatus),
        nullable=False,
        default=CheckInStatus.CHECKED_IN
    )

    booking = relationship(
        "Booking",
        back_populates="checkin"
    )

    staff = relationship(
        "Staff",
        back_populates="checkins"
    )

    baggage = relationship(
        "Baggage",
        back_populates="checkin",
        cascade="all, delete-orphan"
    )