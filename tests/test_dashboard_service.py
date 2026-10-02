import pytest

from app.config.database import SessionLocal
from app.models import UserRole
from app.services import DashboardService, application_context
from app.services.auth_result import AuthenticationResult


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def dashboard_service(database_session):
    return DashboardService(database_session)


def login_as(role: UserRole):
    application_context.session.login(
        AuthenticationResult(
            user_id=1,
            email=f"{role.value.lower()}@test.local",
            role=role,
        )
    )


def logout():
    application_context.session.logout()


def test_dashboard_service_requires_admin(dashboard_service):
    logout()

    with pytest.raises(PermissionError):
        dashboard_service.get_dashboard_statistics()

    logout()


def test_dashboard_service_rejects_staff(dashboard_service):
    login_as(UserRole.STAFF)

    with pytest.raises(PermissionError):
        dashboard_service.get_dashboard_statistics()

    logout()


def test_dashboard_service_rejects_passenger(dashboard_service):
    login_as(UserRole.PASSENGER)

    with pytest.raises(PermissionError):
        dashboard_service.get_dashboard_statistics()

    logout()


def test_dashboard_service_allows_admin(dashboard_service):
    login_as(UserRole.ADMIN)

    statistics = dashboard_service.get_dashboard_statistics()

    assert isinstance(statistics, dict)

    expected_keys = {
        "total_airports",
        "total_aircraft",
        "total_routes",
        "total_flights",
        "scheduled_flights",
        "cancelled_flights",
        "total_bookings",
        "total_passengers",
    }

    assert set(statistics.keys()) == expected_keys

    for value in statistics.values():
        assert isinstance(value, int)
        assert value >= 0

    logout()


def test_dashboard_service_recent_flights_requires_admin(
    dashboard_service,
):
    logout()

    with pytest.raises(PermissionError):
        dashboard_service.get_recent_flights()

    logout()


def test_dashboard_service_recent_flights_allows_admin(
    dashboard_service,
):
    login_as(UserRole.ADMIN)

    flights = dashboard_service.get_recent_flights()

    assert isinstance(flights, list)

    logout()


def test_dashboard_service_rejects_invalid_limit(
    dashboard_service,
):
    login_as(UserRole.ADMIN)

    flights = dashboard_service.get_recent_flights(0)

    assert flights == []

    flights = dashboard_service.get_recent_flights(-5)

    assert flights == []

    logout()