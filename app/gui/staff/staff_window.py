from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.database import SessionLocal
from app.services.application import application_context
from app.gui.components import StaffSidebar
from app.gui.staff.checkin_page import CheckInPage


PAGE_ORDER = (
    "checkin",
)

PAGE_INFORMATION = {
    "checkin": (
        "Check-In Desk",
        "Check passengers in, add baggage, and issue boarding passes.",
    ),
}


class StaffWindow(QWidget):
    """
    Main staff application window.

    Provides a check-in page for staff members.
    """

    logout_requested = Signal()

    def __init__(self):

        super().__init__()

        self.staff_session = None

        self._current_page_key = None

        self.setWindowTitle(
            "Airline Management System - Staff"
        )

        self.setMinimumSize(
            1200,
            750,
        )

        self.resize(
            1400,
            850,
        )

        self._build_ui()

        self._apply_styles()

        self._handle_navigation(
            "checkin"
        )

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        main_layout.setSpacing(
            0
        )

        # ---------------- Sidebar ----------------

        self.sidebar = StaffSidebar()

        self.sidebar.navigation_requested.connect(
            self._handle_navigation
        )

        self.sidebar.logout_requested.connect(
            self._handle_logout
        )

        main_layout.addWidget(
            self.sidebar
        )

        # ---------------- Content container ----------------

        content_container = QWidget()

        content_layout = QVBoxLayout(
            content_container
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        content_layout.setSpacing(
            0
        )

        # ---------------- Header ----------------

        self.header = self._create_header()

        content_layout.addWidget(
            self.header
        )

        # ---------------- Stacked pages ----------------

        self.stack = QStackedWidget()

        content_layout.addWidget(
            self.stack,
            1,
        )

        main_layout.addWidget(
            content_container,
            1,
        )

        self._pages = {}

        self._create_pages()

    def _create_header(self) -> QFrame:

        header = QFrame()

        header.setObjectName(
            "adminHeader"
        )

        header.setFixedHeight(
            76
        )

        header_layout = QHBoxLayout(header)

        header_layout.setContentsMargins(
            28,
            0,
            28,
            0,
        )

        title_container = QWidget()

        title_layout = QVBoxLayout(title_container)

        title_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        title_layout.setSpacing(
            2
        )

        self.page_title = QLabel(
            "Check-In Desk"
        )

        self.page_title.setObjectName(
            "pageTitle"
        )

        self.page_subtitle = QLabel(
            ""
        )

        self.page_subtitle.setObjectName(
            "pageSubtitle"
        )

        title_layout.addWidget(
            self.page_title
        )

        title_layout.addWidget(
            self.page_subtitle
        )

        header_layout.addWidget(
            title_container
        )

        header_layout.addStretch()

        user = application_context.session.current_user

        user_container = QWidget()

        user_layout = QVBoxLayout(user_container)

        user_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        user_layout.setSpacing(
            2
        )

        email_label = QLabel(
            user.email if user else "Staff"
        )

        email_label.setObjectName(
            "userEmail"
        )

        email_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        role_label = QLabel(
            "Staff"
        )

        role_label.setObjectName(
            "userRole"
        )

        role_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        user_layout.addWidget(
            email_label
        )

        user_layout.addWidget(
            role_label
        )

        header_layout.addWidget(
            user_container
        )

        return header

    def _create_pages(self):

        self.checkin_page = CheckInPage(
            session=self._get_session()
        )

        self._pages = {
            "checkin": self.checkin_page,
        }

        for key in PAGE_ORDER:

            self.stack.addWidget(
                self._pages[key]
            )

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------

    def _get_session(self):

        if self.staff_session is None:

            self.staff_session = SessionLocal()

        return self.staff_session

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _handle_navigation(
        self,
        page_key: str,
    ):

        if page_key not in self._pages:

            return

        self._current_page_key = page_key

        self.stack.setCurrentWidget(
            self._pages[page_key]
        )

        title, subtitle = PAGE_INFORMATION.get(
            page_key,
            ("Staff", ""),
        )

        self.page_title.setText(
            title
        )

        self.page_subtitle.setText(
            subtitle
        )

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def _handle_logout(self):

        result = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if result != QMessageBox.StandardButton.Yes:

            return

        application_context.session.logout()

        self.close()

        self.logout_requested.emit()

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------

    def _apply_styles(self):

        self.setStyleSheet(
            """
            QWidget {
                background-color: #F8FAFC;
                color: #0F172A;
                font-family: "Segoe UI";
            }

            QFrame#sidebar {
                background-color: #FFFFFF;
                border-right: 1px solid #E5E7EB;
            }

            QPushButton#navButton {
                background-color: transparent;
                color: #334155;
                text-align: left;
                padding: 8px 14px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#navButton:hover {
                background-color: #F1F5F9;
                color: #0F172A;
            }

            QPushButton#logoutButton {
                background-color: #FEF2F2;
                color: #B91C1C;
                text-align: left;
                padding: 8px 14px;
                border: 1px solid #FECACA;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#logoutButton:hover {
                background-color: #FEE2E2;
            }

            QFrame#adminHeader {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }

            QLabel#pageTitle {
                color: #0F172A;
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#pageSubtitle {
                color: #64748B;
                font-size: 12px;
            }

            QLabel#userEmail {
                color: #0F172A;
                font-size: 13px;
                font-weight: 600;
            }

            QLabel#userRole {
                color: #64748B;
                font-size: 11px;
            }

            QLabel#sectionTitle {
                color: #0F172A;
                font-size: 17px;
                font-weight: 700;
            }

            QLabel#sectionSubtitle {
                color: #64748B;
                font-size: 11px;
            }

            QLabel#statusLabel {
                color: #64748B;
                font-size: 11px;
                padding: 4px;
            }

            QLabel#placeholderTitle {
                color: #0F172A;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#placeholderSubtitle {
                color: #64748B;
                font-size: 13px;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                color: #0F172A;
                padding: 0 14px;
                font-size: 12px;
                min-height: 40px;
            }

            QLineEdit:focus {
                border: 1px solid #94A3B8;
            }

            QComboBox,
            QDateEdit {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                color: #0F172A;
                padding: 0 12px;
                font-size: 12px;
                min-height: 40px;
            }

            QComboBox:focus,
            QDateEdit:focus {
                border: 1px solid #94A3B8;
            }

            QPushButton#refreshButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#refreshButton:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
            }

            QPushButton#primaryButton {
                background-color: #0F172A;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#primaryButton:hover:enabled {
                background-color: #1E293B;
            }

            QPushButton#primaryButton:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
            }

            QPushButton#secondaryButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#secondaryButton:hover:enabled {
                background-color: #F8FAFC;
                border-color: #94A3B8;
            }

            QPushButton#secondaryButton:disabled {
                background-color: #F8FAFC;
                color: #94A3B8;
                border: 1px solid #E2E8F0;
            }

            QPushButton#dangerButton {
                background-color: #FFFFFF;
                color: #B91C1C;
                border: 1px solid #FCA5A5;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#dangerButton:hover:enabled {
                background-color: #FEF2F2;
                border-color: #F87171;
            }

            QPushButton#dangerButton:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border-color: #E2E8F0;
            }

            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                gridline-color: #F1F5F9;
                font-size: 13px;
                color: #0F172A;
            }

            QHeaderView::section {
                background-color: #F8FAFC;
                color: #0F172A;
                border: none;
                border-bottom: 1px solid #E5E7EB;
                padding: 8px 10px;
                font-size: 12px;
                font-weight: 700;
            }

            QTableWidget::item:selected {
                background-color: #E0E7FF;
                color: #1E40AF;
            }

            QTableWidget::item:hover {
                background-color: #F1F5F9;
            }
            """
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def closeEvent(self, event):

        if self.staff_session is not None:

            self.staff_session.close()

            self.staff_session = None

        super().closeEvent(event)
