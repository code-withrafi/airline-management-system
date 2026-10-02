import pytest
from sqlalchemy.exc import IntegrityError

from app.config.database import SessionLocal
from app.models import (
    Aircraft,
    AircraftStatus,
    Booking,
    BookingStatus,
    Passenger,
    Seat,
    User,
    UserRole,
)
from app.services.aircraft_service import AircraftService
from app.services.application import application_context


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def aircraft_factory(database_session):
    created_ids = []

    def _create(
        registration_number=None,
        manufacturer="Airbus",
        model="A320",
        seat_capacity=10,
    ):
        import uuid

        if registration_number is None:
            registration_number = (
                "OM-TEST" + uuid.uuid4().hex[:5].upper()
            )

        application_context.session._current_user = type(
            "User",
            (),
            {
                "user_id": 1,
                "email": "admin@test.com",
                "role": UserRole.ADMIN,
            },
        )()

        service = AircraftService(database_session)

        aircraft = service.create_aircraft(
            registration_number=registration_number,
            manufacturer=manufacturer,
            model=model,
            seat_capacity=seat_capacity,
            status=AircraftStatus.ACTIVE,
        )

        created_ids.append(aircraft.id)
        return aircraft

    yield _create

    for aircraft_id in created_ids:
        stored = database_session.get(Aircraft, aircraft_id)

        if stored is not None:
            database_session.delete(stored)

    try:
        database_session.commit()
    except Exception:
        database_session.rollback()

    application_context.session.logout()


def test_booked_seat_cannot_be_deleted(
    database_session,
    aircraft_factory,
):
    """
    A seat that has an active booking must not be deletable.

    The FK Booking.seat_id -> Seat.id defaults to NO ACTION, so
    PostgreSQL raises an IntegrityError when we try.
    """

    aircraft = aircraft_factory(seat_capacity=10)

    # Grab any seat on this aircraft (1A is fine)
    seat = (
        database_session
        .query(Seat)
        .filter(
            Seat.aircraft_id == aircraft.id,
            Seat.seat_number == "1A",
        )
        .first()
    )

    assert seat is not None, "Expected seat 1A to exist"

    # Minimal Passenger + User + Booking so the FK is satisfied
    import uuid
    from datetime import date

    # Ensure we have a user for the passenger
    user = User(
        email=f"p-{uuid.uuid4().hex[:8]}@test.local",
        password_hash="x",
        role=UserRole.PASSENGER,
    )
    database_session.add(user)
    database_session.flush()

    passenger = Passenger(
        user_id=user.id,
        first_name="Test",
        last_name="Passenger",
        phone="000000",
        date_of_birth=date(1990, 1, 1),
        passport_number=f"P{uuid.uuid4().hex[:8].upper()}",
    )
    database_session.add(passenger)
    database_session.flush()

    # We also need a flight for the booking
    from app.models import Flight, FlightStatus, Route, Airport

    # Reuse any existing route + flight
    flight = database_session.query(Flight).first()

    if flight is None:
        pytest.skip("No flights exist in the DB — cannot test booking FK")

    booking = Booking(
        booking_reference=f"REF{uuid.uuid4().hex[:8].upper()}",
        passenger_id=passenger.id,
        flight_id=flight.id,
        seat_id=seat.id,
        fare_amount=100.00,
        status=BookingStatus.CONFIRMED,
    )

    database_session.add(booking)
    database_session.commit()

    # Now the protection check — deleting the seat must fail
    database_session.delete(seat)

    with pytest.raises(IntegrityError):
        database_session.commit()

    database_session.rollback()