from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.gui.components.dashboard_card import (
    DashboardCard,
)

from app.services.reports_service import (
    ReportsService,
)
from app.services.exceptions import (
    DatabaseOperationError,
)


class ReportsPage(QWidget):
    """
    Administrator reports page — summary cards + top routes.
    """

    def __init__(self, session, parent=None):

        super().__init__(parent)

        self.session = session

        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(20)

        # ---- header row ----

        header = QHBoxLayout()

        title = QLabel("Reports")
        title.setObjectName("sectionTitle")

        header.addWidget(title)
        header.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button)

        layout.addLayout(header)

        # ---- summary cards ----

        self.cards = {}

        card_row_one = QHBoxLayout()
        card_row_one.setSpacing(14)

        for key, title, icon, subtitle in [
            ("total_revenue", "Total Revenue", "$", "From confirmed bookings"),
            ("total_bookings", "Total Bookings", "\u25a3", "All bookings"),
            ("cancelled_bookings", "Cancelled", "\u00d7", "Cancelled bookings"),
        ]:
            card = DashboardCard(
                title=title, value=0, icon=icon, subtitle=subtitle
            )
            self.cards[key] = card
            card_row_one.addWidget(card)

        layout.addLayout(card_row_one)

        card_row_two = QHBoxLayout()
        card_row_two.setSpacing(14)

        for key, title, icon, subtitle in [
            ("refunded_amount", "Refunded Amount", "\u21ba", "Total refunded"),
            ("total_passengers", "Total Passengers", "\u25cf", "Registered passengers"),
            ("total_flights", "Total Flights", "\u25c8", "All flights"),
        ]:
            card = DashboardCard(
                title=title, value=0, icon=icon, subtitle=subtitle
            )
            self.cards[key] = card
            card_row_two.addWidget(card)

        layout.addLayout(card_row_two)

        # ---- top routes table ----

        section_title = QLabel("Top Routes by Bookings")
        section_title.setObjectName("sectionTitle")
        layout.addWidget(section_title)

        self.routes_table = QTableWidget()
        self.routes_table.setColumnCount(3)
        self.routes_table.setHorizontalHeaderLabels(
            ["Route", "Bookings", "Revenue"]
        )
        self.routes_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.routes_table.verticalHeader().setVisible(False)
        self.routes_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        header_view = self.routes_table.horizontalHeader()
        header_view.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        header_view.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header_view.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )

        self.routes_table.setMinimumHeight(220)
        layout.addWidget(self.routes_table, 1)

        # ---- status ----

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("dashboardStatus")
        layout.addWidget(self.status_label)

        # ---- initial load ----

        self.refresh()

    # ------------------------------------------------------------------

    def refresh(self):

        try:
            service = ReportsService(self.session)
            summary = service.get_summary()

            for key, value in summary.items():
                card = self.cards.get(key)
                if card is not None:
                    if key in ("total_revenue", "refunded_amount"):
                        card.set_value(f"${value}")
                    else:
                        card.set_value(value)

            routes = service.get_top_routes(limit=10)

            self.routes_table.setRowCount(0)

            for entry in routes:
                row = self.routes_table.rowCount()
                self.routes_table.insertRow(row)

                self.routes_table.setItem(
                    row, 0, QTableWidgetItem(entry["route"])
                )
                self.routes_table.setItem(
                    row, 1,
                    QTableWidgetItem(str(entry["bookings"])),
                )
                self.routes_table.setItem(
                    row, 2,
                    QTableWidgetItem(f"${entry['revenue']}"),
                )

            self.status_label.setText(
                f"Report generated. {len(routes)} route(s) ranked."
            )

        except DatabaseOperationError as error:
            self.status_label.setText("Unable to load reports.")
            QMessageBox.critical(
                self, "Reports Error", str(error)
            )
        except Exception as error:
            self.status_label.setText("Unable to load reports.")
            QMessageBox.critical(
                self, "Unexpected Error", str(error)
            )
