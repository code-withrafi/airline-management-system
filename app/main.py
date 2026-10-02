# app/main.py
import sys
import webbrowser

from PySide6.QtWidgets import QApplication, QMessageBox

from app.gui.admin import AdminWindow
from app.gui.login import LoginWindow
from app.gui.staff import StaffWindow
from app.models import UserRole
from app.services import application_context


# URL of the React passenger web app
PASSENGER_WEB_APP_URL = "http://localhost:5173"


class ApplicationController:
    """
    Controls transitions between application windows.

    Note
    ----
    Passengers are NOT served by the desktop app anymore.
    When a passenger logs in here, we show a friendly message
    and open the React web app in their default browser.
    """

    def __init__(self):
        self.login_window = None
        self.admin_window = None
        self.staff_window = None

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def start(self):
        self.show_login()

    def show_login(self):
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(
            self.handle_login_success
        )
        self.login_window.show()

    # ------------------------------------------------------------------
    # Login routing
    # ------------------------------------------------------------------

    def handle_login_success(self, result):

        application_context.session.login(result)
        self.login_window.close()

        if result.role == UserRole.ADMIN:
            self.show_admin()

        elif result.role == UserRole.STAFF:
            if self._is_checkin_officer(result.user_id):
                self.show_staff()
            else:
                application_context.session.logout()

                QMessageBox.warning(
                    None,
                    "Login Refused",
                    "This staff account does not have a dashboard.\n\n"
                    "Only check-in officers can log in to the "
                    "staff portal.",
                )
                self.show_login()

        elif result.role == UserRole.PASSENGER:
            # 👇 Redirect passengers to the web app — they are no longer
            #    served by the desktop client.
            self._redirect_passenger_to_web()

        else:
            QMessageBox.warning(
                None,
                "Login Refused",
                f"Authenticated as {result.role.value}.\n\n"
                "This role's interface is not available.",
            )
            self.show_login()

    def _redirect_passenger_to_web(self):
        """Show a friendly message and open the React web app."""
        # Clear the session — passengers don't need a desktop session
        application_context.session.logout()

        QMessageBox.information(
            None,
            "Please use the web app",
            "Passenger accounts are served by the web app.\n\n"
            f"🌐  {PASSENGER_WEB_APP_URL}\n\n"
            "This desktop client is for administrators and staff only.\n\n"
            "Your browser will now open the passenger web app.",
        )

        try:
            webbrowser.open(PASSENGER_WEB_APP_URL)
        except Exception:
            # If the browser can't be opened, the message above already
            # tells the passenger where to go.
            pass

        # Bring the login window back so admins/staff can still log in
        self.show_login()

    # ------------------------------------------------------------------
    # Role helpers
    # ------------------------------------------------------------------

    def _is_checkin_officer(self, user_id):
        """Return True if the user is a check-in officer."""

        from app.config.database import SessionLocal
        from app.services.staff_service import StaffService

        session = SessionLocal()

        try:
            service = StaffService(session)
            return service.is_checkin_officer(user_id)
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Admin / Staff windows
    # ------------------------------------------------------------------

    def show_admin(self):
        self.admin_window = AdminWindow()
        self.admin_window.logout_requested.connect(
            self.handle_logout
        )
        self.admin_window.show()

    def show_staff(self):
        self.staff_window = StaffWindow()
        self.staff_window.logout_requested.connect(
            self.handle_logout
        )
        self.staff_window.show()

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------

    def handle_logout(self):

        if self.admin_window is not None:
            self.admin_window.close()
            self.admin_window = None

        if self.staff_window is not None:
            self.staff_window.close()
            self.staff_window = None

        self.show_login()


def main():

    app = QApplication(sys.argv)

    app.setApplicationName(
        "Airline Management System"
    )

    app.setApplicationDisplayName(
        "Airline Management System"
    )

    controller = ApplicationController()
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()