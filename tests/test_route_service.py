import pytest

from app.config.database import SessionLocal
from app.models import Airport, Route, UserRole
from app.services.application import application_context
from app.services.exceptions import (
    AuthorizationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.route_service import RouteService


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def login_as(role):
    application_context.session._current_user = type(
        "User",
        (),
        {
            "user_id": 1,
            "email": f"{role.value.lower()}@test.local",
            "role": role,
        },
    )()


def logout():
    application_context.session.logout()


def get_two_airports(database_session):
    airports = (
        database_session.query(Airport)
        .order_by(Airport.id)
        .limit(2)
        .all()
    )

    if len(airports) < 2:
        pytest.skip("Need at least 2 airports in the database.")

    return airports[0], airports[1]


# ======================================================================
# Authorization
# ======================================================================


def test_route_service_requires_admin(database_session):
    logout()

    with pytest.raises(AuthorizationError):
        RouteService(database_session).get_all_routes()


def test_route_service_rejects_staff(database_session):
    login_as(UserRole.STAFF)

    try:
        with pytest.raises(AuthorizationError):
            RouteService(database_session).get_all_routes()
    finally:
        logout()


# ======================================================================
# Read
# ======================================================================


def test_admin_can_get_all_routes(database_session):
    login_as(UserRole.ADMIN)

    try:
        routes = RouteService(database_session).get_all_routes()
        assert isinstance(routes, list)
    finally:
        logout()


# ======================================================================
# Validation
# ======================================================================


def test_same_origin_and_destination_is_rejected(database_session):
    login_as(UserRole.ADMIN)

    try:
        origin, _ = get_two_airports(database_session)

        with pytest.raises(ValidationError):
            RouteService(database_session).create_route(
                origin_airport_id=origin.id,
                destination_airport_id=origin.id,
                distance_km=300,
                estimated_duration_minutes=60,
            )
    finally:
        logout()


@pytest.mark.parametrize(
    "distance",
    [0, -1, 25000, "300", None, True],
)
def test_invalid_distance_is_rejected(database_session, distance):
    login_as(UserRole.ADMIN)

    try:
        origin, destination = get_two_airports(database_session)

        with pytest.raises(ValidationError):
            RouteService(database_session).create_route(
                origin_airport_id=origin.id,
                destination_airport_id=destination.id,
                distance_km=distance,
                estimated_duration_minutes=60,
            )
    finally:
        logout()


@pytest.mark.parametrize(
    "duration",
    [0, -1, 2000, "60", None, True],
)
def test_invalid_duration_is_rejected(database_session, duration):
    login_as(UserRole.ADMIN)

    try:
        origin, destination = get_two_airports(database_session)

        with pytest.raises(ValidationError):
            RouteService(database_session).create_route(
                origin_airport_id=origin.id,
                destination_airport_id=destination.id,
                distance_km=300,
                estimated_duration_minutes=duration,
            )
    finally:
        logout()


def test_missing_airport_is_rejected(database_session):
    login_as(UserRole.ADMIN)

    try:
        origin, _ = get_two_airports(database_session)

        with pytest.raises(ResourceNotFoundError):
            RouteService(database_session).create_route(
                origin_airport_id=origin.id,
                destination_airport_id=999999,
                distance_km=300,
                estimated_duration_minutes=60,
            )
    finally:
        logout()


# ======================================================================
# Full CRUD cycle
# ======================================================================


def test_admin_can_create_and_delete_route(database_session):
    login_as(UserRole.ADMIN)

    route = None

    try:
        origin, destination = get_two_airports(database_session)

        # Skip if the route already exists (re-run)
        existing = (
            database_session.query(Route)
            .filter_by(
                origin_airport_id=origin.id,
                destination_airport_id=destination.id,
            )
            .first()
        )

        if existing is not None:
            # Cannot delete if flights reference it
            from app.models import Flight
            if database_session.query(Flight).filter(
                Flight.route_id == existing.id
            ).count() > 0:
                pytest.skip(
                    "Existing route has flights; cannot safely delete."
                )
            database_session.delete(existing)
            database_session.commit()

        service = RouteService(database_session)

        route = service.create_route(
            origin_airport_id=origin.id,
            destination_airport_id=destination.id,
            distance_km=350,
            estimated_duration_minutes=55,
        )

        assert route.id is not None
        assert route.origin_airport_id == origin.id
        assert route.destination_airport_id == destination.id
        assert route.distance_km == 350
        assert route.estimated_duration_minutes == 55
        assert route.is_active is True

        route_id = route.id

        service.delete_route(route_id)
        route = None

        assert database_session.get(Route, route_id) is None

    finally:
        if route is not None:
            stored = database_session.get(Route, route.id)
            if stored is not None:
                database_session.delete(stored)
                database_session.commit()

        logout()


def test_duplicate_route_is_rejected(database_session):
    login_as(UserRole.ADMIN)

    route = None

    try:
        origin, destination = get_two_airports(database_session)

        # Clean any leftovers
        existing = (
            database_session.query(Route)
            .filter_by(
                origin_airport_id=origin.id,
                destination_airport_id=destination.id,
            )
            .first()
        )

        if existing is not None:
            # Cannot delete if flights reference it
            from app.models import Flight
            if database_session.query(Flight).filter(
                Flight.route_id == existing.id
            ).count() > 0:
                pytest.skip(
                    "Existing route has flights; cannot safely delete."
                )
            database_session.delete(existing)
            database_session.commit()

        service = RouteService(database_session)

        route = service.create_route(
            origin_airport_id=origin.id,
            destination_airport_id=destination.id,
            distance_km=350,
            estimated_duration_minutes=55,
        )

        with pytest.raises(ResourceConflictError):
            service.create_route(
                origin_airport_id=origin.id,
                destination_airport_id=destination.id,
                distance_km=400,
                estimated_duration_minutes=60,
            )

    finally:
        if route is not None:
            stored = database_session.get(Route, route.id)
            if stored is not None:
                database_session.delete(stored)
                database_session.commit()

        logout()