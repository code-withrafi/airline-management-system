import pytest

from app.config.database import SessionLocal
from app.models import Airport, UserRole
from app.services import (
    AirportService,
    application_context,
)
from app.services.auth_result import AuthenticationResult
from app.services.exceptions import (
    AuthorizationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def airport_service(database_session):
    return AirportService(database_session)


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


def test_airport_service_requires_admin(
    airport_service,
):
    logout()

    with pytest.raises(AuthorizationError):
        airport_service.get_all_airports()

    logout()


def test_airport_service_rejects_staff(
    airport_service,
):
    login_as(UserRole.STAFF)

    with pytest.raises(AuthorizationError):
        airport_service.get_all_airports()

    logout()


def test_airport_service_rejects_passenger(
    airport_service,
):
    login_as(UserRole.PASSENGER)

    with pytest.raises(AuthorizationError):
        airport_service.get_all_airports()

    logout()


def test_airport_service_allows_admin(
    airport_service,
):
    login_as(UserRole.ADMIN)

    airports = airport_service.get_all_airports()

    assert isinstance(airports, list)
    assert len(airports) >= 4

    logout()


def test_airport_count(
    airport_service,
):
    login_as(UserRole.ADMIN)

    count = airport_service.get_airport_count()

    assert isinstance(count, int)
    assert count >= 4

    logout()


def test_search_airports(
    airport_service,
):
    login_as(UserRole.ADMIN)

    airports = airport_service.search_airports(
        "Dhaka"
    )

    assert isinstance(airports, list)

    assert any(
        airport.iata_code == "DAC"
        for airport in airports
    )

    logout()


@pytest.mark.parametrize(
    "iata_code",
    [
        "",
        "DA",
        "DACA",
        "D1C",
        "12C",
    ],
)
def test_invalid_iata_code(
    airport_service,
    iata_code,
):
    login_as(UserRole.ADMIN)

    with pytest.raises(ValidationError):
        airport_service.create_airport(
            iata_code=iata_code,
            icao_code="TEST",
            name="Test Airport",
            city="Test City",
            country="Test Country",
            timezone="Asia/Dhaka",
        )

    logout()


@pytest.mark.parametrize(
    "icao_code",
    [
        "",
        "VGE",
        "VGEGG",
        "VGE1",
        "1234",
    ],
)
def test_invalid_icao_code(
    airport_service,
    icao_code,
):
    login_as(UserRole.ADMIN)

    with pytest.raises(ValidationError):
        airport_service.create_airport(
            iata_code="TST",
            icao_code=icao_code,
            name="Test Airport",
            city="Test City",
            country="Test Country",
            timezone="Asia/Dhaka",
        )

    logout()


def test_required_fields(
    airport_service,
):
    login_as(UserRole.ADMIN)

    with pytest.raises(ValidationError):
        airport_service.create_airport(
            iata_code="TST",
            icao_code="VTST",
            name="",
            city="Test City",
            country="Test Country",
            timezone="Asia/Dhaka",
        )

    logout()


def test_duplicate_iata_code(
    airport_service,
):
    login_as(UserRole.ADMIN)

    with pytest.raises(ResourceConflictError):
        airport_service.create_airport(
            iata_code="DAC",
            icao_code="VTST",
            name="Duplicate Airport",
            city="Test City",
            country="Bangladesh",
            timezone="Asia/Dhaka",
        )

    logout()


def test_duplicate_icao_code(
    airport_service,
):
    login_as(UserRole.ADMIN)

    with pytest.raises(ResourceConflictError):
        airport_service.create_airport(
            iata_code="TST",
            icao_code="VGHS",
            name="Duplicate Airport",
            city="Test City",
            country="Bangladesh",
            timezone="Asia/Dhaka",
        )

    logout()


def test_admin_can_get_airport(
    airport_service,
):
    login_as(UserRole.ADMIN)

    airports = airport_service.get_all_airports()

    assert airports

    airport = airport_service.get_airport(
        airports[0].id
    )

    assert airport is not None
    assert airport.id == airports[0].id

    logout()


def test_missing_airport_id(
    airport_service,
):
    from app.services.exceptions import (
        ResourceNotFoundError,
    )

    login_as(UserRole.ADMIN)

    with pytest.raises(ResourceNotFoundError):
        airport_service.get_airport(999999)

    logout()


def test_admin_can_create_airport(
    airport_service,
    database_session,
):
    login_as(UserRole.ADMIN)

    airport = None

    try:
        airport = airport_service.create_airport(
            iata_code="TST",
            icao_code="VTST",
            name="Test International Airport",
            city="Test City",
            country="Test Country",
            timezone="Asia/Dhaka",
        )

        assert airport.id is not None
        assert airport.iata_code == "TST"
        assert airport.icao_code == "VTST"
        assert (
            airport.name
            == "Test International Airport"
        )

    finally:
        if airport is not None:
            stored = database_session.get(
                Airport,
                airport.id,
            )

            if stored is not None:
                database_session.delete(stored)
                database_session.commit()

        logout()


def test_admin_can_update_airport(
    airport_service,
    database_session,
):
    login_as(UserRole.ADMIN)

    airport = airport_service.create_airport(
        iata_code="UPD",
        icao_code="VUPD",
        name="Update Test Airport",
        city="Update City",
        country="Bangladesh",
        timezone="Asia/Dhaka",
    )

    try:
        updated_airport = (
            airport_service.update_airport(
                airport.id,
                iata_code="UPX",
                icao_code="VUPX",
                name="Updated Test Airport",
                city="Updated City",
                country="Bangladesh",
                timezone="Asia/Dhaka",
            )
        )

        assert updated_airport.id == airport.id
        assert updated_airport.iata_code == "UPX"
        assert updated_airport.icao_code == "VUPX"
        assert (
            updated_airport.name
            == "Updated Test Airport"
        )
        assert updated_airport.city == "Updated City"

    finally:
        stored = database_session.get(
            Airport,
            airport.id,
        )

        if stored is not None:
            database_session.delete(stored)
            database_session.commit()

        logout()


def test_update_airport_rejects_duplicate_iata(
    airport_service,
    database_session,
):
    login_as(UserRole.ADMIN)

    airport = airport_service.create_airport(
        iata_code="UPA",
        icao_code="VUPA",
        name="Update Airport A",
        city="City A",
        country="Bangladesh",
        timezone="Asia/Dhaka",
    )

    try:
        airport_service.update_airport(
            airport.id,
            iata_code="DAC",
            icao_code="VUPA",
            name="Update Airport A",
            city="City A",
            country="Bangladesh",
            timezone="Asia/Dhaka",
        )

        assert False, (
            "Expected ResourceConflictError"
        )

    except ResourceConflictError:
        pass

    finally:
        stored = database_session.get(
            Airport,
            airport.id,
        )

        if stored is not None:
            database_session.delete(stored)
            database_session.commit()

        logout()


def test_admin_can_delete_airport(
    airport_service,
    database_session,
):
    login_as(UserRole.ADMIN)

    airport = airport_service.create_airport(
        iata_code="DEL",
        icao_code="VDEL",
        name="Delete Test Airport",
        city="Delete City",
        country="Bangladesh",
        timezone="Asia/Dhaka",
    )

    airport_id = airport.id

    airport_service.delete_airport(
        airport_id
    )

    deleted_airport = (
        database_session.get(
            Airport,
            airport_id,
        )
    )

    assert deleted_airport is None

    logout()


def test_delete_missing_airport_raises_not_found(
    airport_service,
):
    login_as(UserRole.ADMIN)

    with pytest.raises(
        ResourceNotFoundError
    ):
        airport_service.delete_airport(
            999999
        )

    logout()


def test_delete_airport_used_by_route_is_rejected(
    airport_service,
):
    login_as(UserRole.ADMIN)

    airport = airport_service.repository.get_by_iata_code(
        "DAC"
    )

    assert airport is not None

    with pytest.raises(
        ResourceConflictError
    ):
        airport_service.delete_airport(
            airport.id
        )

    logout()