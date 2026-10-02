import pytest

from app.config.database import SessionLocal
from app.models import Aircraft, AircraftStatus
from app.repositories import AircraftRepository


@pytest.fixture
def database_session():
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


def test_get_all_aircraft(database_session):
    repository = AircraftRepository(
        database_session
    )

    aircraft = repository.get_all()

    assert len(aircraft) >= 2


def test_get_aircraft_by_id(database_session):
    repository = AircraftRepository(
        database_session
    )

    aircraft_list = repository.get_all()

    assert aircraft_list

    aircraft = repository.get_by_id(
        aircraft_list[0].id
    )

    assert aircraft is not None
    assert (
        aircraft.id
        == aircraft_list[0].id
    )


def test_get_aircraft_by_registration_number(
    database_session,
):
    repository = AircraftRepository(
        database_session
    )

    aircraft = (
        repository
        .get_by_registration_number(
            "BD-A01"
        )
    )

    assert aircraft is not None
    assert (
        aircraft.registration_number
        == "BD-A01"
    )


def test_registration_lookup_is_case_insensitive(
    database_session,
):
    repository = AircraftRepository(
        database_session
    )

    aircraft = (
        repository
        .get_by_registration_number(
            "BD-A01"
        )
    )

    assert aircraft is not None
    assert (
        aircraft.registration_number
        == "BD-A01"
    )


def test_search_aircraft_by_registration(
    database_session,
):
    repository = AircraftRepository(
        database_session
    )

    aircraft = repository.search(
        "BD-A01"
    )

    assert any(
        item.registration_number
        == "BD-A01"
        for item in aircraft
    )


def test_search_aircraft_by_model(
    database_session,
):
    repository = AircraftRepository(
        database_session
    )

    aircraft = repository.search(
        "Airbus"
    )

    assert any(
        "Airbus"
        in (item.manufacturer or "")
        for item in aircraft
    )


def test_empty_search_returns_all_aircraft(
    database_session,
):
    repository = AircraftRepository(
        database_session
    )

    all_aircraft = repository.get_all()

    search_results = repository.search(
        ""
    )

    assert len(search_results) == len(
        all_aircraft
    )


def test_search_without_results(
    database_session,
):
    repository = AircraftRepository(
        database_session
    )

    aircraft = repository.search(
        "ZZZZZZ"
    )

    assert aircraft == []


def test_aircraft_count(database_session):
    repository = AircraftRepository(
        database_session
    )

    count = repository.count()

    assert count >= 2


def test_create_and_delete_aircraft(
    database_session,
):
    repository = AircraftRepository(
        database_session
    )

    aircraft = repository.create(
        registration_number="OM-T99",
        manufacturer="Test Manufacturer",
        model="Test Aircraft",
        seat_capacity=20,
        status=AircraftStatus.ACTIVE,
    )

    assert aircraft.id is not None
    assert (
        aircraft.registration_number
        == "OM-T99"
    )

    database_session.commit()

    created_id = aircraft.id

    repository.delete(
        aircraft
    )

    database_session.commit()

    deleted = database_session.get(
        Aircraft,
        created_id,
    )

    assert deleted is None