import pytest

from app.config.database import SessionLocal
from app.models import Aircraft, AircraftStatus, UserRole
from app.services.aircraft_service import AircraftService
from app.services.application import application_context


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def login_as_admin():
    application_context.session._current_user = type(
        "User",
        (),
        {
            "user_id": 1,
            "email": "admin@test.com",
            "role": UserRole.ADMIN,
        },
    )()


def logout():
    application_context.session.logout()


def test_aircraft_creation_generates_seats(
    database_session,
):
    login_as_admin()

    aircraft = None

    try:
        service = AircraftService(
            database_session
        )

        aircraft = service.create_aircraft(
            registration_number="OM-SEAT01",
            manufacturer="Airbus",
            model="A320",
            seat_capacity=30,
            status=AircraftStatus.ACTIVE,
        )

        assert len(aircraft.seats) == 30

        seat_numbers = {s.seat_number for s in aircraft.seats}

        assert "1A" in seat_numbers
        assert "10A" in seat_numbers

    finally:
        if aircraft is not None:
            stored = database_session.get(
                Aircraft,
                aircraft.id,
            )

            if stored is not None:
                database_session.delete(stored)
                database_session.commit()

        logout()