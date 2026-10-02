import enum

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class AssignmentRole(enum.Enum):

    CHECK_IN = "CHECK_IN"
    BOARDING = "BOARDING"
    GROUND = "GROUND"
    SUPERVISOR = "SUPERVISOR"


class FlightStaff(Base):

    __tablename__ = "flight_staff"

    __table_args__ = (
        UniqueConstraint(
            "flight_id",
            "staff_id",
            name="unique_flight_staff"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    flight_id: Mapped[int] = mapped_column(
        ForeignKey("flights.id", ondelete="CASCADE"),
        nullable=False
    )

    staff_id: Mapped[int] = mapped_column(
        ForeignKey("staff.id", ondelete="CASCADE"),
        nullable=False
    )

    assigned_role: Mapped[AssignmentRole] = mapped_column(
        Enum(AssignmentRole),
        nullable=False
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    flight = relationship(
        "Flight",
        back_populates="staff_assignments"
    )

    staff = relationship(
        "Staff",
        back_populates="flight_assignments"
    )