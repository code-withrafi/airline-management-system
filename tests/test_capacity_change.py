import pytest

from app.config.database import SessionLocal
from app.models import Aircraft, AircraftStatus, UserRole
from app.services.application import application_context
from app.services.aircraft_service import AircraftService
from app.services.seat_management_service import (
    SeatManagementService,
)


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


def create_test_aircraft(
    database_session,
    registration_number="OM-CAP01",
    manufacturer="Airbus",
    model="A320",
    seat_capacity=30,
):
    service = AircraftService(database_session)

    return service.create_aircraft(
        registration_number=registration_number,
        manufacturer=manufacturer,
        model=model,
        seat_capacity=seat_capacity,
        status=AircraftStatus.ACTIVE,
    )


def test_capacity_increase_generates_new_seats(
    database_session,
):
    login_as_admin()

    aircraft = None

    try:
        aircraft = create_test_aircraft(
            database_session,
            registration_number="OM-CAP01",
            seat_capacity=30,
        )

        service = SeatManagementService(
            database_session
        )

        service.synchronize_capacity(
            aircraft,
            36,
        )

        database_session.commit()
        database_session.refresh(aircraft)

        assert len(aircraft.seats) == 36

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


def test_capacity_decrease_removes_unused_seats(
    database_session,
):
    login_as_admin()

    aircraft = None

    try:
        aircraft = create_test_aircraft(
            database_session,
            registration_number="OM-CAP02",
            seat_capacity=40,
        )

        service = SeatManagementService(
            database_session
        )

        service.synchronize_capacity(
            aircraft,
            30,
        )

        database_session.commit()
        database_session.refresh(aircraft)

        assert len(aircraft.seats) == 30

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