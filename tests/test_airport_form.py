from PySide6.QtWidgets import QApplication

from app.gui.components import AirportFormDialog


def get_application():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


def test_airport_form_can_be_created():
    get_application()

    dialog = AirportFormDialog()

    assert dialog.windowTitle() == "Add Airport"
    assert dialog.iata_input.text() == ""
    assert dialog.icao_input.text() == ""
    assert dialog.name_input.text() == ""


def test_airport_form_can_return_data():
    get_application()

    dialog = AirportFormDialog()

    dialog.iata_input.setText("dac")
    dialog.icao_input.setText("vghs")
    dialog.name_input.setText(
        "Hazrat Shahjalal International Airport"
    )
    dialog.city_input.setText("Dhaka")
    dialog.country_input.setText("Bangladesh")
    dialog.timezone_input.setText("Asia/Dhaka")

    data = dialog.get_data()

    assert data["iata_code"] == "DAC"
    assert data["icao_code"] == "VGHS"
    assert (
        data["name"]
        == "Hazrat Shahjalal International Airport"
    )
    assert data["city"] == "Dhaka"
    assert data["country"] == "Bangladesh"
    assert data["timezone"] == "Asia/Dhaka"


def test_airport_form_populates_existing_airport():
    get_application()

    class Airport:
        iata_code = "DAC"
        icao_code = "VGHS"
        name = "Hazrat Shahjalal International Airport"
        city = "Dhaka"
        country = "Bangladesh"
        timezone = "Asia/Dhaka"

    dialog = AirportFormDialog(
        airport=Airport()
    )

    assert dialog.windowTitle() == "Edit Airport"
    assert dialog.iata_input.text() == "DAC"
    assert dialog.icao_input.text() == "VGHS"
    assert (
        dialog.name_input.text()
        == "Hazrat Shahjalal International Airport"
    )
    assert dialog.city_input.text() == "Dhaka"
    assert dialog.country_input.text() == "Bangladesh"
    assert dialog.timezone_input.text() == "Asia/Dhaka"