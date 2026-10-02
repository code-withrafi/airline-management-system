from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class AirportFormDialog(QDialog):
    """
    Reusable dialog for creating and editing airport information.

    This component handles user input and basic presentation-level
    validation only. Database operations and business rules remain
    in AirportService.
    """

    submitted = Signal(dict)

    def __init__(
        self,
        parent=None,
        airport=None,
    ):
        super().__init__(parent)

        self.airport = airport

        if airport is None:
            self.setWindowTitle("Add Airport")
        else:
            self.setWindowTitle("Edit Airport")

        self.setModal(True)
        self.setMinimumWidth(500)

        self._build_ui()
        self._apply_styles()

        if airport is not None:
            self._populate_from_airport(airport)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the airport form interface."""

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            28,
            24,
            28,
            24,
        )

        main_layout.setSpacing(20)

        form_layout = QFormLayout()

        form_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(14)

        # --------------------------------------------------------------
        # IATA
        # --------------------------------------------------------------

        self.iata_input = QLineEdit()

        self.iata_input.setObjectName(
            "airportFormInput"
        )

        self.iata_input.setMaxLength(3)
        self.iata_input.setPlaceholderText(
            "e.g. DAC"
        )

        self.iata_input.setToolTip(
            "3-letter IATA airport code"
        )

        form_layout.addRow(
            "IATA Code",
            self.iata_input,
        )

        # --------------------------------------------------------------
        # ICAO
        # --------------------------------------------------------------

        self.icao_input = QLineEdit()

        self.icao_input.setObjectName(
            "airportFormInput"
        )

        self.icao_input.setMaxLength(4)
        self.icao_input.setPlaceholderText(
            "e.g. VGHS"
        )

        self.icao_input.setToolTip(
            "4-letter ICAO airport code"
        )

        form_layout.addRow(
            "ICAO Code",
            self.icao_input,
        )

        # --------------------------------------------------------------
        # Airport Name
        # --------------------------------------------------------------

        self.name_input = QLineEdit()

        self.name_input.setObjectName(
            "airportFormInput"
        )

        self.name_input.setMaxLength(150)
        self.name_input.setPlaceholderText(
            "e.g. Hazrat Shahjalal International Airport"
        )

        form_layout.addRow(
            "Airport Name",
            self.name_input,
        )

        # --------------------------------------------------------------
        # City
        # --------------------------------------------------------------

        self.city_input = QLineEdit()

        self.city_input.setObjectName(
            "airportFormInput"
        )

        self.city_input.setMaxLength(100)
        self.city_input.setPlaceholderText(
            "e.g. Dhaka"
        )

        form_layout.addRow(
            "City",
            self.city_input,
        )

        # --------------------------------------------------------------
        # Country
        # --------------------------------------------------------------

        self.country_input = QLineEdit()

        self.country_input.setObjectName(
            "airportFormInput"
        )

        self.country_input.setMaxLength(100)
        self.country_input.setPlaceholderText(
            "e.g. Bangladesh"
        )

        form_layout.addRow(
            "Country",
            self.country_input,
        )

        # --------------------------------------------------------------
        # Timezone
        # --------------------------------------------------------------

        self.timezone_input = QLineEdit()

        self.timezone_input.setObjectName(
            "airportFormInput"
        )

        self.timezone_input.setMaxLength(100)
        self.timezone_input.setPlaceholderText(
            "e.g. Asia/Dhaka"
        )

        form_layout.addRow(
            "Timezone",
            self.timezone_input,
        )

        main_layout.addLayout(
            form_layout
        )

        # --------------------------------------------------------------
        # Buttons
        # --------------------------------------------------------------

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.accepted.connect(
            self._handle_submit
        )

        self.button_box.rejected.connect(
            self.reject
        )

        main_layout.addWidget(
            self.button_box
        )

        self.iata_input.setFocus()

    # ------------------------------------------------------------------
    # Populate existing airport
    # ------------------------------------------------------------------

    def _populate_from_airport(
        self,
        airport,
    ) -> None:
        """Populate the form with an existing airport."""

        self.iata_input.setText(
            getattr(
                airport,
                "iata_code",
                "",
            )
        )

        self.icao_input.setText(
            getattr(
                airport,
                "icao_code",
                "",
            )
        )

        self.name_input.setText(
            getattr(
                airport,
                "name",
                "",
            )
        )

        self.city_input.setText(
            getattr(
                airport,
                "city",
                "",
            )
        )

        self.country_input.setText(
            getattr(
                airport,
                "country",
                "",
            )
        )

        self.timezone_input.setText(
            getattr(
                airport,
                "timezone",
                "",
            )
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_form(self) -> bool:
        """
        Perform basic form validation.

        Detailed business validation is handled by AirportService.
        """

        fields = [
            (
                self.iata_input,
                "IATA Code",
            ),
            (
                self.icao_input,
                "ICAO Code",
            ),
            (
                self.name_input,
                "Airport Name",
            ),
            (
                self.city_input,
                "City",
            ),
            (
                self.country_input,
                "Country",
            ),
            (
                self.timezone_input,
                "Timezone",
            ),
        ]

        for field, label in fields:
            if not field.text().strip():
                QMessageBox.warning(
                    self,
                    "Validation Error",
                    f"{label} is required.",
                )

                field.setFocus()

                return False

        iata = self.iata_input.text().strip()

        if len(iata) != 3:
            QMessageBox.warning(
                self,
                "Validation Error",
                "IATA Code must contain exactly 3 characters.",
            )

            self.iata_input.setFocus()

            return False

        icao = self.icao_input.text().strip()

        if len(icao) != 4:
            QMessageBox.warning(
                self,
                "Validation Error",
                "ICAO Code must contain exactly 4 characters.",
            )

            self.icao_input.setFocus()

            return False

        if not iata.isalpha():
            QMessageBox.warning(
                self,
                "Validation Error",
                "IATA Code must contain letters only.",
            )

            self.iata_input.setFocus()

            return False

        if not icao.isalpha():
            QMessageBox.warning(
                self,
                "Validation Error",
                "ICAO Code must contain letters only.",
            )

            self.icao_input.setFocus()

            return False

        return True

    # ------------------------------------------------------------------
    # Submit
    # ------------------------------------------------------------------

    def _handle_submit(self) -> None:
        """Validate and emit the entered airport data."""

        if not self._validate_form():
            return

        data = {
            "iata_code": self.iata_input.text().strip().upper(),
            "icao_code": self.icao_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "city": self.city_input.text().strip(),
            "country": self.country_input.text().strip(),
            "timezone": self.timezone_input.text().strip(),
        }

        self.submitted.emit(data)

        self.accept()

    # ------------------------------------------------------------------
    # Public data access
    # ------------------------------------------------------------------

    def get_data(self) -> dict[str, str]:
        """
        Return the current form data.
        """

        return {
            "iata_code": self.iata_input.text().strip().upper(),
            "icao_code": self.icao_input.text().strip().upper(),
            "name": self.name_input.text().strip(),
            "city": self.city_input.text().strip(),
            "country": self.country_input.text().strip(),
            "timezone": self.timezone_input.text().strip(),
        }

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        """Apply styling to the dialog."""

        self.setStyleSheet(
            """
            QDialog {
                background-color: #FFFFFF;
                color: #0F172A;
            }

            QLabel {
                color: #334155;
                font-size: 12px;
                font-weight: 600;
            }

            QLineEdit#airportFormInput {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                color: #0F172A;
                padding: 9px 12px;
                font-size: 12px;
                min-height: 18px;
            }

            QLineEdit#airportFormInput:focus {
                background-color: #FFFFFF;
                border: 1px solid #64748B;
            }

            QDialogButtonBox QPushButton {
                min-width: 90px;
                min-height: 34px;
                border-radius: 8px;
                padding: 4px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QDialogButtonBox QPushButton[text="Save"] {
                background-color: #0F172A;
                color: #FFFFFF;
                border: none;
            }

            QDialogButtonBox QPushButton[text="Save"]:hover {
                background-color: #1E293B;
            }

            QDialogButtonBox QPushButton[text="Cancel"] {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
            }

            QDialogButtonBox QPushButton[text="Cancel"]:hover {
                background-color: #F8FAFC;
            }
            """
        )