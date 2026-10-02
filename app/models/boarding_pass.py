from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class BoardingPass(Base):

    __tablename__ = "boarding_passes"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    booking_id: Mapped[int] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    boarding_pass_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    boarding_group: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    boarding_gate: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    issued_by: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id"),
        nullable=True
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    pdf_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    booking = relationship(
        "Booking",
        back_populates="boarding_pass"
    )

    issued_by_staff = relationship(
        "Staff",
        back_populates="boarding_passes"
    )