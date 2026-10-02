from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from PySide6.QtCore import QDate


class PassengerFormDialog(QDialog):
    """
    Create/edit dialog for passengers.

    In create mode, takes an email + password and creates the
    underlying User. In edit mode, only passenger fields are
    editable.
    """

    def __init__(
        self,
        parent=None,
        passenger=None,
    ):

        super().__init__(parent)

        self.passenger = passenger

        self.setWindowTitle(
            "Edit Passenger"
            if passenger
            else "Add Passenger"
        )

        self.setMinimumWidth(420)

        self._build_ui()

        if passenger is not None:
            self._load_passenger()

    def _build_ui(self):

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText(
            "passenger@example.com"
        )

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_input.setPlaceholderText(
            "At least 6 characters"
        )

        if self.passenger is None:
            form.addRow("Email:", self.email_input)
            form.addRow("Password:", self.password_input)

        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.passport_input = QLineEdit()
        self.address_input = QLineEdit()

        self.dob_input = QDateEdit()
        self.dob_input.setCalendarPopup(True)
        self.dob_input.setDate(QDate(1990, 1, 1))

        form.addRow("First name:", self.first_name_input)
        form.addRow("Last name:", self.last_name_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Passport:", self.passport_input)
        form.addRow("Date of birth:", self.dob_input)
        form.addRow("Address:", self.address_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def _load_passenger(self):

        self.first_name_input.setText(
            self.passenger.first_name
        )
        self.last_name_input.setText(
            self.passenger.last_name
        )
        self.phone_input.setText(
            self.passenger.phone
        )
        self.passport_input.setText(
            self.passenger.passport_number
        )

        if self.passenger.date_of_birth:
            dob = self.passenger.date_of_birth
            self.dob_input.setDate(
                QDate(dob.year, dob.month, dob.day)
            )

        if self.passenger.address:
            self.address_input.setText(
                self.passenger.address
            )

    def validate_and_accept(self):

        if not self.first_name_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error",
                "First name is required.",
            )
            return

        if not self.last_name_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error",
                "Last name is required.",
            )
            return

        if not self.phone_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error",
                "Phone is required.",
            )
            return

        if not self.passport_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error",
                "Passport number is required.",
            )
            return

        if self.passenger is None:
            if not self.email_input.text().strip():
                QMessageBox.warning(
                    self, "Validation Error",
                    "Email is required.",
                )
                return

            if len(self.password_input.text()) < 6:
                QMessageBox.warning(
                    self, "Validation Error",
                    "Password must be at least 6 characters.",
                )
                return

        self.accept()

    def get_data(self) -> dict:

        dob = self.dob_input.date()

        data = {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "passport_number": self.passport_input.text().strip(),
            "date_of_birth": dob.toPython(),
            "address": self.address_input.text().strip() or None,
        }

        if self.passenger is None:
            data["email"] = self.email_input.text().strip().lower()
            data["password"] = self.password_input.text()

        return data
