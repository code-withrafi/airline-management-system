from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class RouteTable(QTableWidget):
    """
    Table widget for displaying routes.
    """

    HEADERS = [
        "Origin",
        "Destination",
        "Distance (km)",
        "Duration (min)",
        "Active",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self._routes = []

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
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )

        self.setSortingEnabled(False)
        self.setMinimumHeight(300)

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def set_routes(self, routes) -> None:
        self._routes = list(routes)

        self.clearContents()
        self.setRowCount(len(self._routes))

        for row, route in enumerate(self._routes):
            origin = getattr(route, "origin_airport", None)
            destination = getattr(route, "destination_airport", None)

            origin_text = (
                f"{origin.iata_code} — {origin.city}"
                if origin is not None
                else "—"
            )

            destination_text = (
                f"{destination.iata_code} — {destination.city}"
                if destination is not None
                else "—"
            )

            self.setItem(
                row, 0, QTableWidgetItem(origin_text)
            )
            self.setItem(
                row, 1, QTableWidgetItem(destination_text)
            )

            distance_item = QTableWidgetItem(
                str(route.distance_km)
            )
            distance_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.setItem(row, 2, distance_item)

            duration_item = QTableWidgetItem(
                str(route.estimated_duration_minutes)
            )
            duration_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.setItem(row, 3, duration_item)

            active_item = QTableWidgetItem(
                "Yes" if route.is_active else "No"
            )
            active_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )
            self.setItem(row, 4, active_item)

    def clear_routes(self) -> None:
        self._routes = []
        self.clearContents()
        self.setRowCount(0)

    def route_count(self) -> int:
        return len(self._routes)

    def get_route_at_row(self, row: int):
        if row < 0 or row >= len(self._routes):
            return None
        return self._routes[row]

    def get_selected_route(self):
        return self.get_route_at_row(self.currentRow())