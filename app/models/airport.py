from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base


class Airport(Base):

    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    iata_code: Mapped[str] = mapped_column(
        String(3),
        unique=True,
        nullable=False,
        index=True
    )

    icao_code: Mapped[str] = mapped_column(
        String(4),
        unique=True,
        nullable=False,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    timezone: Mapped[str] = mapped_column(
        String(100),
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

    origin_routes = relationship(
        "Route",
        foreign_keys="Route.origin_airport_id",
        back_populates="origin_airport"
    )

    destination_routes = relationship(
        "Route",
        foreign_keys="Route.destination_airport_id",
        back_populates="destination_airport"
    )