from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)

from app.models import Aircraft


class AircraftTable(QTableWidget):
    HEADERS = [
        "Registration",
        "Manufacturer",
        "Model",
        "Seat Capacity",
        "Status",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self._aircraft: list[Aircraft] = []

        self._configure_table()

    def _configure_table(self) -> None:
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
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )

        self.setSortingEnabled(False)
        self.setMinimumHeight(300)

    def set_aircraft(self, aircraft_list) -> None:
        self._aircraft = list(aircraft_list)

        self.clearContents()
        self.setRowCount(len(self._aircraft))

        for row, aircraft in enumerate(self._aircraft):
            registration_item = QTableWidgetItem(
                aircraft.registration_number
            )
            manufacturer_item = QTableWidgetItem(
                aircraft.manufacturer
            )
            model_item = QTableWidgetItem(
                aircraft.model
            )
            seat_capacity_item = QTableWidgetItem(
                str(aircraft.seat_capacity)
            )
            status_item = QTableWidgetItem(
                aircraft.status.value
            )

            seat_capacity_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            status_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            self.setItem(row, 0, registration_item)
            self.setItem(row, 1, manufacturer_item)
            self.setItem(row, 2, model_item)
            self.setItem(row, 3, seat_capacity_item)
            self.setItem(row, 4, status_item)

    def clear_aircraft(self) -> None:
        self._aircraft.clear()
        self.clearContents()
        self.setRowCount(0)

    def aircraft_count(self) -> int:
        return len(self._aircraft)

    def get_aircraft_at_row(self, row: int):
        if row < 0:
            return None
        if row >= len(self._aircraft):
            return None
        return self._aircraft[row]

    def get_selected_aircraft(self):
        return self.get_aircraft_at_row(self.currentRow())
