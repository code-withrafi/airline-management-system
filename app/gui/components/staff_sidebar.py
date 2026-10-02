from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)


# Unicode escapes so encoding never corrupts the icons:
#   \u2708 = ✈   (airplane)
#   \u25A4 = ▤   (list / operational view)
#   \u21E5 = ⇥   (logout arrow)
ICON_BRAND = "\u2708"
ICON_CHECKIN = "\u25A4"
ICON_LOGOUT = "\u21E5"


class StaffSidebar(QFrame):
    """
    Sidebar for the staff application.

    Same visual idiom as the admin Sidebar, but with
    staff-only navigation items.
    """

    navigation_requested = Signal(str)
    logout_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setObjectName(
            "sidebar"
        )

        self.setFixedWidth(
            240
        )

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

        layout.setSpacing(
            8
        )

        # ====================================================
        # BRAND
        # ====================================================

        brand_icon = QLabel(ICON_BRAND)

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

        layout.addWidget(
            brand_icon
        )

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

        layout.addWidget(
            brand_title
        )

        brand_subtitle = QLabel(
            "STAFF PORTAL"
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

        layout.addWidget(
            brand_subtitle
        )

        # ====================================================
        # NAVIGATION
        # ====================================================

        self.checkin_button = self.create_nav_button(
            f"{ICON_CHECKIN}   Check-In Desk",
            "checkin",
        )

        self.checkin_button.clicked.connect(
            lambda: self.navigation_requested.emit(
                "checkin"
            )
        )

        layout.addWidget(
            self.checkin_button
        )

        layout.addStretch()

        # ====================================================
        # LOGOUT
        # ====================================================

        self.logout_button = QPushButton(
            f"{ICON_LOGOUT}   Logout"
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
