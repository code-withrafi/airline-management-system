from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QDateTimeEdit,
    QDoubleSpinBox,
    QMessageBox,
)

from PySide6.QtCore import QDateTime

from app.gui.components.aircraft_selector import (
    AircraftSelector,
)

from app.services.flight_service import FlightService
from app.services.exceptions import (
    ValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    DatabaseOperationError,
)


class FlightForm(QWidget):

    def __init__(
        self,
        session,
        refresh_callback=None,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.session = session

        self.refresh_callback = refresh_callback

        self.flight_service = FlightService(
            session
        )

        self.setup_ui()

    def setup_ui(self):

        layout = QFormLayout()

        self.flight_number_input = QLineEdit()

        layout.addRow(
            "Flight Number:",
            self.flight_number_input
        )

        self.route_select = QComboBox()

        layout.addRow(
            "Route:",
            self.route_select
        )

        self.aircraft_selector = AircraftSelector(
            self.session
        )

        layout.addRow(
            self.aircraft_selector
        )

        self.departure_time = QDateTimeEdit()

        self.departure_time.setDateTime(
            QDateTime.currentDateTime()
        )

        self.departure_time.setCalendarPopup(
            True
        )

        layout.addRow(
            "Departure:",
            self.departure_time
        )

        self.arrival_time = QDateTimeEdit()

        self.arrival_time.setDateTime(
            QDateTime.currentDateTime()
        )

        self.arrival_time.setCalendarPopup(
            True
        )

        layout.addRow(
            "Arrival:",
            self.arrival_time
        )

        self.fare_input = QDoubleSpinBox()

        self.fare_input.setMaximum(
            100000
        )

        self.fare_input.setPrefix(
            "$ "
        )

        layout.addRow(
            "Base Fare:",
            self.fare_input
        )

        self.gate_input = QLineEdit()

        layout.addRow(
            "Boarding Gate:",
            self.gate_input
        )

        self.save_button = QPushButton(
            "Create Flight"
        )

        self.save_button.clicked.connect(
            self.create_flight
        )

        layout.addWidget(
            self.save_button
        )

        self.setLayout(
            layout
        )

        self.load_routes()

    def load_routes(self):

        from app.repositories import RouteRepository

        self.route_select.clear()

        repository = RouteRepository(self.session)

        for route in repository.get_all():
            if not route.is_active:
                continue

            origin = route.origin_airport.iata_code
            destination = route.destination_airport.iata_code

            self.route_select.addItem(
                f"{origin} \u2192 {destination}",
                route.id,
            )

    def create_flight(self):

        aircraft_id = (
            self.aircraft_selector
            .get_selected_aircraft_id()
        )

        if aircraft_id is None:

            QMessageBox.warning(
                self,
                "Aircraft Required",
                "Please select an aircraft."
            )

            return

        route_id = self.route_select.currentData()

        if route_id is None:

            QMessageBox.warning(
                self,
                "Route Required",
                "Please select a route."
            )

            return

        try:

            flight = (
                self.flight_service
                .create_flight(
                    flight_number=self.flight_number_input.text(),
                    route_id=route_id,
                    aircraft_id=aircraft_id,
                    departure_time=self.departure_time.dateTime().toPython(),
                    arrival_time=self.arrival_time.dateTime().toPython(),
                    base_fare=self.fare_input.value(),
                    boarding_gate=self.gate_input.text().strip() or None,
                )
            )

            QMessageBox.information(
                self,
                "Success",
                (
                    f"Flight "
                    f"{flight.flight_number}"
                    f" created successfully."
                )
            )

            self.clear_form()

            if self.refresh_callback is not None:
                self.refresh_callback()

        except (
            ValidationError,
            ResourceConflictError,
            ResourceNotFoundError,
        ) as exc:

            QMessageBox.warning(
                self,
                "Error",
                str(exc)
            )

        except DatabaseOperationError as exc:

            QMessageBox.critical(
                self,
                "Database Error",
                str(exc)
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{exc}"
            )

    def clear_form(self):

        self.flight_number_input.clear()

        self.fare_input.setValue(0)

        self.gate_input.clear()

        self.aircraft_selector.refresh()

        self.load_routes()
