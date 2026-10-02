from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    Airport,
    Booking,
    BookingStatus,
    Flight,
    Passenger,
    Route,
)
from app.services.exceptions import DatabaseOperationError


# Statuses that count as "revenue" — paid and still valid
REVENUE_STATUSES = (
    BookingStatus.CONFIRMED,
    BookingStatus.CHECKED_IN,
    BookingStatus.COMPLETED,
)


class ReportsService:
    """
    Read-only aggregation service for the Reports page.
    """

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        """
        Return a dict with high-level metrics.
        """

        try:
            # Total revenue
            revenue_stmt = select(
                func.coalesce(
                    func.sum(Booking.fare_amount),
                    0,
                )
            ).where(
                Booking.status.in_(REVENUE_STATUSES)
            )

            total_revenue = self.session.scalar(
                revenue_stmt
            ) or Decimal("0.00")

            # Total bookings
            total_bookings = (
                self.session.scalar(
                    select(func.count(Booking.id))
                )
                or 0
            )

            # Cancelled bookings
            cancelled = (
                self.session.scalar(
                    select(func.count(Booking.id)).where(
                        Booking.status
                        == BookingStatus.CANCELLED
                    )
                )
                or 0
            )

            # Refunded amount
            refunded_amount = (
                self.session.scalar(
                    select(
                        func.coalesce(
                            func.sum(Booking.refund_amount),
                            0,
                        )
                    ).where(
                        Booking.status
                        == BookingStatus.REFUNDED
                    )
                )
                or Decimal("0.00")
            )

            # Passengers / flights totals
            total_passengers = (
                self.session.scalar(
                    select(func.count(Passenger.id))
                )
                or 0
            )

            total_flights = (
                self.session.scalar(
                    select(func.count(Flight.id))
                )
                or 0
            )

            return {
                "total_revenue": Decimal(str(total_revenue)),
                "total_bookings": int(total_bookings),
                "cancelled_bookings": int(cancelled),
                "refunded_amount": Decimal(str(refunded_amount)),
                "total_passengers": int(total_passengers),
                "total_flights": int(total_flights),
            }

        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to compute report summary."
            ) from exc

    # ------------------------------------------------------------------

    def get_top_routes(
        self,
        limit: int = 10,
    ) -> list[dict]:
        """
        Return the routes with the most bookings.

        Each entry:
            {
                "route": "DAC -> CGP",
                "bookings": 12,
                "revenue": Decimal("4800.00"),
            }
        """

        try:
            origin = (
                Airport.__table__.alias("origin")
            )

            destination = (
                Airport.__table__.alias("destination")
            )

            stmt = (
                select(
                    origin.c.iata_code,
                    destination.c.iata_code,
                    func.count(Booking.id).label("bookings"),
                    func.coalesce(
                        func.sum(Booking.fare_amount),
                        0,
                    ).label("revenue"),
                )
                .select_from(Route)
                .join(
                    origin,
                    Route.origin_airport_id == origin.c.id,
                )
                .join(
                    destination,
                    Route.destination_airport_id == destination.c.id,
                )
                .outerjoin(
                    Flight,
                    Flight.route_id == Route.id,
                )
                .outerjoin(
                    Booking,
                    Booking.flight_id == Flight.id,
                )
                .where(
                    Booking.status.in_(REVENUE_STATUSES)
                )
                .group_by(
                    origin.c.iata_code,
                    destination.c.iata_code,
                )
                .order_by(
                    func.count(Booking.id).desc()
                )
                .limit(limit)
            )

            rows = self.session.execute(stmt).all()

            return [
                {
                    "route": f"{row[0]} \u2192 {row[1]}",
                    "bookings": int(row[2]),
                    "revenue": Decimal(str(row[3])),
                }
                for row in rows
            ]

        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to compute top routes."
            ) from exc
