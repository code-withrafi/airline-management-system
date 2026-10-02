import pytest
from PySide6.QtWidgets import QApplication

from app.gui.components.aircraft_form import AircraftFormDialog
from app.models import AircraftStatus


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


def test_aircraft_form_default_mode(qapp):
    dialog = AircraftFormDialog()

    assert (
        "Add Aircraft"
        in dialog.windowTitle()
    )


def test_aircraft_form_load_existing(qapp):
    aircraft = type(
        "Aircraft",
        (),
        {
            "registration_number": "OM-A01",
            "manufacturer": "Airbus",
            "model": "A320-200",
            "seat_capacity": 30,
            "status": AircraftStatus.ACTIVE,
        },
    )()

    dialog = AircraftFormDialog(
        aircraft=aircraft
    )

    assert (
        dialog.registration_input.text()
        == "OM-A01"
    )

    assert (
        dialog.manufacturer_input.text()
        == "Airbus"
    )

    assert (
        dialog.model_input.text()
        == "A320-200"
    )

    assert (
        dialog.seat_capacity_input.value()
        == 30
    )


def test_get_form_data(qapp):
    dialog = AircraftFormDialog()

    dialog.registration_input.setText(
        "om-t01"
    )

    dialog.manufacturer_input.setText(
        "Airbus"
    )

    dialog.model_input.setText(
        "Test Plane"
    )

    dialog.seat_capacity_input.setValue(
        20
    )

    data = dialog.get_data()

    assert (
        data["registration_number"]
        == "OM-T01"
    )

    assert (
        data["manufacturer"]
        == "Airbus"
    )

    assert (
        data["model"]
        == "Test Plane"
    )

    assert (
        data["seat_capacity"]
        == 20
    )