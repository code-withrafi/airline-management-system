from datetime import datetime

import pytest

from app.config.database import SessionLocal
from app.models import (
    Aircraft,
    AircraftStatus,
    Airport,
    Route,
    UserRole,
)
from app.models.flight import (
    Flight,
    FlightStatus,
)
from app.services.aircraft_service import AircraftService
from app.services.application import application_context
from app.services.exceptions import ValidationError
from app.services.flight_service import FlightService


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def admin_login():
    application_context.session._current_user = type(
        "User",
        (),
        {
            "user_id": 1,
            "email": "admin@test.com",
            "role": UserRole.ADMIN,
        },
    )()

    yield

    application_context.session.logout()


@pytest.fixture
def flight_service(database_session, admin_login):
    return FlightService(database_session)


@pytest.fixture
def aircraft_factory(database_session, admin_login):
    import uuid

    created_ids = []

    def _create(
        registration_number=None,
        manufacturer="Airbus",
        model="A320",
        seat_capacity=10,
    ):
        if registration_number is None:
            registration_number = (
                "OM-TEST" + uuid.uuid4().hex[:5].upper()
            )

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

    database_session.commit()


@pytest.fixture
def route_factory(database_session):
    created_ids = []

    def _create():
        airports = (
            database_session
            .query(Airport)
            .limit(2)
            .all()
        )

        if len(airports) < 2:
            pytest.skip(
                "Need at least 2 airports in the DB to create a route."
            )

        route = Route(
            origin_airport_id=airports[0].id,
            destination_airport_id=airports[1].id,
            distance_km=300,
            estimated_duration_minutes=60,
            is_active=True,
        )

        database_session.add(route)
        database_session.flush()

        created_ids.append(route.id)
        return route

    yield _create

    for route_id in created_ids:
        stored = database_session.get(Route, route_id)

        if stored is not None:
            database_session.delete(stored)

    database_session.commit()


@pytest.fixture
def flight_factory(
    database_session,
    flight_service,
    route_factory,
    aircraft_factory,
):
    created_ids = []

    def _create(
        flight_number=None,
        status=FlightStatus.SCHEDULED,
    ):
        import uuid

        if flight_number is None:
            flight_number = (
                "OM-T" + uuid.uuid4().hex[:4].upper()
            )

        route = route_factory()
        aircraft = aircraft_factory()

        flight = flight_service.create_flight(
            flight_number=flight_number,
            route_id=route.id,
            aircraft_id=aircraft.id,
            departure_time=datetime(2026, 10, 1, 10, 0),
            arrival_time=datetime(2026, 10, 1, 14, 0),
            base_fare=500,
        )

        created_ids.append(flight.id)

        # Drive the flight to the requested status via valid transitions
        if status != FlightStatus.SCHEDULED:
            _drive_to(flight, status)

        return flight

    def _drive_to(flight, target_status):
        # Valid chain: SCHEDULED → BOARDING → DEPARTED → ARRIVED
        chain = {
            FlightStatus.SCHEDULED: [],
            FlightStatus.BOARDING: [FlightStatus.BOARDING],
            FlightStatus.DEPARTED: [
                FlightStatus.BOARDING,
                FlightStatus.DEPARTED,
            ],
            FlightStatus.ARRIVED: [
                FlightStatus.BOARDING,
                FlightStatus.DEPARTED,
                FlightStatus.ARRIVED,
            ],
            FlightStatus.DELAYED: [FlightStatus.DELAYED],
            FlightStatus.CANCELLED: [FlightStatus.CANCELLED],
        }

        for step in chain[target_status]:
            flight_service.update_status(flight.id, step)

    yield _create

    for flight_id in created_ids:
        stored = database_session.get(Flight, flight_id)

        if stored is not None:
            database_session.delete(stored)

    database_session.commit()


# ----------------------------------------------------------------------
# No-op transition
# ----------------------------------------------------------------------


def test_same_status_is_noop(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.SCHEDULED)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.SCHEDULED,
    )

    assert result.status == FlightStatus.SCHEDULED


# ----------------------------------------------------------------------
# Allowed transitions
# ----------------------------------------------------------------------


def test_scheduled_can_board(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.SCHEDULED)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.BOARDING,
    )

    assert result.status == FlightStatus.BOARDING


def test_scheduled_can_be_delayed(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.SCHEDULED)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.DELAYED,
    )

    assert result.status == FlightStatus.DELAYED


def test_scheduled_can_be_cancelled(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.SCHEDULED)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.CANCELLED,
    )

    assert result.status == FlightStatus.CANCELLED


def test_boarding_can_be_delayed(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.BOARDING)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.DELAYED,
    )

    assert result.status == FlightStatus.DELAYED


def test_boarding_can_be_cancelled(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.BOARDING)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.CANCELLED,
    )

    assert result.status == FlightStatus.CANCELLED


def test_boarding_can_depart(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.BOARDING)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.DEPARTED,
    )

    assert result.status == FlightStatus.DEPARTED


def test_delayed_can_board(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.DELAYED)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.BOARDING,
    )

    assert result.status == FlightStatus.BOARDING


def test_delayed_can_depart(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.DELAYED)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.DEPARTED,
    )

    assert result.status == FlightStatus.DEPARTED


def test_departed_can_arrive(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.DEPARTED)

    result = flight_service.update_status(
        flight.id,
        FlightStatus.ARRIVED,
    )

    assert result.status == FlightStatus.ARRIVED


# ----------------------------------------------------------------------
# Blocked transitions
# ----------------------------------------------------------------------


def test_arrived_cannot_change(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.ARRIVED)

    with pytest.raises(ValidationError):
        flight_service.update_status(
            flight.id,
            FlightStatus.BOARDING,
        )


def test_cancelled_cannot_change(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.CANCELLED)

    with pytest.raises(ValidationError):
        flight_service.update_status(
            flight.id,
            FlightStatus.SCHEDULED,
        )


def test_scheduled_cannot_jump_to_departed(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.SCHEDULED)

    with pytest.raises(ValidationError):
        flight_service.update_status(
            flight.id,
            FlightStatus.DEPARTED,
        )


def test_scheduled_cannot_jump_to_arrived(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.SCHEDULED)

    with pytest.raises(ValidationError):
        flight_service.update_status(
            flight.id,
            FlightStatus.ARRIVED,
        )


def test_departed_cannot_go_back_to_boarding(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.DEPARTED)

    with pytest.raises(ValidationError):
        flight_service.update_status(
            flight.id,
            FlightStatus.BOARDING,
        )


def test_delayed_cannot_arrive(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.DELAYED)

    with pytest.raises(ValidationError):
        flight_service.update_status(
            flight.id,
            FlightStatus.ARRIVED,
        )


# ----------------------------------------------------------------------
# Full lifecycle
# ----------------------------------------------------------------------


def test_full_flight_lifecycle(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.SCHEDULED)

    flight_service.update_status(flight.id, FlightStatus.BOARDING)
    assert flight_service.get_flight(flight.id).status == FlightStatus.BOARDING

    flight_service.update_status(flight.id, FlightStatus.DEPARTED)
    assert flight_service.get_flight(flight.id).status == FlightStatus.DEPARTED

    flight_service.update_status(flight.id, FlightStatus.ARRIVED)
    assert flight_service.get_flight(flight.id).status == FlightStatus.ARRIVED


# ----------------------------------------------------------------------
# Cancel convenience method
# ----------------------------------------------------------------------


def test_cancel_flight_wrapper(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.SCHEDULED)

    result = flight_service.cancel_flight(flight.id)

    assert result.status == FlightStatus.CANCELLED


def test_cannot_cancel_arrived_flight(
    flight_service,
    flight_factory,
):
    flight = flight_factory(status=FlightStatus.ARRIVED)

    with pytest.raises(ValidationError):
        flight_service.cancel_flight(flight.id)