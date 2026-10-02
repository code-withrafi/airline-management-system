"""
Phase 1 smoke test for PassengerBookingService.

Auto-discovers a bookable flight/seat, exercises the full
lifecycle, then cleans up after itself.
"""

from datetime import datetime

from app.config.database import SessionLocal
from app.models import (
    Booking,
    BookingStatus,
    Flight,
    FlightStatus,
    Seat,
    User,
    Passenger,
    UserRole,
)
from app.services.passenger_booking_service import (
    PassengerBookingService,
)
from app.services.exceptions import (
    AuthorizationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


def banner(text):
    print()
    print("=" * 60)
    print(text)
    print("=" * 60)


def pick_passenger_user(session):
    """Pick a passenger user that has a linked Passenger profile."""
    row = (
        session.query(User, Passenger)
        .join(Passenger, Passenger.user_id == User.id)
        .filter(User.role == UserRole.PASSENGER)
        .first()
    )
    if row is None:
        raise RuntimeError("No passenger with a linked profile found.")
    return row[0], row[1]


def pick_bookable_flight(session):
    """Pick the first future SCHEDULED flight."""
    return (
        session.query(Flight)
        .filter(
            Flight.status == FlightStatus.SCHEDULED,
            Flight.departure_time > datetime.utcnow(),
        )
        .first()
    )


def pick_free_seat(session, flight):
    """Pick a seat on the flight's aircraft with no booking row."""
    taken = {
        row[0]
        for row in session.query(Booking.seat_id)
        .filter(Booking.flight_id == flight.id)
        .all()
    }
    q = session.query(Seat).filter(Seat.aircraft_id == flight.aircraft_id)
    if taken:
        q = q.filter(~Seat.id.in_(taken))
    return q.order_by(Seat.row_number, Seat.seat_number).first()


def main():
    session = SessionLocal()
    booking_id = None

    try:
        service = PassengerBookingService(session)

        # ----------------------------------------------------------
        banner("0. Discover test fixtures")

        user, passenger = pick_passenger_user(session)
        print("OK  user_id:", user.id)
        print("OK  passenger_id:", passenger.id)
        print("OK  name:", passenger.first_name, passenger.last_name)

        flight = pick_bookable_flight(session)
        if flight is None:
            print("FAIL  no bookable (SCHEDULED + future) flight found.")
            print("      flip a flight to SCHEDULED first.")
            return
        print("OK  flight_id:", flight.id, "status:", flight.status.value)
        print("OK  departure:", flight.departure_time)

        seat = pick_free_seat(session, flight)
        if seat is None:
            print("FAIL  no free seat on aircraft", flight.aircraft_id)
            return
        print("OK  seat_id:", seat.id, "number:", seat.seat_number)

        # ----------------------------------------------------------
        banner("1. Create UNPAID booking")

        booking = service.create_booking(
            user_id=user.id,
            flight_id=flight.id,
            seat_id=seat.id,
        )
        booking_id = booking.id

        assert booking.status == BookingStatus.UNPAID
        print("OK  booking_id:", booking.id)
        print("OK  reference:", booking.booking_reference)
        print("OK  status:", booking.status.value)
        print("OK  fare:", booking.fare_amount)

        # ----------------------------------------------------------
        banner("2. Payment with BAD card (expect failure)")

        booking_after_bad, result_bad = service.pay_for_booking(
            user_id=user.id,
            booking_id=booking_id,
            card_number="abc",
            expiry="12/29",
            cvv="123",
            cardholder_name="Test Passenger",
        )
        assert result_bad.success is False
        assert booking_after_bad.status == BookingStatus.UNPAID
        print("OK  payment rejected:", result_bad.message)
        print("OK  status still:", booking_after_bad.status.value)

        # ----------------------------------------------------------
        banner("3. Payment with GOOD card (expect success)")

        booking_paid, result_good = service.pay_for_booking(
            user_id=user.id,
            booking_id=booking_id,
            card_number="4242 4242 4242 4242",
            expiry="12/29",
            cvv="123",
            cardholder_name="Test Passenger",
        )
        assert result_good.success is True
        assert booking_paid.status == BookingStatus.CONFIRMED
        print("OK  approved:", result_good.transaction_id)
        print("OK  status:", booking_paid.status.value)

        # ----------------------------------------------------------
        banner("4. Preview refund")

        preview = service.preview_refund(
            user_id=user.id,
            booking_id=booking_id,
        )
        print("OK  preview:", preview)

        # ----------------------------------------------------------
        banner("5. Request refund")

        refunded = service.request_refund(
            user_id=user.id,
            booking_id=booking_id,
        )
        assert refunded.status == BookingStatus.REFUND_REQUESTED
        print("OK  status:", refunded.status.value)

        # ----------------------------------------------------------
        banner("6. Ownership guard")

        other = (
            session.query(User, Passenger)
            .join(Passenger, Passenger.user_id == User.id)
            .filter(
                User.role == UserRole.PASSENGER,
                Passenger.id != passenger.id,
            )
            .first()
        )
        if other:
            try:
                service.preview_refund(
                    user_id=other[0].id,
                    booking_id=booking_id,
                )
                print("FAIL  ownership guard did NOT fire")
            except AuthorizationError as exc:
                print("OK  guard fired:", exc)
        else:
            print("SKIP  no second passenger")

        # ----------------------------------------------------------
        banner("ALL CHECKS PASSED")

    finally:
        banner("Cleanup")
        try:
            if booking_id:
                # Fresh session to avoid stale identity map issues
                fresh = SessionLocal()
                try:
                    b = fresh.get(Booking, booking_id)
                    if b is not None:
                        fresh.delete(b)
                        fresh.commit()
                        print("OK  deleted test booking:", booking_id)
                    else:
                        print("(no booking found to delete)")
                finally:
                    fresh.close()
        except Exception as exc:
            print("cleanup error:", exc)
        finally:
            session.close()


if __name__ == "__main__":
    main()
