from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from app.repositories import AirportRepository


class RouteFormDialog(QDialog):
    """
    Create/update dialog for routes.
    """

    def __init__(
        self,
        parent=None,
        session=None,
        route=None,
    ):
        super().__init__(parent)

        self.session = session
        self.route = route

        self.setWindowTitle(
            "Edit Route" if route else "Add Route"
        )

        self.setMinimumWidth(420)

        self._build_ui()

        if route is not None:
            self._load_route()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.origin_input = QComboBox()
        self.destination_input = QComboBox()

        self._populate_airports()

        self.distance_input = QSpinBox()
        self.distance_input.setMinimum(1)
        self.distance_input.setMaximum(20000)
        self.distance_input.setSuffix(" km")

        self.duration_input = QSpinBox()
        self.duration_input.setMinimum(1)
        self.duration_input.setMaximum(1440)
        self.duration_input.setSuffix(" min")

        self.is_active_input = QCheckBox("Route is active")
        self.is_active_input.setChecked(True)

        form_layout.addRow("Origin airport:", self.origin_input)
        form_layout.addRow("Destination airport:", self.destination_input)
        form_layout.addRow("Distance:", self.distance_input)
        form_layout.addRow("Estimated duration:", self.duration_input)
        form_layout.addRow("", self.is_active_input)

        layout.addLayout(form_layout)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def _populate_airports(self) -> None:
        """Fill both dropdowns with every airport."""

        self.origin_input.clear()
        self.destination_input.clear()

        if self.session is None:
            return

        repository = AirportRepository(self.session)
        airports = repository.get_all()

        for airport in airports:
            label = (
                f"{airport.iata_code} — "
                f"{airport.name} ({airport.city})"
            )

            self.origin_input.addItem(label, airport.id)
            self.destination_input.addItem(label, airport.id)

    # ------------------------------------------------------------------
    # Load existing
    # ------------------------------------------------------------------

    def _load_route(self) -> None:
        self._select_by_id(
            self.origin_input,
            self.route.origin_airport_id,
        )
        self._select_by_id(
            self.destination_input,
            self.route.destination_airport_id,
        )

        self.distance_input.setValue(
            self.route.distance_km
        )
        self.duration_input.setValue(
            self.route.estimated_duration_minutes
        )
        self.is_active_input.setChecked(
            bool(self.route.is_active)
        )

    @staticmethod
    def _select_by_id(combo: QComboBox, value) -> None:
        index = combo.findData(value)

        if index >= 0:
            combo.setCurrentIndex(index)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_and_accept(self) -> None:
        origin_id = self.origin_input.currentData()
        destination_id = self.destination_input.currentData()

        if origin_id is None or destination_id is None:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please select both origin and destination airports.",
            )
            return

        if origin_id == destination_id:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Origin and destination airports must be different.",
            )
            return

        self.accept()

    # ------------------------------------------------------------------
    # Data out
    # ------------------------------------------------------------------

    def get_data(self) -> dict:
        return {
            "origin_airport_id": self.origin_input.currentData(),
            "destination_airport_id": self.destination_input.currentData(),
            "distance_km": self.distance_input.value(),
            "estimated_duration_minutes": self.duration_input.value(),
            "is_active": self.is_active_input.isChecked(),
        }