from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
)

from PySide6.QtCore import Qt

from app.gui.components.flight_form import (
    FlightForm,
)

from app.gui.components.flight_table import (
    FlightTable,
)

from app.models.flight import FlightStatus
from app.services.flight_service import FlightService
from app.services.exceptions import (
    ValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    DatabaseOperationError,
)


class FlightManagementPage(QWidget):

    def __init__(
        self,
        session,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.session = session

        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        self.flight_form = FlightForm(
            self.session,
            self.refresh_table,
        )

        self.flight_table = FlightTable()

        self.flight_table.itemSelectionChanged.connect(
            self._on_selection_changed
        )

        layout.addWidget(
            self.flight_form
        )

        layout.addWidget(
            self._build_status_toolbar()
        )

        layout.addWidget(
            self.flight_table
        )

        self.status_label = QLabel()
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        layout.addWidget(
            self.status_label
        )

        self.setLayout(
            layout
        )

        self.refresh_table()

    # ------------------------------------------------------------------
    # Status toolbar
    # ------------------------------------------------------------------

    def _build_status_toolbar(self) -> QWidget:

        container = QWidget()
        bar = QHBoxLayout(container)
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(8)

        self.boarding_button = QPushButton("Set Boarding")
        self.departed_button = QPushButton("Set Departed")
        self.arrived_button = QPushButton("Set Arrived")
        self.delayed_button = QPushButton("Set Delayed")
        self.cancel_button = QPushButton("Cancel Flight")
        self.delete_button = QPushButton("Delete Flight")

        buttons = [
            self.boarding_button,
            self.departed_button,
            self.arrived_button,
            self.delayed_button,
            self.cancel_button,
            self.delete_button,
        ]

        for button in buttons:
            button.setEnabled(False)
            bar.addWidget(button)

        bar.addStretch()

        self.boarding_button.clicked.connect(
            lambda: self._change_status(FlightStatus.BOARDING)
        )
        self.departed_button.clicked.connect(
            lambda: self._change_status(FlightStatus.DEPARTED)
        )
        self.arrived_button.clicked.connect(
            lambda: self._change_status(FlightStatus.ARRIVED)
        )
        self.delayed_button.clicked.connect(
            lambda: self._change_status(FlightStatus.DELAYED)
        )
        self.cancel_button.clicked.connect(
            lambda: self._change_status(FlightStatus.CANCELLED)
        )
        self.delete_button.clicked.connect(
            self._delete_selected_flight
        )

        return container

    def _on_selection_changed(self) -> None:

        flight = self.flight_table.get_selected_flight()

        has_selection = flight is not None

        self.boarding_button.setEnabled(has_selection)
        self.departed_button.setEnabled(has_selection)
        self.arrived_button.setEnabled(has_selection)
        self.delayed_button.setEnabled(has_selection)
        self.cancel_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

    # ------------------------------------------------------------------
    # Data load
    # ------------------------------------------------------------------

    def refresh_table(self) -> None:

        try:
            service = FlightService(self.session)
            flights = service.get_all_flights()
            self.flight_table.set_flights(flights)
            self.status_label.setText(
                f"Showing {len(flights)} flight(s)."
            )
        except DatabaseOperationError as error:
            self.status_label.setText(
                "Unable to load flights."
            )
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )
        except Exception as error:
            self.status_label.setText(
                "Unable to load flights."
            )
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{error}",
            )

        self._on_selection_changed()

    # ------------------------------------------------------------------
    # Status change
    # ------------------------------------------------------------------

    def _change_status(self, new_status) -> None:

        flight = self.flight_table.get_selected_flight()

        if flight is None:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a flight first.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Status Change",
            (
                f"Change flight {flight.flight_number} "
                f"status from {flight.status.value} "
                f"to {new_status.value}?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = FlightService(self.session)
            service.update_status(flight.id, new_status)
            self.refresh_table()
            QMessageBox.information(
                self,
                "Flight Status Updated",
                (
                    f"Flight {flight.flight_number} "
                    f"is now {new_status.value}."
                ),
            )

        except ValidationError as error:
            QMessageBox.warning(
                self,
                "Invalid Transition",
                str(error),
            )
        except ResourceNotFoundError as error:
            QMessageBox.warning(
                self,
                "Flight Not Found",
                str(error),
            )
        except DatabaseOperationError as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{error}",
            )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def _delete_selected_flight(self) -> None:

        flight = self.flight_table.get_selected_flight()

        if flight is None:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a flight first.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Delete",
            (
                f"Delete flight {flight.flight_number}?\n\n"
                "This action cannot be undone. Flights with "
                "existing bookings cannot be deleted."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = FlightService(self.session)
            service.delete_flight(flight.id)
            self.refresh_table()
            QMessageBox.information(
                self,
                "Flight Deleted",
                f"Flight {flight.flight_number} was deleted.",
            )

        except ResourceConflictError as error:
            QMessageBox.warning(
                self,
                "Cannot Delete Flight",
                str(error),
            )
        except ResourceNotFoundError as error:
            QMessageBox.warning(
                self,
                "Flight Not Found",
                str(error),
            )
        except DatabaseOperationError as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{error}",
            )