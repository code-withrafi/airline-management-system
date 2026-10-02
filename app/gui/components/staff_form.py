from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class StaffFormDialog(QDialog):
    """
    Create/edit dialog for staff members.

    In create mode, takes an email + password to create the
    underlying User. In edit mode, only staff fields are editable.
    """

    def __init__(self, parent=None, staff=None):

        super().__init__(parent)

        self.staff = staff

        self.setWindowTitle(
            "Edit Staff" if staff else "Add Staff"
        )

        self.setMinimumWidth(420)

        self._build_ui()

        if staff is not None:
            self._load_staff()

    def _build_ui(self):

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("staff@example.com")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("At least 6 characters")

        if self.staff is None:
            form.addRow("Email:", self.email_input)
            form.addRow("Password:", self.password_input)

        self.employee_id_input = QLineEdit()
        self.employee_id_input.setPlaceholderText("EMP001")

        if self.staff is not None:
            # Employee ID is immutable after creation
            self.employee_id_input.setEnabled(False)

        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.position_input = QLineEdit()

        form.addRow("Employee ID:", self.employee_id_input)
        form.addRow("First name:", self.first_name_input)
        form.addRow("Last name:", self.last_name_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Position:", self.position_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def _load_staff(self):

        self.employee_id_input.setText(self.staff.employee_id)
        self.first_name_input.setText(self.staff.first_name)
        self.last_name_input.setText(self.staff.last_name)
        self.phone_input.setText(self.staff.phone)
        self.position_input.setText(self.staff.position)

    def validate_and_accept(self):

        if not self.employee_id_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error",
                "Employee ID is required.",
            )
            return

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

        if not self.position_input.text().strip():
            QMessageBox.warning(
                self, "Validation Error",
                "Position is required.",
            )
            return

        if self.staff is None:
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

        data = {
            "first_name": self.first_name_input.text().strip(),
            "last_name": self.last_name_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "position": self.position_input.text().strip(),
        }

        if self.staff is None:
            data["employee_id"] = (
                self.employee_id_input.text().strip()
            )
            data["email"] = self.email_input.text().strip().lower()
            data["password"] = self.password_input.text()

        return data
