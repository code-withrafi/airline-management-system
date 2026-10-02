from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from app.models import AircraftStatus


class AircraftFormDialog(QDialog):
    """
    Reusable aircraft create/update dialog.
    """

    def __init__(
        self,
        parent=None,
        aircraft=None,
    ):
        super().__init__(
            parent
        )

        self.aircraft = aircraft

        self.setWindowTitle(
            "Edit Aircraft"
            if aircraft
            else "Add Aircraft"
        )

        self.setMinimumWidth(
            400
        )

        self._build_ui()

        if aircraft:
            self._load_aircraft()

    # -------------------------------------------------
    # UI
    # -------------------------------------------------

    def _build_ui(self):

        layout = QVBoxLayout(
            self
        )

        form_layout = QFormLayout()

        self.registration_input = (
            QLineEdit()
        )

        self.registration_input.setPlaceholderText(
            "Example: OM-A01"
        )

        self.manufacturer_input = (
            QLineEdit()
        )

        self.manufacturer_input.setPlaceholderText(
            "Example: Airbus"
        )

        self.model_input = (
            QLineEdit()
        )

        self.model_input.setPlaceholderText(
            "Example: A320-200"
        )

        self.seat_capacity_input = (
            QSpinBox()
        )

        self.seat_capacity_input.setMinimum(
            1
        )

        self.seat_capacity_input.setMaximum(
            1000
        )

        self.status_input = (
            QComboBox()
        )

        for status in AircraftStatus:
            self.status_input.addItem(
                status.value,
                status,
            )

        form_layout.addRow(
            "Registration:",
            self.registration_input,
        )

        form_layout.addRow(
            "Manufacturer:",
            self.manufacturer_input,
        )

        form_layout.addRow(
            "Model:",
            self.model_input,
        )

        form_layout.addRow(
            "Seat Capacity:",
            self.seat_capacity_input,
        )

        form_layout.addRow(
            "Status:",
            self.status_input,
        )

        layout.addLayout(
            form_layout
        )

        self.buttons = (
            QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save
                |
                QDialogButtonBox.StandardButton.Cancel
            )
        )

        self.buttons.accepted.connect(
            self.validate_and_accept
        )

        self.buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(
            self.buttons
        )

    # -------------------------------------------------
    # Load Existing Aircraft
    # -------------------------------------------------

    def _load_aircraft(self):

        self.registration_input.setText(
            self.aircraft.registration_number
        )

        self.manufacturer_input.setText(
            self.aircraft.manufacturer
        )

        self.model_input.setText(
            self.aircraft.model
        )

        self.seat_capacity_input.setValue(
            self.aircraft.seat_capacity
        )

        index = (
            self.status_input
            .findData(
                self.aircraft.status
            )
        )

        if index >= 0:
            self.status_input.setCurrentIndex(
                index
            )

    # -------------------------------------------------
    # Validation
    # -------------------------------------------------

    def validate_and_accept(self):

        registration = (
            self.registration_input
            .text()
            .strip()
        )

        manufacturer = (
            self.manufacturer_input
            .text()
            .strip()
        )

        model = (
            self.model_input
            .text()
            .strip()
        )

        seat_capacity = (
            self.seat_capacity_input
            .value()
        )

        if not registration:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Registration number is required.",
            )

            return

        if not manufacturer:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Aircraft manufacturer is required.",
            )

            return

        if not model:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Aircraft model is required.",
            )

            return

        if seat_capacity <= 0:

            QMessageBox.warning(
                self,
                "Validation Error",
                "Seat capacity must be greater than zero.",
            )

            return

        self.accept()

    # -------------------------------------------------
    # Get Data
    # -------------------------------------------------

    def get_data(self):

        return {

            "registration_number":
                self.registration_input
                .text()
                .strip()
                .upper(),

            "manufacturer":
                self.manufacturer_input
                .text()
                .strip(),

            "model":
                self.model_input
                .text()
                .strip(),

            "seat_capacity":
                self.seat_capacity_input
                .value(),

            "status":
                self.status_input
                .currentData(),
        }