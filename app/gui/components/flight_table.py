from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
)


class FlightTable(QTableWidget):
    """
    Reusable table for displaying flight information.

    This component only handles presentation. It does not perform
    database queries or business logic.
    """

    COLUMNS = [
        "Flight",
        "Route",
        "Aircraft",
        "Departure",
        "Arrival",
        "Status",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self._flights = []

        self._configure_table()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _configure_table(self) -> None:
        """Configure table appearance and behavior."""

        self.setObjectName("flightTable")

        self.setColumnCount(
            len(self.COLUMNS)
        )

        self.setHorizontalHeaderLabels(
            self.COLUMNS
        )

        self.setAlternatingRowColors(False)

        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )

        self.setShowGrid(False)

        self.verticalHeader().setVisible(False)

        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------

        header = self.horizontalHeader()

        header.setStretchLastSection(True)

        header.setSectionResizeMode(
            0,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeMode.Stretch,
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        header.setSectionResizeMode(
            5,
            QHeaderView.ResizeMode.ResizeToContents,
        )

        # --------------------------------------------------------------
        # Row height
        # --------------------------------------------------------------

        self.verticalHeader().setDefaultSectionSize(
            42
        )

        # --------------------------------------------------------------
        # Font
        # --------------------------------------------------------------

        font = QFont()
        font.setPointSize(10)

        self.setFont(font)

        # --------------------------------------------------------------
        # Stylesheet
        # --------------------------------------------------------------

        self.setStyleSheet(
            """
            QTableWidget#flightTable {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                color: #1E293B;
                gridline-color: transparent;
                outline: none;
            }

            QTableWidget#flightTable::item {
                padding: 8px;
                border-bottom: 1px solid #F1F5F9;
            }

            QTableWidget#flightTable::item:selected {
                background-color: #F1F5F9;
                color: #0F172A;
            }

            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                border: none;
                border-bottom: 1px solid #E5E7EB;
                padding: 10px 8px;
                font-size: 12px;
                font-weight: 600;
            }

            QScrollBar:vertical {
                background: #F8FAFC;
                width: 8px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background: #CBD5E1;
                border-radius: 4px;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def set_flights(self, flights: list) -> None:
        """
        Populate the table using SQLAlchemy Flight objects.

        Related route, airport, and aircraft objects are expected
        to be available through eager loading.
        """

        self._flights = list(flights)

        self.setRowCount(0)

        for flight in self._flights:
            row = self.rowCount()

            self.insertRow(row)

            # ----------------------------------------------------------
            # Flight number
            # ----------------------------------------------------------

            flight_number = self._get_attribute(
                flight,
                "flight_number",
                str(flight.id),
            )

            self._set_item(
                row,
                0,
                str(flight_number),
            )

            # ----------------------------------------------------------
            # Route
            # ----------------------------------------------------------

            route_text = self._get_route_text(
                flight
            )

            self._set_item(
                row,
                1,
                route_text,
            )

            # ----------------------------------------------------------
            # Aircraft
            # ----------------------------------------------------------

            aircraft_text = self._get_aircraft_text(
                flight
            )

            self._set_item(
                row,
                2,
                aircraft_text,
            )

            # ----------------------------------------------------------
            # Departure
            # ----------------------------------------------------------

            departure_text = self._format_datetime(
                getattr(
                    flight,
                    "departure_time",
                    None,
                )
            )

            self._set_item(
                row,
                3,
                departure_text,
            )

            # ----------------------------------------------------------
            # Arrival
            # ----------------------------------------------------------

            arrival_text = self._format_datetime(
                getattr(
                    flight,
                    "arrival_time",
                    None,
                )
            )

            self._set_item(
                row,
                4,
                arrival_text,
            )

            # ----------------------------------------------------------
            # Status
            # ----------------------------------------------------------

            status_text = self._format_status(
                getattr(
                    flight,
                    "status",
                    None,
                )
            )

            status_item = self._set_item(
                row,
                5,
                status_text,
            )

            status_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_attribute(
        obj,
        attribute: str,
        default=None,
    ):
        """Safely retrieve an object attribute."""

        value = getattr(
            obj,
            attribute,
            None,
        )

        if value is None:
            return default

        return value

    @staticmethod
    def _get_route_text(flight) -> str:
        """Build route text from origin and destination airports."""

        route = getattr(
            flight,
            "route",
            None,
        )

        if route is None:
            return "—"

        origin = getattr(
            route,
            "origin_airport",
            None,
        )

        destination = getattr(
            route,
            "destination_airport",
            None,
        )

        origin_code = getattr(
            origin,
            "iata_code",
            None,
        )

        destination_code = getattr(
            destination,
            "iata_code",
            None,
        )

        if origin_code and destination_code:
            return f"{origin_code} → {destination_code}"

        return "—"

    @staticmethod
    def _get_aircraft_text(flight) -> str:
        """Build aircraft display text."""

        aircraft = getattr(
            flight,
            "aircraft",
            None,
        )

        if aircraft is None:
            return "—"

        registration = getattr(
            aircraft,
            "registration_number",
            None,
        )

        if registration:
            return str(registration)

        return str(
            getattr(
                aircraft,
                "id",
                "—",
            )
        )

    @staticmethod
    def _format_datetime(value) -> str:
        """Format a datetime value for dashboard display."""

        if value is None:
            return "—"

        return value.strftime(
            "%d %b %Y, %H:%M"
        )

    @staticmethod
    def _format_status(value) -> str:
        """Convert enum status into readable uppercase text."""

        if value is None:
            return "UNKNOWN"

        status_value = getattr(
            value,
            "value",
            value,
        )

        return str(
            status_value
        ).replace(
            "_",
            " ",
        ).upper()

    def _set_item(
        self,
        row: int,
        column: int,
        text: str,
    ) -> QTableWidgetItem:
        """Create and insert a table item."""

        item = QTableWidgetItem(
            str(text)
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

        return item

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------

    def get_flight_at_row(self, row: int):
        """
        Return the Flight object for the given row, or None.
        """

        if row < 0:
            return None

        if row >= len(self._flights):
            return None

        return self._flights[row]

    def get_selected_flight(self):
        """
        Return the currently selected Flight, or None.
        """

        return self.get_flight_at_row(
            self.currentRow()
        )

    def clear_flights(self) -> None:
        """Remove all flight rows."""

        self._flights = []

        self.setRowCount(0)

    def flight_count(self) -> int:
        """Return the number of displayed flights."""

        return self.rowCount()