import enum

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class BaggageStatus(enum.Enum):

    CHECKED = "CHECKED"
    LOADED = "LOADED"
    DELIVERED = "DELIVERED"


class Baggage(Base):

    __tablename__ = "baggage"

    __table_args__ = (
        CheckConstraint(
            "weight_kg > 0",
            name="check_positive_baggage_weight"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    checkin_id: Mapped[int] = mapped_column(
        ForeignKey("checkins.id", ondelete="CASCADE"),
        nullable=False
    )

    bag_tag: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    weight_kg: Mapped[float] = mapped_column(
        Numeric(6, 2),
        nullable=False
    )

    status: Mapped[BaggageStatus] = mapped_column(
        Enum(BaggageStatus),
        nullable=False,
        default=BaggageStatus.CHECKED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    checkin = relationship(
        "CheckIn",
        back_populates="baggage"
    )