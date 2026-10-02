from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class StaffTable(QTableWidget):

    HEADERS = [
        "Employee ID",
        "Name",
        "Position",
        "Phone",
        "Email",
    ]

    def __init__(self, parent=None):

        super().__init__(parent)

        self._staff = []

        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)

        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()
        for i, mode in enumerate([
            QHeaderView.ResizeMode.ResizeToContents,
            QHeaderView.ResizeMode.Stretch,
            QHeaderView.ResizeMode.ResizeToContents,
            QHeaderView.ResizeMode.ResizeToContents,
            QHeaderView.ResizeMode.Stretch,
        ]):
            header.setSectionResizeMode(i, mode)

        self.setMinimumHeight(350)

    def set_staff(self, staff_list):

        self._staff = list(staff_list)

        self.setRowCount(0)

        for member in self._staff:

            row = self.rowCount()
            self.insertRow(row)

            emp_item = QTableWidgetItem(member.employee_id)
            emp_item.setData(Qt.ItemDataRole.UserRole, member.id)
            self.setItem(row, 0, emp_item)

            self.setItem(
                row, 1,
                QTableWidgetItem(
                    f"{member.first_name} {member.last_name}"
                ),
            )
            self.setItem(row, 2, QTableWidgetItem(member.position))
            self.setItem(row, 3, QTableWidgetItem(member.phone))

            email = ""
            if member.user is not None:
                email = member.user.email

            self.setItem(row, 4, QTableWidgetItem(email))

    def clear_staff(self):
        self._staff = []
        self.setRowCount(0)

    def get_staff_at_row(self, row):
        if row < 0 or row >= len(self._staff):
            return None
        return self._staff[row]

    def get_selected_staff(self):
        return self.get_staff_at_row(self.currentRow())
