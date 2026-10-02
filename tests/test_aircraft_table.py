import pytest

from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from app.gui.components.aircraft_table import AircraftTable
from app.models import AircraftStatus


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


def make_aircraft(
    registration_number,
    manufacturer,
    model,
    seat_capacity,
    status,
):
    return SimpleNamespace(
        registration_number=registration_number,
        manufacturer=manufacturer,
        model=model,
        seat_capacity=seat_capacity,
        status=status,
        id=1,
    )


def test_aircraft_table_starts_empty(qapp):
    table = AircraftTable()

    assert table.aircraft_count() == 0
    assert table.rowCount() == 0


def test_aircraft_table_displays_aircraft(qapp):
    table = AircraftTable()

    aircraft = [
        make_aircraft(
            "OM-A01",
            "Airbus",
            "A320-200",
            30,
            AircraftStatus.ACTIVE,
        ),
        make_aircraft(
            "OM-B02",
            "Boeing",
            "737-800",
            40,
            AircraftStatus.ACTIVE,
        ),
    ]

    table.set_aircraft(aircraft)

    assert table.aircraft_count() == 2
    assert table.rowCount() == 2

    assert table.item(0, 0).text() == "OM-A01"
    assert table.item(0, 1).text() == "Airbus"
    assert table.item(0, 2).text() == "A320-200"
    assert table.item(0, 3).text() == "30"
    assert table.item(0, 4).text() == "ACTIVE"


def test_get_aircraft_at_row(qapp):
    table = AircraftTable()

    aircraft = make_aircraft(
        "OM-A01",
        "Airbus",
        "A320-200",
        30,
        AircraftStatus.ACTIVE,
    )

    table.set_aircraft([aircraft])

    result = table.get_aircraft_at_row(0)

    assert result is aircraft


def test_get_aircraft_at_invalid_row(qapp):
    table = AircraftTable()

    assert table.get_aircraft_at_row(0) is None


def test_get_selected_aircraft(qapp):
    table = AircraftTable()

    aircraft = make_aircraft(
        "OM-A01",
        "Airbus",
        "A320-200",
        30,
        AircraftStatus.ACTIVE,
    )

    table.set_aircraft([aircraft])

    table.selectRow(0)

    result = table.get_selected_aircraft()

    assert result is aircraft


def test_clear_aircraft(qapp):
    table = AircraftTable()

    aircraft = make_aircraft(
        "OM-A01",
        "Airbus",
        "A320-200",
        30,
        AircraftStatus.ACTIVE,
    )

    table.set_aircraft([aircraft])

    table.clear_aircraft()

    assert table.aircraft_count() == 0
    assert table.rowCount() == 0
    assert table.get_selected_aircraft() is None
