import pytest

from app.config.database import SessionLocal
from app.models import Aircraft, AircraftStatus, UserRole
from app.services.application import application_context
from app.services.exceptions import ValidationError
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
def assignment_service(database_session):
    return FlightAssignmentService(database_session)


@pytest.fixture
def maintenance_aircraft(database_session):
    """Return any aircraft whose status is MAINTENANCE."""

    aircraft = (
        database_session.query(Aircraft)
        .filter(Aircraft.status == AircraftStatus.MAINTENANCE)
        .first()
    )

    if aircraft is None:
        pytest.skip("No MAINTENANCE aircraft in the database.")

    return aircraft


@pytest.fixture
def flight():
    """
    A stand-in for a Flight object.

    assign_aircraft only reads/writes `aircraft_id`, so a simple
    namespace is enough. This avoids needing to build a real
    Flight with route, aircraft, departure, arrival, etc.
    """

    return type(
        "FakeFlight",
        (),
        {"aircraft_id": 0},
    )()


def test_cannot_assign_maintenance_aircraft(
    assignment_service,
    flight,
    maintenance_aircraft,
):

    with pytest.raises(ValidationError):

        assignment_service.assign_aircraft(
            flight,
            maintenance_aircraft.id,
        )