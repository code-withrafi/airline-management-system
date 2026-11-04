# app/gui/components/sidebar.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QFrame):
    """
    Reusable sidebar for the Admin application.
    """

    navigation_requested = Signal(str)
    logout_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName("sidebar")

        self.setFixedWidth(240)

        self.setup_ui()

    def setup_ui(self):
        """
        Build the sidebar interface.
        """

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            18,
            22,
            18,
            18,
        )

        layout.setSpacing(8)

        # ====================================================
        # BRAND
        # ====================================================

        brand_icon = QLabel("✈")

        brand_icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        brand_icon.setStyleSheet(
            """
            QLabel {
                font-size: 38px;
                color: #2563eb;
                margin-bottom: 2px;
            }
            """
        )

        layout.addWidget(brand_icon)

        brand_title = QLabel(
            "AIRLINE"
        )

        brand_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        brand_title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: 800;
                color: #111827;
                letter-spacing: 2px;
            }
            """
        )

        layout.addWidget(brand_title)

        brand_subtitle = QLabel(
            "ADMIN PANEL"
        )

        brand_subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        brand_subtitle.setStyleSheet(
            """
            QLabel {
                font-size: 10px;
                font-weight: 600;
                color: #6b7280;
                letter-spacing: 1.5px;
                margin-bottom: 18px;
            }
            """
        )

        layout.addWidget(brand_subtitle)

        # ====================================================
        # NAVIGATION
        # ====================================================

        self.dashboard_button = self.create_nav_button(
            "▣   Dashboard",
            "dashboard",
        )

        self.airports_button = self.create_nav_button(
            "◉   Airports",
            "airports",
        )

        self.aircraft_button = self.create_nav_button(
            "✈   Aircraft",
            "aircraft",
        )

        self.routes_button = self.create_nav_button(
            "↔   Routes",
            "routes",
        )

        self.flights_button = self.create_nav_button(
            "▤   Flights",
            "flights",
        )

        self.schedule_button = self.create_nav_button(
            "🤖   Schedule",
            "schedule",
        )

        self.crew_button = self.create_nav_button(
            "Crew Assignment",
            "crew_assignment",
        )
        self.staff_button = self.create_nav_button(
            "♙   Staff",
            "staff",
        )

        self.bookings_button = self.create_nav_button(
            "▣   Bookings",
            "bookings",
        )

        self.passengers_button = self.create_nav_button(
            "♙   Passengers",
            "passengers",
        )

        self.reports_button = self.create_nav_button(
            "▥   Reports",
            "reports",
        )

        self.dashboard_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "dashboard"
            )
        )

        self.airports_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "airports"
            )
        )

        self.aircraft_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "aircraft"
            )
        )

        self.routes_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "routes"
            )
        )

        self.flights_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "flights"
            )
        )

        self.schedule_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "schedule"
            )
        )

        self.crew_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "crew_assignment"
            )
        )
        self.staff_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "staff"
            )
        )

        self.bookings_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "bookings"
            )
        )

        self.passengers_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "passengers"
            )
        )

        self.reports_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "reports"
            )
        )

        layout.addWidget(
            self.dashboard_button
        )

        layout.addWidget(
            self.airports_button
        )

        layout.addWidget(
            self.aircraft_button
        )

        layout.addWidget(
            self.routes_button
        )

        layout.addWidget(
            self.flights_button
        )

        layout.addWidget(
            self.schedule_button
        )

        layout.addWidget(
            self.crew_button
        )

        layout.addWidget(
            self.staff_button
        )

        layout.addWidget(
            self.bookings_button
        )

        layout.addWidget(
            self.passengers_button
        )

        layout.addWidget(
            self.reports_button
        )

        layout.addStretch()

        # ====================================================
        # LOGOUT
        # ====================================================

        self.logout_button = QPushButton(
            "⇥   Logout"
        )

        self.logout_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.logout_button.setMinimumHeight(
            42
        )

        self.logout_button.setObjectName(
            "logoutButton"
        )

        self.logout_button.clicked.connect(
            self.logout_requested.emit
        )

        layout.addWidget(
            self.logout_button
        )

    def create_nav_button(
        self,
        text: str,
        page_name: str,
    ) -> QPushButton:
        """
        Create a navigation button.
        """

        button = QPushButton(text)

        button.setObjectName(
            "navButton"
        )

        button.setProperty(
            "page_name",
            page_name,
        )

        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        button.setMinimumHeight(
            42
        )

        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        return button