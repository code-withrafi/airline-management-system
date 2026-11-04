# app/gui/admin/flight_management.py
from datetime import date

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QMessageBox,
)

from app.gui.components.flight_form import (
    FlightForm,
)

from app.gui.components.flight_table import (
    FlightTable,
)

from app.gui.admin.overbooking_advisor import (
    OverbookingAdvisorPanel,
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
        super().__init__(parent)

        self.session = session
        self._all_flights = []          # cache for client-side filtering

        self.setup_ui()

    # ==================================================================
    # UI
    # ==================================================================

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

        # --- Overbooking Advisor (initially hidden) ---
        self.overbooking_advisor = OverbookingAdvisorPanel(
            self.session
        )
        self.overbooking_advisor.setVisible(False)

        layout.addWidget(self.flight_form)
        layout.addWidget(self._build_filter_toolbar())
        layout.addWidget(self._build_status_toolbar())
        layout.addWidget(self.flight_table)
        layout.addWidget(self.overbooking_advisor)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.refresh_table()

    # ------------------------------------------------------------------
    # Filter toolbar
    # ------------------------------------------------------------------

    def _build_filter_toolbar(self) -> QWidget:

        container = QWidget()
        bar = QHBoxLayout(container)
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(10)

        # --- Search ---
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search by flight number, route (DAC-CXB), gate..."
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumHeight(38)
        self.search_input.setMinimumWidth(280)
        self.search_input.textChanged.connect(self._apply_filters)
        bar.addWidget(self.search_input, 1)

        # --- Status filter ---
        status_label = QLabel("Status:")
        status_label.setStyleSheet("color: #64748B; font-size: 12px;")
        bar.addWidget(status_label)

        self.status_filter = QComboBox()
        self.status_filter.setMinimumHeight(38)
        self.status_filter.setMinimumWidth(150)
        self.status_filter.addItem("All statuses", None)
        for s in FlightStatus:
            self.status_filter.addItem(s.value.capitalize(), s)
        self.status_filter.currentIndexChanged.connect(self._apply_filters)
        bar.addWidget(self.status_filter)

        # --- From date ---
        from_label = QLabel("From:")
        from_label.setStyleSheet("color: #64748B; font-size: 12px;")
        bar.addWidget(from_label)

        self.from_date_input = QDateEdit()
        self.from_date_input.setCalendarPopup(True)
        self.from_date_input.setDisplayFormat("yyyy-MM-dd")
        self.from_date_input.setDate(QDate.currentDate())
        self.from_date_input.setMinimumHeight(38)
        self.from_date_input.setMinimumWidth(130)
        self.from_date_input.dateChanged.connect(self._apply_filters)
        bar.addWidget(self.from_date_input)

        # --- To date ---
        to_label = QLabel("To:")
        to_label.setStyleSheet("color: #64748B; font-size: 12px;")
        bar.addWidget(to_label)

        self.to_date_input = QDateEdit()
        self.to_date_input.setCalendarPopup(True)
        self.to_date_input.setDisplayFormat("yyyy-MM-dd")
        self.to_date_input.setDate(QDate.currentDate().addMonths(1))
        self.to_date_input.setMinimumHeight(38)
        self.to_date_input.setMinimumWidth(130)
        self.to_date_input.dateChanged.connect(self._apply_filters)
        bar.addWidget(self.to_date_input)

        # --- Reset button ---
        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("airportRefreshButton")
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.setMinimumHeight(38)
        self.reset_button.clicked.connect(self._reset_filters)
        bar.addWidget(self.reset_button)

        return container

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

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _on_selection_changed(self) -> None:

        flight = self.flight_table.get_selected_flight()

        has_selection = flight is not None

        self.boarding_button.setEnabled(has_selection)
        self.departed_button.setEnabled(has_selection)
        self.arrived_button.setEnabled(has_selection)
        self.delayed_button.setEnabled(has_selection)
        self.cancel_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)

        # --- Overbooking Advisor ---
        if flight is None:
            self.overbooking_advisor.setVisible(False)
        else:
            self.overbooking_advisor.setVisible(True)
            self.overbooking_advisor.load_for_flight(
                flight.id,
                flight_number=flight.flight_number,
            )

    # ------------------------------------------------------------------
    # Data load
    # ------------------------------------------------------------------

    def refresh_table(self) -> None:

        try:
            # On-demand completion: catch any flights that expired
            # since the last background sweep ran (up to 60s ago).
            try:
                from app.services.flight_completion_service import (
                    FlightCompletionService,
                )
                FlightCompletionService(self.session).complete_expired_flights()
            except Exception:
                # Non-fatal — proceed with the refresh regardless
                pass

            service = FlightService(self.session)
            self._all_flights = service.get_all_flights()
            self._apply_filters()
        except DatabaseOperationError as error:
            self.status_label.setText("Unable to load flights.")
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            self.status_label.setText("Unable to load flights.")
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{error}",
            )

    # ------------------------------------------------------------------
    # Filtering (client-side)
    # ------------------------------------------------------------------

    def _reset_filters(self) -> None:
        """Reset all filter controls to defaults."""
        self.search_input.blockSignals(True)
        self.status_filter.blockSignals(True)
        self.from_date_input.blockSignals(True)
        self.to_date_input.blockSignals(True)

        self.search_input.clear()
        self.status_filter.setCurrentIndex(0)
        self.from_date_input.setDate(QDate.currentDate())
        self.to_date_input.setDate(QDate.currentDate().addMonths(1))

        self.search_input.blockSignals(False)
        self.status_filter.blockSignals(False)
        self.from_date_input.blockSignals(False)
        self.to_date_input.blockSignals(False)

        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply search + status + date filters to the cached flight list."""

        text = self.search_input.text().strip().lower()
        status_value = self.status_filter.currentData()
        from_qd = self.from_date_input.date()
        to_qd = self.to_date_input.date()

        from_date = date(from_qd.year(), from_qd.month(), from_qd.day())
        to_date = date(to_qd.year(), to_qd.month(), to_qd.day())

        filtered = []

        for flight in self._all_flights:

            # -------- Status filter --------
            if status_value is not None and flight.status != status_value:
                continue

            # -------- Date filter --------
            dep = flight.departure_time.date()
            if dep < from_date or dep > to_date:
                continue

            # -------- Text filter --------
            if text:
                # Build searchable blob
                route = getattr(flight, "route", None)
                origin = (
                    route.origin_airport.iata_code.lower()
                    if route and route.origin_airport
                    else ""
                )
                destination = (
                    route.destination_airport.iata_code.lower()
                    if route and route.destination_airport
                    else ""
                )
                gate = (flight.boarding_gate or "").lower()

                haystack = " ".join([
                    flight.flight_number.lower(),
                    origin,
                    destination,
                    f"{origin}-{destination}",
                    f"{origin}->{destination}",
                    gate,
                ])

                if text not in haystack:
                    continue

            filtered.append(flight)

        self.flight_table.set_flights(filtered)

        total = len(self._all_flights)
        shown = len(filtered)

        if shown == total:
            self.status_label.setText(f"Showing {total} flight(s).")
        else:
            self.status_label.setText(
                f"Showing {shown} of {total} flight(s)."
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
            QMessageBox.warning(self, "Invalid Transition", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Flight Not Found", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
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
            QMessageBox.warning(self, "Cannot Delete Flight", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Flight Not Found", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{error}",
            )