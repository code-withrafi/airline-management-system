from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Seat


class SeatRepository:

    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def create(
        self,
        *,
        aircraft_id: int,
        seat_number: str,
        seat_class,
        row_number: int,
        position,
    ) -> Seat:

        seat = Seat(
            aircraft_id=aircraft_id,
            seat_number=seat_number,
            seat_class=seat_class,
            row_number=row_number,
            position=position,
        )

        self.session.add(seat)
        self.session.flush()

        return seat

    def get_by_id(
        self,
        seat_id: int,
    ):
        from sqlalchemy import select
        from app.models import Seat
        statement = select(Seat).where(Seat.id == seat_id)
        return self.session.scalar(statement)

    def get_by_aircraft(
        self,
        aircraft_id: int,
    ) -> list[Seat]:
        """Return seats for an aircraft, ordered by row only."""

        statement = (
            select(Seat)
            .where(Seat.aircraft_id == aircraft_id)
            .order_by(Seat.row_number.asc())
            .options(selectinload(Seat.bookings))
        )

        return list(self.session.scalars(statement).all())

    def get_layout(
        self,
        aircraft_id: int,
    ) -> list[Seat]:
        """
        Return seats for an aircraft, ordered by row and number.

        Bookings are eager-loaded so that per-seat checks (like
        'is this seat booked?') do not cause an N+1 query problem.
        """

        statement = (
            select(Seat)
            .where(Seat.aircraft_id == aircraft_id)
            .order_by(Seat.row_number.asc(), Seat.seat_number.asc())
            .options(selectinload(Seat.bookings))
        )

        return list(self.session.scalars(statement).all())

    def count_by_aircraft(
        self,
        aircraft_id: int,
    ) -> int:

        statement = select(func.count(Seat.id)).where(
            Seat.aircraft_id == aircraft_id
        )

        return self.session.scalar(statement) or 0

    def delete_by_aircraft(
        self,
        aircraft_id: int,
    ) -> int:
        """Delete all seats for an aircraft. Returns the count removed."""

        seats = (
            self.session
            .query(Seat)
            .filter(Seat.aircraft_id == aircraft_id)
            .all()
        )

        for seat in seats:
            self.session.delete(seat)

        self.session.flush()
        return len(seats)