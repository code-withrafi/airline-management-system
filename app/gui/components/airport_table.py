from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem


class AirportTable(QTableWidget):
    """
    Reusable table for displaying airport information.
    """

    HEADERS = [
        "IATA",
        "ICAO",
        "Airport Name",
        "City",
        "Country",
        "Timezone",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self._airports = []

        self.setColumnCount(
            len(self.HEADERS)
        )

        self.setHorizontalHeaderLabels(
            self.HEADERS
        )

        self.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.setAlternatingRowColors(False)

        self.setShowGrid(False)

        self.verticalHeader().setVisible(False)

        self.horizontalHeader().setStretchLastSection(
            True
        )

        self.setSortingEnabled(False)

        self._apply_styles()

    def set_airports(self, airports) -> None:
        """
        Replace the table contents with the supplied airports.
        """

        self._airports = list(airports)

        self.setRowCount(0)

        for airport in self._airports:
            row = self.rowCount()

            self.insertRow(row)

            self._set_item(
                row,
                0,
                airport.iata_code,
            )

            self._set_item(
                row,
                1,
                airport.icao_code,
            )

            self._set_item(
                row,
                2,
                airport.name,
            )

            self._set_item(
                row,
                3,
                airport.city,
            )

            self._set_item(
                row,
                4,
                airport.country,
            )

            self._set_item(
                row,
                5,
                airport.timezone,
            )

        self.resizeColumnsToContents()

    def _set_item(
        self,
        row: int,
        column: int,
        value: str,
    ) -> None:
        item = QTableWidgetItem(
            str(value)
        )

        item.setFlags(
            item.flags()
            & ~Qt.ItemFlag.ItemIsEditable
        )

        self.setItem(
            row,
            column,
            item,
        )

    def get_airport_at_row(self, row: int):
        """
        Return the Airport object associated with
        the specified table row.
        """

        if row < 0:
            return None

        if row >= len(self._airports):
            return None

        return self._airports[row]

    def get_selected_airport(self):
        """
        Return the currently selected Airport object.

        Returns None when no row is selected.
        """

        row = self.currentRow()

        return self.get_airport_at_row(row)

    def clear_airports(self) -> None:
        """
        Clear all airport data from the table.
        """

        self._airports = []

        self.setRowCount(0)

    def airport_count(self) -> int:
        """
        Return the number of airports currently displayed.
        """

        return len(self._airports)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                color: #0F172A;
                font-size: 12px;
                gridline-color: transparent;
                selection-background-color: #E2E8F0;
                selection-color: #0F172A;
            }

            QTableWidget::item {
                padding: 8px;
                border: none;
            }

            QTableWidget::item:selected {
                background-color: #E2E8F0;
                color: #0F172A;
            }

            QHeaderView::section {
                background-color: #F8FAFC;
                border: none;
                border-bottom: 1px solid #E2E8F0;
                color: #475569;
                font-size: 11px;
                font-weight: 600;
                padding: 9px 8px;
            }

            QScrollBar:vertical {
                background-color: #F8FAFC;
                width: 10px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background-color: #CBD5E1;
                border-radius: 5px;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )