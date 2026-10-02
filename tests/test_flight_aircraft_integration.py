from datetime import datetime, timedelta

import pytest

from app.config.database import SessionLocal
from app.models import Aircraft, AircraftStatus, Route, UserRole
from app.services.application import application_context
from app.services.flight_service import FlightService


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def flight_service(database_session):
    application_context.session._current_user = type(
        "User",
        (),
        {
            "user_id": 1,
            "email": "admin@test.local",
            "role": UserRole.ADMIN,
        },
    )()

    yield FlightService(database_session)

    application_context.session.logout()


@pytest.fixture
def active_aircraft(database_session):
    """Return any ACTIVE aircraft from the database."""

    aircraft = (
        database_session.query(Aircraft)
        .filter(Aircraft.status == AircraftStatus.ACTIVE)
        .first()
    )

    if aircraft is None:
        pytest.skip("No ACTIVE aircraft in the database.")

    return aircraft


@pytest.fixture
def active_route(database_session):
    """Return any ACTIVE route from the database."""

    route = (
        database_session.query(Route)
        .filter(Route.is_active.is_(True))
        .first()
    )

    if route is None:
        pytest.skip("No ACTIVE route in the database.")

    return route


def test_create_flight_assigns_aircraft(
    flight_service,
    active_aircraft,
    active_route,
    database_session,
):
    from app.models import Flight

    start = datetime(2030, 1, 1, 10, 0)
    end = start + timedelta(hours=1)

    flight = None

    try:
        flight = flight_service.create_flight(
            flight_number="OM101",
            route_id=active_route.id,
            aircraft_id=active_aircraft.id,
            departure_time=start,
            arrival_time=end,
            base_fare=500,
        )

        assert flight.aircraft_id == active_aircraft.id
        assert flight.route_id == active_route.id

    finally:
        # Cleanup: delete the flight if it was created
        if flight is not None:
            stored = database_session.get(Flight, flight.id)

            if stored is not None:
                database_session.delete(stored)
                database_session.commit()

        # Also clean any leftover OM101 from a previous failed run
        leftover = (
            database_session.query(Flight)
            .filter(Flight.flight_number == "OM101")
            .first()
        )

        if leftover is not None:
            database_session.delete(leftover)
            database_session.commit()