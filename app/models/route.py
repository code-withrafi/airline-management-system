from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Route(Base):

    __tablename__ = "routes"

    __table_args__ = (
        CheckConstraint(
            "origin_airport_id != destination_airport_id",
            name="check_different_airports"
        ),
        CheckConstraint(
            "distance_km > 0",
            name="check_positive_distance"
        ),
        CheckConstraint(
            "estimated_duration_minutes > 0",
            name="check_positive_duration"
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    origin_airport_id: Mapped[int] = mapped_column(
        ForeignKey("airports.id"),
        nullable=False
    )

    destination_airport_id: Mapped[int] = mapped_column(
        ForeignKey("airports.id"),
        nullable=False
    )

    distance_km: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    estimated_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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

    origin_airport = relationship(
        "Airport",
        foreign_keys=[origin_airport_id],
        back_populates="origin_routes"
    )

    destination_airport = relationship(
        "Airport",
        foreign_keys=[destination_airport_id],
        back_populates="destination_routes"
    )

    flights = relationship(
        "Flight",
        back_populates="route"
    )