from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
)

from app.gui.components.staff_selector import (
    StaffSelector,
)

from app.models.flight_staff import (
    AssignmentRole,
)

from app.services.staff_assignment_service import (
    StaffAssignmentService,
)

from app.services.exceptions import (
    ValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    DatabaseOperationError,
)


class CrewAssignmentWidget(QWidget):
    """
    Widget responsible for assigning and removing
    staff members from selected flights.
    """

    def __init__(
        self,
        session,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.session = session

        self.flight_id = None

        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        title = QLabel(
            "Flight Crew Assignment"
        )

        layout.addWidget(
            title
        )

        controls = QHBoxLayout()

        self.staff_selector = StaffSelector(
            self.session
        )

        self.role_selector = QComboBox()

        for role in AssignmentRole:

            self.role_selector.addItem(
                role.value,
                role
            )

        self.assign_button = QPushButton(
            "Assign Staff"
        )

        self.assign_button.setEnabled(
            False
        )

        controls.addWidget(
            self.staff_selector
        )

        controls.addWidget(
            self.role_selector
        )

        controls.addWidget(
            self.assign_button
        )

        layout.addLayout(
            controls
        )

        self.crew_table = QTableWidget()

        self.crew_table.setColumnCount(
            3
        )

        self.crew_table.setHorizontalHeaderLabels(
            [
                "Employee ID",
                "Name",
                "Role",
            ]
        )

        self.crew_table.itemSelectionChanged.connect(
            self._on_crew_selection_changed
        )

        layout.addWidget(
            self.crew_table
        )

        self.remove_button = QPushButton(
            "Remove Selected Crew"
        )

        self.remove_button.setEnabled(
            False
        )

        layout.addWidget(
            self.remove_button
        )

        self.setLayout(
            layout
        )

        self.assign_button.clicked.connect(
            self.assign_staff
        )

        self.remove_button.clicked.connect(
            self.remove_staff
        )

    # ------------------------------------------------------------------
    # Flight binding
    # ------------------------------------------------------------------

    def set_flight(
        self,
        flight_id: int | None,
    ):

        self.flight_id = flight_id

        has_flight = (
            flight_id is not None
        )

        self.assign_button.setEnabled(
            has_flight
        )

        self.remove_button.setEnabled(
            False
        )

        if not has_flight:

            self.crew_table.setRowCount(
                0
            )

            return

        self.load_crew()

    # ------------------------------------------------------------------
    # Crew list
    # ------------------------------------------------------------------

    def load_crew(self):

        self.crew_table.setRowCount(
            0
        )

        self.remove_button.setEnabled(
            False
        )

        if self.flight_id is None:

            return

        try:

            service = (
                StaffAssignmentService(
                    self.session
                )
            )

            assignments = (
                service.get_flight_crew(
                    self.flight_id
                )
            )

            for assignment in assignments:

                row = (
                    self.crew_table.rowCount()
                )

                self.crew_table.insertRow(
                    row
                )

                employee_item = QTableWidgetItem(
                    assignment.staff.employee_id
                )

                employee_item.setData(
                    Qt.ItemDataRole.UserRole,
                    assignment.staff.id,
                )

                self.crew_table.setItem(
                    row,
                    0,
                    employee_item
                )

                self.crew_table.setItem(
                    row,
                    1,
                    QTableWidgetItem(
                        (
                            assignment.staff.first_name
                            +
                            " "
                            +
                            assignment.staff.last_name
                        )
                    )
                )

                self.crew_table.setItem(
                    row,
                    2,
                    QTableWidgetItem(
                        assignment.assigned_role.value
                    )
                )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                str(error),
            )

    def refresh_crew(self):

        if self.flight_id is None:

            self.crew_table.setRowCount(
                0
            )

            return

        self.load_crew()

    def _on_crew_selection_changed(self):

        has_selection = (
            self.crew_table.currentRow() >= 0
        )

        self.remove_button.setEnabled(
            has_selection
        )

    # ------------------------------------------------------------------
    # Assign
    # ------------------------------------------------------------------

    def assign_staff(self):

        if self.flight_id is None:

            QMessageBox.warning(
                self,
                "No Flight Selected",
                "Please select a flight first.",
            )

            return

        staff_id = (
            self.staff_selector
            .get_selected_staff_id()
        )

        if staff_id is None:

            QMessageBox.warning(
                self,
                "No Staff Selected",
                "Please select a staff member.",
            )

            return

        role = (
            self.role_selector
            .currentData()
        )

        try:

            service = (
                StaffAssignmentService(
                    self.session
                )
            )

            service.assign_staff(
                flight_id=self.flight_id,
                staff_id=staff_id,
                assigned_role=role,
            )

            self.load_crew()

            QMessageBox.information(
                self,
                "Assignment Successful",
                "Staff member assigned successfully.",
            )

            self.staff_selector.setCurrentIndex(
                -1
            )

        except ValidationError as error:

            QMessageBox.warning(
                self,
                "Validation Error",
                str(error),
            )

        except ResourceConflictError as error:

            QMessageBox.warning(
                self,
                "Assignment Conflict",
                str(error),
            )

        except ResourceNotFoundError as error:

            QMessageBox.warning(
                self,
                "Not Found",
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
                (
                    "An unexpected error occurred:\n\n"
                    f"{error}"
                ),
            )

    # ------------------------------------------------------------------
    # Remove
    # ------------------------------------------------------------------

    def remove_staff(self):

        if self.flight_id is None:

            QMessageBox.warning(
                self,
                "No Flight Selected",
                "Please select a flight first.",
            )

            return

        row = (
            self.crew_table.currentRow()
        )

        if row < 0:

            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a crew member.",
            )

            return

        employee_item = (
            self.crew_table.item(
                row,
                0
            )
        )

        staff_id = (
            employee_item.data(
                Qt.ItemDataRole.UserRole
            )
        )

        employee_id = employee_item.text()

        confirmation = QMessageBox.question(
            self,
            "Confirm Removal",
            (
                f"Remove {employee_id} from "
                "this flight's crew?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:

            return

        try:

            service = (
                StaffAssignmentService(
                    self.session
                )
            )

            service.remove_staff(
                flight_id=self.flight_id,
                staff_id=staff_id,
            )

            self.load_crew()

            QMessageBox.information(
                self,
                "Removed",
                "Staff member removed successfully.",
            )

        except ResourceNotFoundError as error:

            QMessageBox.warning(
                self,
                "Not Found",
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
                str(error),
            )