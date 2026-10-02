from PySide6.QtWidgets import QApplication

from app.gui.components import AirportTable


def test_airport_table_can_be_created():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    table = AirportTable()

    assert table.columnCount() == 6
    assert table.rowCount() == 0


def test_airport_table_can_display_airports():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    class Airport:
        iata_code = "DAC"
        icao_code = "VGHS"
        name = "Hazrat Shahjalal International Airport"
        city = "Dhaka"
        country = "Bangladesh"
        timezone = "Asia/Dhaka"

    table = AirportTable()

    table.set_airports(
        [Airport()]
    )

    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "DAC"
    assert table.item(0, 1).text() == "VGHS"
    assert (
        table.item(0, 2).text()
        == "Hazrat Shahjalal International Airport"
    )
    assert table.item(0, 3).text() == "Dhaka"
    assert table.item(0, 4).text() == "Bangladesh"
    assert table.item(0, 5).text() == "Asia/Dhaka"


def test_airport_table_can_clear():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    class Airport:
        iata_code = "DAC"
        icao_code = "VGHS"
        name = "Test Airport"
        city = "Dhaka"
        country = "Bangladesh"
        timezone = "Asia/Dhaka"

    table = AirportTable()

    table.set_airports(
        [Airport()]
    )

    assert table.airport_count() == 1

    table.clear_airports()

    assert table.airport_count() == 0


def test_airport_table_returns_selected_airport():
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    class Airport:
        def __init__(
            self,
            iata_code,
            icao_code,
            name,
            city,
            country,
            timezone,
        ):
            self.iata_code = iata_code
            self.icao_code = icao_code
            self.name = name
            self.city = city
            self.country = country
            self.timezone = timezone

    airport_one = Airport(
        "AAA",
        "VAAA",
        "Airport One",
        "City One",
        "Bangladesh",
        "Asia/Dhaka",
    )

    airport_two = Airport(
        "BBB",
        "VBBB",
        "Airport Two",
        "City Two",
        "Bangladesh",
        "Asia/Dhaka",
    )

    table = AirportTable()

    table.set_airports(
        [
            airport_one,
            airport_two,
        ]
    )

    table.selectRow(1)

    selected = table.get_selected_airport()

    assert selected is airport_two