import pytest

from app.config.database import SessionLocal
from app.models import AircraftStatus
from app.services.flight_assignment_service import (
    FlightAssignmentService,
)


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def flight_assignment_service(database_session):
    return FlightAssignmentService(database_session)


def test_available_aircraft_only_active(
    flight_assignment_service,
):
    aircraft = (
        flight_assignment_service
        .get_available_aircraft()
    )

    for item in aircraft:
        assert (
            item.status
            ==
            AircraftStatus.ACTIVE
        )