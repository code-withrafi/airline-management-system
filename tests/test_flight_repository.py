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


def test_create_flight(
    database_session,
    route_factory,
    aircraft_factory,
):
    route = route_factory()
    aircraft = aircraft_factory()

    flight = Flight(
        flight_number="OM101",
        route_id=route.id,
        aircraft_id=aircraft.id,
        departure_time=datetime(2026, 10, 1, 10, 0, 0),
        arrival_time=datetime(2026, 10, 1, 14, 0, 0),
        base_fare=500,
        status=FlightStatus.SCHEDULED,
    )

    try:
        database_session.add(flight)
        database_session.commit()

        result = (
            database_session
            .query(Flight)
            .filter(Flight.flight_number == "OM101")
            .first()
        )

        assert result is not None
        assert result.flight_number == "OM101"
        assert result.route_id == route.id
        assert result.aircraft_id == aircraft.id
        assert result.status == FlightStatus.SCHEDULED

    finally:
        stored = (
            database_session
            .query(Flight)
            .filter(Flight.flight_number == "OM101")
            .first()
        )

        if stored is not None:
            database_session.delete(stored)
            database_session.commit()