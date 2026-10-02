from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.flight import (
    Flight,
    FlightStatus,
)


class FlightRepository:
    """Repository for Flight persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self) -> list[Flight]:
        statement = (
            select(Flight)
            .options(
                selectinload(Flight.route),
                selectinload(Flight.aircraft),
            )
            .order_by(Flight.departure_time.asc())
        )

        return list(self.session.scalars(statement).all())

    def get_by_id(self, flight_id: int) -> Flight | None:
        statement = (
            select(Flight)
            .where(Flight.id == flight_id)
            .options(
                selectinload(Flight.route),
                selectinload(Flight.aircraft),
            )
        )

        return self.session.scalar(statement)

    def get_by_flight_number(
        self,
        flight_number: str,
    ) -> Flight | None:
        """
        Returns the most recent flight matching the given
        flight number, ordered by departure_time descending.

        NOTE: kept for backwards compatibility. Prefer
        get_by_flight_number_and_time() for uniqueness checks.
        """
        normalized = flight_number.strip().upper()

        statement = (
            select(Flight)
            .where(
                func.upper(Flight.flight_number) == normalized
            )
            .options(
                selectinload(Flight.route),
                selectinload(Flight.aircraft),
            )
            .order_by(Flight.departure_time.desc())
            .limit(1)
        )

        return self.session.scalar(statement)

    def exists_by_flight_number_and_time(
        self,
        flight_number: str,
        departure_time,
        *,
        exclude_id: int | None = None,
    ) -> bool:
        """
        True if a flight with the given number AND the exact
        same departure_time already exists.

        A flight number may repeat across different days/times
        (e.g. daily SN101), but must not collide at the same
        scheduled departure datetime.

        Pass exclude_id when updating an existing flight so it
        does not conflict with itself.
        """
        normalized = flight_number.strip().upper()

        statement = select(Flight).where(
            func.upper(Flight.flight_number) == normalized,
            Flight.departure_time == departure_time,
        )

        if exclude_id is not None:
            statement = statement.where(Flight.id != exclude_id)

        statement = statement.limit(1)

        return self.session.scalar(statement) is not None

    def count(self) -> int:
        statement = select(func.count(Flight.id))

        return self.session.scalar(statement) or 0

    def search(
        self,
        *,
        keyword: str = "",
        status=None,
        route_id=None,
        aircraft_id=None,
        start_date=None,
        end_date=None,
    ) -> list[Flight]:
        statement = select(Flight)

        normalized = (keyword or "").strip()

        if normalized:
            pattern = f"%{normalized}%"

            statement = statement.where(
                or_(
                    Flight.flight_number.ilike(pattern),
                    Flight.boarding_gate.ilike(pattern),
                )
            )

        if status is not None:
            if isinstance(status, (list, tuple, set)):
                statement = statement.where(
                    Flight.status.in_(list(status))
                )
            else:
                statement = statement.where(
                    Flight.status == status
                )

        if route_id is not None:
            statement = statement.where(
                Flight.route_id == route_id
            )

        if aircraft_id is not None:
            statement = statement.where(
                Flight.aircraft_id == aircraft_id
            )

        if start_date is not None:
            statement = statement.where(
                Flight.departure_time >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                Flight.departure_time <= end_date
            )

        statement = (
            statement
            .options(
                selectinload(Flight.route),
                selectinload(Flight.aircraft),
            )
            .order_by(Flight.departure_time.asc())
        )

        return list(self.session.scalars(statement).all())

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        flight_number: str,
        route_id: int,
        aircraft_id: int,
        departure_time,
        arrival_time,
        base_fare,
        status=FlightStatus.SCHEDULED,
        boarding_gate=None,
    ) -> Flight:
        flight = Flight(
            flight_number=flight_number,
            route_id=route_id,
            aircraft_id=aircraft_id,
            departure_time=departure_time,
            arrival_time=arrival_time,
            base_fare=base_fare,
            status=status,
            boarding_gate=boarding_gate,
        )

        self.session.add(flight)
        self.session.flush()

        return flight

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        flight: Flight,
        *,
        flight_number=None,
        route_id=None,
        aircraft_id=None,
        departure_time=None,
        arrival_time=None,
        base_fare=None,
        status=None,
        boarding_gate=None,
    ) -> Flight:
        if flight_number is not None:
            flight.flight_number = flight_number

        if route_id is not None:
            flight.route_id = route_id

        if aircraft_id is not None:
            flight.aircraft_id = aircraft_id

        if departure_time is not None:
            flight.departure_time = departure_time

        if arrival_time is not None:
            flight.arrival_time = arrival_time

        if base_fare is not None:
            flight.base_fare = base_fare

        if status is not None:
            flight.status = status

        if boarding_gate is not None:
            flight.boarding_gate = boarding_gate

        self.session.flush()

        return flight

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, flight: Flight) -> None:
        self.session.delete(flight)
        self.session.flush()