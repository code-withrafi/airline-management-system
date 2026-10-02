from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.config.database import SessionLocal
from app.services import AuthService, AuthenticationError
from app.gui.common.styles import APP_STYLE


class LoginWindow(QMainWindow):
    """
    Main login window for the Airline Management System.
    """

    login_successful = Signal(object)

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Airline Management System - Login"
        )

        self.setMinimumSize(900, 600)

        # ----------------------------------------------------
        # Background image (assets/login.jpg in project root)
        # ----------------------------------------------------
        background_path = (
            Path(__file__)
            .resolve()
            .parents[3]
            / "assets"
            / "login.jpg"
        )

        background_url = background_path.as_posix()

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-image: url("{background_url}");
                background-position: center;
                background-repeat: no-repeat;
            }}
            """
            + APP_STYLE
        )

        self.setup_ui()

    def setup_ui(self):
        """
        Build the login interface.
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            60,
            40,
            60,
            40,
        )

        main_layout.setSpacing(50)

        # ====================================================
        # LEFT SIDE
        # ====================================================

        left_container = QWidget()

        left_layout = QVBoxLayout(
            left_container
        )

        left_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        left_layout.setSpacing(12)

        brand_label = QLabel(
            "✈"
        )

        brand_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        brand_label.setStyleSheet(
            """
            QLabel {
                font-size: 54px;
                color: #2563eb;
            }
            """
        )

        left_layout.addWidget(
            brand_label
        )

        company_label = QLabel(
            "AIRLINE"
        )

        company_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        company_label.setStyleSheet(
            """
            QLabel {
                font-size: 32px;
                font-weight: 800;
                color: #111827;
                letter-spacing: 3px;
            }
            """
        )

        left_layout.addWidget(
            company_label
        )

        management_label = QLabel(
            "MANAGEMENT SYSTEM"
        )

        management_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        management_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #6b7280;
                letter-spacing: 2px;
            }
            """
        )

        left_layout.addWidget(
            management_label
        )

        description_label = QLabel(
            "Manage flights, passengers, staff\n"
            "and airline operations from one place."
        )

        description_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        description_label.setStyleSheet(
            """
            QLabel {
                margin-top: 15px;
                font-size: 14px;
                color: #6b7280;
                line-height: 1.5;
            }
            """
        )

        left_layout.addWidget(
            description_label
        )

        main_layout.addWidget(
            left_container,
            1,
        )

        # ====================================================
        # RIGHT SIDE - LOGIN CARD
        # ====================================================

        card = QFrame()

        card.setObjectName(
            "loginCard"
        )

        card.setMaximumWidth(
            420
        )

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        card_layout = QVBoxLayout(
            card
        )

        card_layout.setContentsMargins(
            35,
            35,
            35,
            35,
        )

        card_layout.setSpacing(
            14
        )

        welcome_label = QLabel(
            "Welcome back"
        )

        welcome_label.setObjectName(
            "titleLabel"
        )

        card_layout.addWidget(
            welcome_label
        )

        subtitle_label = QLabel(
            "Sign in to continue to your account."
        )

        subtitle_label.setObjectName(
            "subtitleLabel"
        )

        card_layout.addWidget(
            subtitle_label
        )

        card_layout.addSpacing(
            15
        )

        # ====================================================
        # EMAIL
        # ====================================================

        email_label = QLabel(
            "Email address"
        )

        email_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            email_label
        )

        self.email_input = QLineEdit()

        self.email_input.setPlaceholderText(
            "Enter your email"
        )

        self.email_input.setClearButtonEnabled(
            True
        )

        card_layout.addWidget(
            self.email_input
        )

        # ====================================================
        # PASSWORD
        # ====================================================

        password_label = QLabel(
            "Password"
        )

        password_label.setObjectName(
            "fieldLabel"
        )

        card_layout.addWidget(
            password_label
        )

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText(
            "Enter your password"
        )

        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        card_layout.addWidget(
            self.password_input
        )

        # ====================================================
        # ERROR LABEL
        # ====================================================

        self.error_label = QLabel()

        self.error_label.setObjectName(
            "errorLabel"
        )

        self.error_label.setWordWrap(
            True
        )

        self.error_label.hide()

        card_layout.addWidget(
            self.error_label
        )

        # ====================================================
        # LOGIN BUTTON
        # ====================================================

        self.login_button = QPushButton(
            "Sign In"
        )

        self.login_button.setObjectName(
            "loginButton"
        )

        self.login_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.login_button.clicked.connect(
            self.handle_login
        )

        card_layout.addWidget(
            self.login_button
        )

        card_layout.addStretch()

        # ====================================================
        # FOOTER
        # ====================================================

        footer_label = QLabel(
            "Airline Management System"
        )

        footer_label.setObjectName(
            "footerLabel"
        )

        footer_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        card_layout.addWidget(
            footer_label
        )

        main_layout.addWidget(
            card,
            1,
        )

        # Enter key support
        self.password_input.returnPressed.connect(
            self.handle_login
        )

        self.email_input.returnPressed.connect(
            self.handle_login
        )

        self.email_input.setFocus()

    def handle_login(self):
        """
        Authenticate the user.
        """

        email = self.email_input.text().strip()
        password = self.password_input.text()

        self.error_label.hide()

        if not email:
            self.show_error(
                "Please enter your email address."
            )

            self.email_input.setFocus()

            return

        if not password:
            self.show_error(
                "Please enter your password."
            )

            self.password_input.setFocus()

            return

        self.set_login_enabled(
            False
        )

        session = SessionLocal()

        try:

            auth_service = AuthService(
                session
            )

            result = auth_service.authenticate(
                email,
                password,
            )

            self.login_successful.emit(
                result
            )

        except AuthenticationError as error:

            self.show_error(
                str(error)
            )

            self.password_input.clear()
            self.password_input.setFocus()

        except Exception as error:

            print(
                "Login error:",
                error,
            )

            self.show_error(
                "An unexpected error occurred. "
                "Please try again."
            )

        finally:

            session.close()

            self.set_login_enabled(
                True
            )

    def show_error(self, message: str):
        """
        Display an authentication error.
        """

        self.error_label.setText(
            message
        )

        self.error_label.show()

    def set_login_enabled(self, enabled: bool):
        """
        Enable or disable login controls.
        """

        self.login_button.setEnabled(
            enabled
        )

        self.email_input.setEnabled(
            enabled
        )

        self.password_input.setEnabled(
            enabled
        )
