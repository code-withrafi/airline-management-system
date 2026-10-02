from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus


class BookingRepository:
    """
    Repository responsible for database operations
    related to bookings.
    """

    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def get_all(self) -> list[Booking]:

        from sqlalchemy.orm import selectinload

        statement = (
            select(Booking)
            .options(
                selectinload(Booking.flight),
                selectinload(Booking.seat),
                selectinload(Booking.passenger),
            )
            .order_by(
                Booking.booked_at.desc()
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_by_id(
        self,
        booking_id: int,
    ) -> Booking | None:

        statement = select(Booking).where(
            Booking.id == booking_id
        )

        return self.session.scalar(
            statement
        )

    def get_by_reference(
        self,
        booking_reference: str,
    ) -> Booking | None:

        normalized = (
            booking_reference
            .strip()
            .upper()
        )

        statement = select(Booking).where(
            func.upper(
                Booking.booking_reference
            )
            == normalized
        )

        return self.session.scalar(
            statement
        )

    def get_by_passenger(
        self,
        passenger_id: int,
    ) -> list[Booking]:

        from sqlalchemy.orm import selectinload

        statement = (
            select(Booking)
            .where(
                Booking.passenger_id == passenger_id
            )
            .options(
                selectinload(Booking.flight),
                selectinload(Booking.seat),
            )
            .order_by(
                Booking.booked_at.desc()
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_by_flight(
        self,
        flight_id: int,
    ) -> list[Booking]:

        statement = (
            select(Booking)
            .where(
                Booking.flight_id == flight_id
            )
            .order_by(
                Booking.id.asc()
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_by_flight_and_seat(
        self,
        flight_id: int,
        seat_id: int,
    ) -> Booking | None:

        statement = select(Booking).where(
            Booking.flight_id == flight_id,
            Booking.seat_id == seat_id,
        )

        return self.session.scalar(
            statement
        )

    def get_active_bookings(
        self,
        flight_id: int,
    ) -> list[Booking]:

        statement = (
            select(Booking)
            .where(
                Booking.flight_id == flight_id,
                Booking.status != BookingStatus.CANCELLED,
            )
            .order_by(
                Booking.id.asc()
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_expired_unpaid(
        self,
        cutoff: datetime,
    ) -> list[Booking]:
        """Return UNPAID bookings created at or before *cutoff*.

        Used by the payment-window sweeper: a booking whose
        booked_at is older than the cutoff has sat unpaid for
        too long and should be auto-cancelled.
        """

        statement = (
            select(Booking)
            .where(
                Booking.status == BookingStatus.UNPAID,
                Booking.booked_at <= cutoff,
            )
            .order_by(
                Booking.id.asc()
            )
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_available_seats_for_flight(
        self,
        flight_id: int,
    ) -> list:
        """
        Return seats on the flight's aircraft that have no active booking.
        """
        from sqlalchemy import select
        from app.models import Booking, BookingStatus, Flight, Seat

        flight = self.session.get(Flight, flight_id)

        if flight is None:
            return []

        taken_seat_ids = (
            select(Booking.seat_id)
            .where(
                Booking.flight_id == flight_id,
                Booking.status.not_in([
                    BookingStatus.CANCELLED,
                    BookingStatus.REFUNDED,
                ]),
            )
        )

        statement = (
            select(Seat)
            .where(
                Seat.aircraft_id == flight.aircraft_id,
                Seat.id.not_in(taken_seat_ids),
            )
            .order_by(
                Seat.row_number.asc(),
                Seat.seat_number.asc(),
            )
        )

        return list(self.session.scalars(statement).all())

    def create(
        self,
        *,
        booking_reference: str,
        passenger_id: int,
        flight_id: int,
        seat_id: int,
        fare_amount,
        status=BookingStatus.CONFIRMED,
    ) -> Booking:

        booking = Booking(
            booking_reference=booking_reference,
            passenger_id=passenger_id,
            flight_id=flight_id,
            seat_id=seat_id,
            fare_amount=fare_amount,
            status=status,
        )

        self.session.add(
            booking
        )

        self.session.flush()

        return booking

    def update_status(
        self,
        booking: Booking,
        status: BookingStatus,
    ) -> Booking:

        booking.status = status

        self.session.flush()

        return booking

    def set_refund_amount(
        self,
        booking: Booking,
        amount,
    ) -> Booking:
        """Store the refund amount on a booking."""

        booking.refund_amount = amount

        self.session.flush()

        return booking

    def delete(
        self,
        booking: Booking,
    ) -> None:

        self.session.delete(
            booking
        )

        self.session.flush()

    def count(self) -> int:

        statement = select(
            func.count(
                Booking.id
            )
        )

        return (
            self.session.scalar(statement)
            or 0
        )