from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Aircraft,
    Airport,
    Booking,
    Flight,
    FlightStatus,
    Passenger,
    Route,
)


class DashboardRepository:
    """
    Repository responsible for retrieving administrator dashboard data
    from the PostgreSQL database.
    """

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Basic entity counts
    # ------------------------------------------------------------------

    def get_total_airports(self) -> int:
        statement = select(func.count(Airport.id))
        return self.session.scalar(statement) or 0

    def get_total_aircraft(self) -> int:
        statement = select(func.count(Aircraft.id))
        return self.session.scalar(statement) or 0

    def get_total_routes(self) -> int:
        statement = select(func.count(Route.id))
        return self.session.scalar(statement) or 0

    def get_total_flights(self) -> int:
        statement = select(func.count(Flight.id))
        return self.session.scalar(statement) or 0

    def get_total_bookings(self) -> int:
        statement = select(func.count(Booking.id))
        return self.session.scalar(statement) or 0

    def get_total_passengers(self) -> int:
        statement = select(func.count(Passenger.id))
        return self.session.scalar(statement) or 0

    # ------------------------------------------------------------------
    # Flight statistics
    # ------------------------------------------------------------------

    def get_scheduled_flights(self) -> int:
        statement = select(func.count(Flight.id)).where(
            Flight.status == FlightStatus.SCHEDULED
        )

        return self.session.scalar(statement) or 0

    def get_cancelled_flights(self) -> int:
        statement = select(func.count(Flight.id)).where(
            Flight.status == FlightStatus.CANCELLED
        )

        return self.session.scalar(statement) or 0

    # ------------------------------------------------------------------
    # Combined dashboard statistics
    # ------------------------------------------------------------------

    def get_dashboard_statistics(self) -> dict[str, int]:
        """
        Return all dashboard statistics.
        """

        return {
            "total_airports": self.get_total_airports(),
            "total_aircraft": self.get_total_aircraft(),
            "total_routes": self.get_total_routes(),
            "total_flights": self.get_total_flights(),
            "scheduled_flights": self.get_scheduled_flights(),
            "cancelled_flights": self.get_cancelled_flights(),
            "total_bookings": self.get_total_bookings(),
            "total_passengers": self.get_total_passengers(),
        }

    # ------------------------------------------------------------------
    # Recent / upcoming flights
    # ------------------------------------------------------------------

    def get_recent_flights(self, limit: int = 10) -> list[Flight]:
        """
        Return recent/upcoming flights with their related route,
        airports, and aircraft loaded.

        Eager loading is used so the GUI can access the related
        objects without generating additional database queries.
        """

        if limit <= 0:
            return []

        statement = (
            select(Flight)
            .options(
                joinedload(Flight.route).joinedload(
                    Route.origin_airport
                ),
                joinedload(Flight.route).joinedload(
                    Route.destination_airport
                ),
                joinedload(Flight.aircraft),
            )
            .order_by(Flight.departure_time.asc())
            .limit(limit)
        )

        return list(
            self.session.scalars(statement).unique().all()
        )