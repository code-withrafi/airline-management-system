from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.config.database import SessionLocal
from app.models import (
    Aircraft,
    AircraftStatus,
    Booking,
    BookingStatus,
    CheckIn,
    CheckInStatus,
    Flight,
    FlightStatus,
    Passenger,
    Route,
    Seat,
    User,
    UserRole,
)
from app.services.application import application_context
from app.services.checkin_service import CheckInService
from app.services.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
)


@pytest.fixture
def database_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def booking_factory(database_session):
    """
    Returns a function that creates a CONFIRMED booking on a
    future flight and cleans it up at the end of the test.
    """
    import uuid
    created_ids = []

    def _create(
        status=BookingStatus.CONFIRMED,
        departure_offset_days=10,
    ):
        tag = uuid.uuid4().hex[:8].upper()

        # Ensure an aircraft with seats exists
        aircraft = (
            database_session.query(Aircraft)
            .join(Seat, Seat.aircraft_id == Aircraft.id)
            .filter(Aircraft.status == AircraftStatus.ACTIVE)
            .first()
        )
        if aircraft is None:
            pytest.skip("No ACTIVE aircraft with seats in DB.")

        # Need an airport to build a route
        from app.models import Airport
        airports = (
            database_session.query(Airport)
            .order_by(Airport.id.asc())
            .limit(2)
            .all()
        )
        if len(airports) < 2:
            pytest.skip("Need at least 2 airports.")

        # Route
        route = (
            database_session.query(Route)
            .filter(
                Route.origin_airport_id == airports[0].id,
                Route.destination_airport_id == airports[1].id,
            )
            .first()
        )
        if route is None:
            route = Route(
                origin_airport_id=airports[0].id,
                destination_airport_id=airports[1].id,
                distance_km=100,
                estimated_duration_minutes=60,
                is_active=True,
            )
            database_session.add(route)
            database_session.flush()

        # Flight (future)
        departure = datetime.utcnow() + timedelta(days=departure_offset_days)
        flight = Flight(
            flight_number=f"TN{tag}",
            route_id=route.id,
            aircraft_id=aircraft.id,
            departure_time=departure,
            arrival_time=departure + timedelta(hours=1),
            base_fare=Decimal("500.00"),
            status=FlightStatus.SCHEDULED,
        )
        database_session.add(flight)
        database_session.flush()

        # Passenger + user
        user = User(
            email=f"p-{tag}@test.local",
            password_hash="x",
            role=UserRole.PASSENGER,
        )
        database_session.add(user)
        database_session.flush()

        passenger = Passenger(
            user_id=user.id,
            first_name="Test",
            last_name=f"P{tag}",
            phone="000000",
            date_of_birth=datetime(1990, 1, 1).date(),
            passport_number=f"PA{tag}",
        )
        database_session.add(passenger)
        database_session.flush()

        # Find a free seat
        from app.repositories import BookingRepository
        repo = BookingRepository(database_session)
        available = repo.get_available_seats_for_flight(flight.id)
        if not available:
            pytest.skip("No available seats for test flight.")
        seat = available[0]

        booking = Booking(
            booking_reference=f"TN{tag}",
            passenger_id=passenger.id,
            flight_id=flight.id,
            seat_id=seat.id,
            fare_amount=Decimal("500.00"),
            status=status,
        )
        database_session.add(booking)
        database_session.commit()

        created_ids.append(booking.id)
        return booking

    yield _create

    # Cleanup — strict FK-safe delete order:
    #   Baggage -> BoardingPass -> CheckIn -> Booking
    #   -> Flight -> Passenger -> User
    try:
        from app.models import Baggage, BoardingPass

        for booking_id in created_ids:
            booking = database_session.get(Booking, booking_id)
            if booking is None:
                continue

            flight_id = booking.flight_id
            passenger_id = booking.passenger_id

            checkin = (
                database_session.query(CheckIn)
                .filter(CheckIn.booking_id == booking.id)
                .first()
            )

            # 1. Baggage attached to this check-in
            if checkin is not None:
                bags = (
                    database_session.query(Baggage)
                    .filter(Baggage.checkin_id == checkin.id)
                    .all()
                )
                for bag in bags:
                    database_session.delete(bag)
                database_session.flush()

            # 2. Boarding pass attached to this booking
            bpass = (
                database_session.query(BoardingPass)
                .filter(BoardingPass.booking_id == booking.id)
                .first()
            )
            if bpass is not None:
                database_session.delete(bpass)
                database_session.flush()

            # 3. The check-in itself
            if checkin is not None:
                database_session.delete(checkin)
                database_session.flush()

            # 4. The booking
            database_session.delete(booking)
            database_session.flush()

            # 5. The flight
            flight = database_session.get(Flight, flight_id)
            if flight is not None:
                database_session.delete(flight)
                database_session.flush()

            # 6. The passenger and its user
            passenger = database_session.get(Passenger, passenger_id)
            if passenger is not None:
                user_id = passenger.user_id
                database_session.delete(passenger)
                database_session.flush()

                user = database_session.get(User, user_id)
                if user is not None:
                    database_session.delete(user)
                    database_session.flush()

        database_session.commit()
    except Exception:
        database_session.rollback()
        raise


# ======================================================================


def test_check_in_confirmed_booking_succeeds(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = CheckInService(database_session)
    checkin = service.check_in_booking(booking_id=booking.id)
    assert checkin.id is not None
    assert checkin.status == CheckInStatus.CHECKED_IN


def test_check_in_flips_booking_status(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = CheckInService(database_session)
    service.check_in_booking(booking_id=booking.id)
    database_session.refresh(booking)
    assert booking.status == BookingStatus.CHECKED_IN


def test_check_in_unpaid_booking_rejected(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.UNPAID)
    service = CheckInService(database_session)
    with pytest.raises(ResourceConflictError):
        service.check_in_booking(booking_id=booking.id)


def test_check_in_cancelled_booking_rejected(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CANCELLED)
    service = CheckInService(database_session)
    with pytest.raises(ResourceConflictError):
        service.check_in_booking(booking_id=booking.id)


def test_check_in_refunded_booking_rejected(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.REFUNDED)
    service = CheckInService(database_session)
    with pytest.raises(ResourceConflictError):
        service.check_in_booking(booking_id=booking.id)


def test_check_in_after_departure_rejected(database_session, booking_factory):
    # Flight departs 1 day AGO
    booking = booking_factory(
        status=BookingStatus.CONFIRMED,
        departure_offset_days=-1,
    )
    service = CheckInService(database_session)
    with pytest.raises(ResourceConflictError):
        service.check_in_booking(booking_id=booking.id)


def test_check_in_already_checked_in_rejected(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = CheckInService(database_session)
    service.check_in_booking(booking_id=booking.id)
    with pytest.raises(ResourceConflictError):
        service.check_in_booking(booking_id=booking.id)


def test_get_checkin_by_booking(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = CheckInService(database_session)
    service.check_in_booking(booking_id=booking.id)
    checkin = service.get_checkin_by_booking(booking.id)
    assert checkin.booking_id == booking.id


def test_get_checkin_by_booking_missing_raises(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = CheckInService(database_session)
    with pytest.raises(ResourceNotFoundError):
        service.get_checkin_by_booking(booking.id)


def test_cancel_checkin_reverts_status(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = CheckInService(database_session)
    checkin = service.check_in_booking(booking_id=booking.id)
    service.cancel_checkin(checkin.id)
    database_session.refresh(booking)
    assert booking.status == BookingStatus.CONFIRMED
