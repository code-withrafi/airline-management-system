from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class PassengerTable(QTableWidget):
    """
    Table widget for displaying passengers.
    """

    HEADERS = [
        "Name",
        "Phone",
        "Passport",
        "Email",
        "Date of Birth",
    ]

    def __init__(self, parent=None):

        super().__init__(parent)

        self._passengers = []

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
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )

        self.setMinimumHeight(350)

    def set_passengers(self, passengers):

        self._passengers = list(passengers)

        self.setRowCount(0)

        for passenger in self._passengers:

            row = self.rowCount()
            self.insertRow(row)

            name_item = QTableWidgetItem(
                f"{passenger.first_name} {passenger.last_name}"
            )
            name_item.setData(
                Qt.ItemDataRole.UserRole,
                passenger.id,
            )
            self.setItem(row, 0, name_item)

            self.setItem(
                row, 1, QTableWidgetItem(passenger.phone)
            )
            self.setItem(
                row, 2,
                QTableWidgetItem(passenger.passport_number),
            )

            email = ""
            if passenger.user is not None:
                email = passenger.user.email

            self.setItem(
                row, 3, QTableWidgetItem(email)
            )

            self.setItem(
                row, 4,
                QTableWidgetItem(
                    passenger.date_of_birth.strftime("%Y-%m-%d")
                ),
            )

    def clear_passengers(self):

        self._passengers = []
        self.setRowCount(0)

    def get_passenger_at_row(self, row):

        if row < 0 or row >= len(self._passengers):
            return None

        return self._passengers[row]

    def get_selected_passenger(self):

        return self.get_passenger_at_row(self.currentRow())
