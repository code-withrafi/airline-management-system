# app/gui/admin/admin_window.py
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config.database import SessionLocal
from app.gui.components import (
    AirportFormDialog,
    AircraftFormDialog,
    AirportTable,
    AircraftTable,
    DashboardCard,
    FlightTable,
    RouteFormDialog,
    RouteTable,
    PassengerFormDialog,
    PassengerTable,
    StaffFormDialog,
    StaffTable,
    SeatTable,
    Sidebar,
)
from app.gui.admin.flight_management import (
    FlightManagementPage,
)
from app.gui.admin.schedule_generator import (
    ScheduleGeneratorPage,
)
from app.gui.admin.crew_assignment_page import (
    CrewAssignmentPage,
)
from app.gui.admin.booking_management import (
    AdminBookingManagementPage,
)
from app.gui.admin.reports_page import (
    ReportsPage,
)
from app.models import AircraftStatus, UserRole
from app.services import DashboardService, application_context
from app.services.aircraft_service import AircraftService
from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class AdminWindow(QWidget):
    """Main administrator application window."""

    logout_requested = Signal()

    def __init__(self):
        super().__init__()

        application_context.session.require_role(
            UserRole.ADMIN
        )

        self.dashboard_session = None
        self.dashboard_service = None

        self.aircraft_session = None
        self.flight_session = None

        self.dashboard_cards = {}

        self.setWindowTitle(
            "Airline Management System - Admin"
        )

        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        self._build_ui()
        self._apply_styles()

        self._show_dashboard()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()

        self.sidebar.navigation_requested.connect(
            self._handle_navigation
        )
        self.sidebar.logout_requested.connect(
            self._handle_logout
        )

        main_layout.addWidget(self.sidebar)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.header = self._create_header()
        content_layout.addWidget(self.header)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)

        main_layout.addWidget(content_container, 1)

        self.pages = {}
        self._create_pages()

    def _create_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("adminHeader")
        header.setFixedHeight(76)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(28, 0, 28, 0)

        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)

        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("pageTitle")

        self.page_subtitle = QLabel(
            "Overview of your airline operations"
        )
        self.page_subtitle.setObjectName("pageSubtitle")

        title_layout.addWidget(self.page_title)
        title_layout.addWidget(self.page_subtitle)

        layout.addWidget(title_container)
        layout.addStretch()

        user = application_context.session.current_user

        user_container = QWidget()
        user_layout = QVBoxLayout(user_container)
        user_layout.setContentsMargins(0, 0, 0, 0)
        user_layout.setSpacing(2)

        self.user_email = QLabel(
            user.email if user else "Administrator"
        )
        self.user_email.setObjectName("userEmail")

        self.user_role = QLabel("Administrator")
        self.user_role.setObjectName("userRole")

        self.user_email.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.user_role.setAlignment(Qt.AlignmentFlag.AlignRight)

        user_layout.addWidget(self.user_email)
        user_layout.addWidget(self.user_role)

        layout.addWidget(user_container)

        return header

    def _create_pages(self) -> None:
        dashboard_page = self._create_dashboard_page()
        self.pages["dashboard"] = dashboard_page
        self.stack.addWidget(dashboard_page)

        airport_page = self._create_airport_page()
        self.pages["airports"] = airport_page
        self.stack.addWidget(airport_page)

        aircraft_page = self._build_aircraft_page()
        self.pages["aircraft"] = aircraft_page
        self.stack.addWidget(aircraft_page)

        flight_page = FlightManagementPage(
            self._get_flight_session()
        )
        self.pages["flights"] = flight_page
        self.stack.addWidget(flight_page)

        schedule_page = ScheduleGeneratorPage(
            self._get_flight_session()
        )
        schedule_page.generation_completed.connect(
            self._on_schedule_generated
        )
        self.pages["schedule"] = schedule_page
        self.stack.addWidget(schedule_page)

        crew_page = CrewAssignmentPage(
            self._get_flight_session()
        )
        self.pages["crew_assignment"] = crew_page
        self.stack.addWidget(crew_page)

        route_page = self._create_route_page()
        self.pages["routes"] = route_page
        self.stack.addWidget(route_page)

        bookings_page = AdminBookingManagementPage(
            session=self._get_flight_session(),
        )
        self.pages["bookings"] = bookings_page
        self.stack.addWidget(bookings_page)

        passenger_page = self._create_passenger_page()
        self.pages["passengers"] = passenger_page
        self.stack.addWidget(passenger_page)

        staff_page = self._create_staff_page()
        self.pages["staff"] = staff_page
        self.stack.addWidget(staff_page)

        reports_page = ReportsPage(
            session=self._get_flight_session(),
        )
        self.pages["reports"] = reports_page
        self.stack.addWidget(reports_page)

    # ==================================================================
    # Dashboard
    # ==================================================================

    def _create_dashboard_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(28, 24, 28, 28)
        page_layout.setSpacing(20)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        dashboard_content = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_content)
        dashboard_layout.setContentsMargins(0, 0, 0, 0)
        dashboard_layout.setSpacing(22)

        cards_container = QWidget()
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(14)

        row_one = QHBoxLayout()
        row_one.setSpacing(14)

        self.dashboard_cards["total_airports"] = DashboardCard(
            title="Total Airports", value=0, icon="✈",
            subtitle="Registered airports",
        )
        self.dashboard_cards["total_aircraft"] = DashboardCard(
            title="Total Aircraft", value=0, icon="◆",
            subtitle="Registered aircraft",
        )
        self.dashboard_cards["total_routes"] = DashboardCard(
            title="Total Routes", value=0, icon="↔",
            subtitle="Available routes",
        )
        self.dashboard_cards["total_flights"] = DashboardCard(
            title="Total Flights", value=0, icon="◈",
            subtitle="All flights",
        )

        for k in ["total_airports", "total_aircraft", "total_routes", "total_flights"]:
            row_one.addWidget(self.dashboard_cards[k])

        cards_layout.addLayout(row_one)

        row_two = QHBoxLayout()
        row_two.setSpacing(14)

        self.dashboard_cards["scheduled_flights"] = DashboardCard(
            title="Scheduled Flights", value=0, icon="✓",
            subtitle="Currently scheduled",
        )
        self.dashboard_cards["cancelled_flights"] = DashboardCard(
            title="Cancelled Flights", value=0, icon="×",
            subtitle="Cancelled flights",
        )
        self.dashboard_cards["total_bookings"] = DashboardCard(
            title="Total Bookings", value=0, icon="▣",
            subtitle="All bookings",
        )
        self.dashboard_cards["total_passengers"] = DashboardCard(
            title="Total Passengers", value=0, icon="●",
            subtitle="Registered passengers",
        )

        for k in ["scheduled_flights", "cancelled_flights", "total_bookings", "total_passengers"]:
            row_two.addWidget(self.dashboard_cards[k])

        cards_layout.addLayout(row_two)
        dashboard_layout.addWidget(cards_container)

        flight_header = QHBoxLayout()
        flight_title_container = QWidget()
        flight_title_layout = QVBoxLayout(flight_title_container)
        flight_title_layout.setContentsMargins(0, 0, 0, 0)
        flight_title_layout.setSpacing(2)

        flight_title = QLabel("Recent / Upcoming Flights")
        flight_title.setObjectName("sectionTitle")
        flight_subtitle = QLabel("Latest flight activity from the database")
        flight_subtitle.setObjectName("sectionSubtitle")

        flight_title_layout.addWidget(flight_title)
        flight_title_layout.addWidget(flight_subtitle)

        flight_header.addWidget(flight_title_container)
        flight_header.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("refreshButton")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.clicked.connect(self._refresh_dashboard)

        flight_header.addWidget(self.refresh_button)
        dashboard_layout.addLayout(flight_header)

        self.flight_table = FlightTable()
        self.flight_table.setMinimumHeight(280)
        self.flight_table.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        dashboard_layout.addWidget(self.flight_table, 1)

        self.dashboard_status = QLabel()
        self.dashboard_status.setObjectName("dashboardStatus")
        self.dashboard_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dashboard_layout.addWidget(self.dashboard_status)

        scroll_area.setWidget(dashboard_content)
        page_layout.addWidget(scroll_area)

        return page

    # ==================================================================
    # Airport management
    # ==================================================================

    def _create_airport_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(28, 24, 28, 28)
        page_layout.setSpacing(18)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(4)

        self.airport_search = QLineEdit()
        self.airport_search.setObjectName("airportSearch")
        self.airport_search.setPlaceholderText(
            "Search by IATA, ICAO, name, city, or country..."
        )
        self.airport_search.setMinimumHeight(40)
        self.airport_search.textChanged.connect(self._search_airports)

        search_layout.addWidget(self.airport_search)
        toolbar.addWidget(search_container, 1)

        self.airport_refresh_button = QPushButton("Refresh")
        self.airport_refresh_button.setObjectName("airportRefreshButton")
        self.airport_refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.airport_refresh_button.clicked.connect(self._refresh_airports)
        toolbar.addWidget(self.airport_refresh_button)

        self.add_airport_button = QPushButton("+ Add Airport")
        self.add_airport_button.setObjectName("addAirportButton")
        self.add_airport_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar.addWidget(self.add_airport_button)

        self.edit_airport_button = QPushButton("Edit Airport")
        self.edit_airport_button.setObjectName("editAirportButton")
        self.edit_airport_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_airport_button.setEnabled(False)
        toolbar.addWidget(self.edit_airport_button)

        self.delete_airport_button = QPushButton("Delete Airport")
        self.delete_airport_button.setObjectName("airportDeleteButton")
        self.delete_airport_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_airport_button.setEnabled(False)
        toolbar.addWidget(self.delete_airport_button)

        self.add_airport_button.clicked.connect(self._open_add_airport_dialog)
        self.edit_airport_button.clicked.connect(self._open_edit_airport_dialog)
        self.delete_airport_button.clicked.connect(self._delete_selected_airport)

        page_layout.addLayout(toolbar)

        self.airport_table = AirportTable()
        self.airport_table.setMinimumHeight(350)
        self.airport_table.itemSelectionChanged.connect(
            self._handle_airport_selection_changed
        )
        page_layout.addWidget(self.airport_table, 1)

        self.airport_status = QLabel()
        self.airport_status.setObjectName("airportStatus")
        self.airport_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_layout.addWidget(self.airport_status)

        return page

    def _create_airport_service(self):
        if not hasattr(self, "airport_session"):
            self.airport_session = SessionLocal()

        if not hasattr(self, "airport_service"):
            from app.services import AirportService
            self.airport_service = AirportService(self.airport_session)

        return self.airport_service

    def _refresh_airports(self) -> None:
        try:
            service = self._create_airport_service()
            airports = service.get_all_airports()
            self.airport_table.set_airports(airports)
            self.airport_status.setText(
                f"Showing {len(airports)} airport(s)."
            )
            self._handle_airport_selection_changed()
        except Exception as error:
            self.airport_status.setText("Unable to load airports.")
            QMessageBox.critical(
                self, "Airport Error",
                f"An error occurred while loading airports:\n\n{error}",
            )

    def _search_airports(self, search_text: str) -> None:
        try:
            service = self._create_airport_service()
            airports = service.search_airports(search_text)
            self.airport_table.set_airports(airports)
            if search_text.strip():
                self.airport_status.setText(
                    f"Found {len(airports)} airport(s)."
                )
            else:
                self.airport_status.setText(
                    f"Showing {len(airports)} airport(s)."
                )
            self._handle_airport_selection_changed()
        except Exception as error:
            self.airport_status.setText("Unable to search airports.")
            QMessageBox.critical(
                self, "Airport Search Error",
                f"An error occurred while searching airports:\n\n{error}",
            )

    def _handle_airport_selection_changed(self) -> None:
        has_selection = self.airport_table.currentRow() >= 0
        self.edit_airport_button.setEnabled(has_selection)
        self.delete_airport_button.setEnabled(has_selection)

    def _get_selected_airport(self):
        return self.airport_table.get_selected_airport()

    def _open_add_airport_dialog(self) -> None:
        dialog = AirportFormDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._create_airport(dialog.get_data())

    def _open_edit_airport_dialog(self) -> None:
        airport = self._get_selected_airport()
        if airport is None:
            QMessageBox.information(
                self, "No Airport Selected",
                "Please select an airport to edit.",
            )
            return

        dialog = AirportFormDialog(parent=self, airport=airport)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self._update_airport(airport.id, dialog.get_data())

    def _delete_selected_airport(self) -> None:
        airport = self._get_selected_airport()
        if airport is None:
            QMessageBox.warning(
                self, "No Airport Selected",
                "Please select an airport to delete.",
            )
            return

        confirmation = QMessageBox.question(
            self, "Delete Airport",
            (
                "Are you sure you want to delete this airport?\n\n"
                f"IATA: {airport.iata_code}\n"
                f"ICAO: {airport.icao_code}\n"
                f"Name: {airport.name}\n"
                f"City: {airport.city}\n\n"
                "This action cannot be undone."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        self._delete_airport(airport.id, airport.iata_code)

    def _create_airport(self, data: dict[str, str]) -> None:
        from app.services.exceptions import (
            DatabaseOperationError as DbOpError,
            ResourceConflictError as RCE,
            ValidationError as VE,
        )
        try:
            service = self._create_airport_service()
            service.create_airport(**data)
            self._refresh_airports()
            QMessageBox.information(
                self, "Airport Created",
                f"Airport '{data['iata_code']}' was created successfully.",
            )
        except (VE, RCE) as error:
            QMessageBox.warning(self, "Unable to Create Airport", str(error))
        except DbOpError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while creating the airport:\n\n{error}",
            )

    def _update_airport(self, airport_id: int, data: dict[str, str]) -> None:
        from app.services.exceptions import (
            DatabaseOperationError as DbOpError,
            ResourceConflictError as RCE,
            ValidationError as VE,
        )
        try:
            service = self._create_airport_service()
            service.update_airport(airport_id, **data)
            self._refresh_airports()
            QMessageBox.information(
                self, "Airport Updated",
                f"Airport '{data['iata_code']}' was updated successfully.",
            )
        except (VE, RCE) as error:
            QMessageBox.warning(self, "Unable to Update Airport", str(error))
        except DbOpError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while updating the airport:\n\n{error}",
            )

    def _delete_airport(self, airport_id: int, iata_code: str) -> None:
        from app.services.exceptions import (
            DatabaseOperationError as DbOpError,
            ResourceConflictError as RCE,
            ResourceNotFoundError as RNFE,
            ValidationError as VE,
        )
        try:
            service = self._create_airport_service()
            service.delete_airport(airport_id)
            self._refresh_airports()
            QMessageBox.information(
                self, "Airport Deleted",
                f"Airport '{iata_code}' was deleted successfully.",
            )
        except (VE, RCE, RNFE) as error:
            QMessageBox.warning(self, "Unable to Delete Airport", str(error))
            self._refresh_airports()
        except DbOpError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while deleting the airport:\n\n{error}",
            )

    # ==================================================================
    # Aircraft management
    # ==================================================================

    def _build_aircraft_page(self) -> QWidget:
        """Create the administrator aircraft management interface."""

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(4)

        self.aircraft_search_input = QLineEdit()
        self.aircraft_search_input.setObjectName("aircraftSearch")
        self.aircraft_search_input.setPlaceholderText(
            "Search by registration, manufacturer, or model..."
        )
        self.aircraft_search_input.setClearButtonEnabled(True)
        self.aircraft_search_input.setMinimumHeight(40)
        self.aircraft_search_input.textChanged.connect(self._search_aircraft)

        search_layout.addWidget(self.aircraft_search_input)
        toolbar.addWidget(search_container, 1)

        self.aircraft_refresh_button = QPushButton("Refresh")
        self.aircraft_refresh_button.setObjectName("aircraftRefreshButton")
        self.aircraft_refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.aircraft_refresh_button.clicked.connect(self._refresh_aircraft)
        toolbar.addWidget(self.aircraft_refresh_button)

        self.aircraft_add_button = QPushButton("+ Add Aircraft")
        self.aircraft_add_button.setObjectName("addAircraftButton")
        self.aircraft_add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar.addWidget(self.aircraft_add_button)

        self.aircraft_edit_button = QPushButton("Edit Aircraft")
        self.aircraft_edit_button.setObjectName("editAircraftButton")
        self.aircraft_edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.aircraft_edit_button.setEnabled(False)
        toolbar.addWidget(self.aircraft_edit_button)

        self.aircraft_delete_button = QPushButton("Delete Aircraft")
        self.aircraft_delete_button.setObjectName("aircraftDeleteButton")
        self.aircraft_delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.aircraft_delete_button.setEnabled(False)
        toolbar.addWidget(self.aircraft_delete_button)

        self.view_seats_button = QPushButton("View Seats")
        self.view_seats_button.setObjectName("aircraftViewSeatsButton")
        self.view_seats_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_seats_button.setEnabled(False)
        toolbar.addWidget(self.view_seats_button)

        self.aircraft_activate_button = QPushButton("Set Active")
        self.aircraft_activate_button.setObjectName("aircraftActivateButton")
        self.aircraft_activate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.aircraft_activate_button.setEnabled(False)
        toolbar.addWidget(self.aircraft_activate_button)

        self.aircraft_maintenance_button = QPushButton("Set Maintenance")
        self.aircraft_maintenance_button.setObjectName("aircraftMaintenanceButton")
        self.aircraft_maintenance_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.aircraft_maintenance_button.setEnabled(False)
        toolbar.addWidget(self.aircraft_maintenance_button)

        self.aircraft_inactive_button = QPushButton("Set Inactive")
        self.aircraft_inactive_button.setObjectName("aircraftInactiveButton")
        self.aircraft_inactive_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.aircraft_inactive_button.setEnabled(False)
        toolbar.addWidget(self.aircraft_inactive_button)

        self.aircraft_add_button.clicked.connect(self._open_add_aircraft_dialog)
        self.aircraft_edit_button.clicked.connect(self._open_edit_aircraft_dialog)
        self.aircraft_delete_button.clicked.connect(self._delete_aircraft)
        self.view_seats_button.clicked.connect(self._open_seat_view)

        self.aircraft_activate_button.clicked.connect(
            lambda: self._change_aircraft_status(AircraftStatus.ACTIVE)
        )
        self.aircraft_maintenance_button.clicked.connect(
            lambda: self._change_aircraft_status(AircraftStatus.MAINTENANCE)
        )
        self.aircraft_inactive_button.clicked.connect(
            lambda: self._change_aircraft_status(AircraftStatus.INACTIVE)
        )

        layout.addLayout(toolbar)

        self.aircraft_table = AircraftTable()
        self.aircraft_table.setMinimumHeight(350)
        self.aircraft_table.itemSelectionChanged.connect(
            self._on_aircraft_selection_changed
        )
        layout.addWidget(self.aircraft_table, 1)

        self.aircraft_status_label = QLabel()
        self.aircraft_status_label.setObjectName("aircraftStatus")
        self.aircraft_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.aircraft_status_label)

        return page

    def _get_aircraft_session(self):
        if self.aircraft_session is None:
            self.aircraft_session = SessionLocal()
        return self.aircraft_session

    def _get_aircraft_service(self) -> AircraftService:
        return AircraftService(self._get_aircraft_session())

    def _get_flight_session(self):
        if not hasattr(self, "flight_session") or self.flight_session is None:
            self.flight_session = SessionLocal()
        return self.flight_session

    def _refresh_aircraft(self) -> None:
        try:
            service = self._get_aircraft_service()
            search_text = self.aircraft_search_input.text().strip()

            if search_text:
                aircraft = service.search_aircraft(search_text)
            else:
                aircraft = service.get_all_aircraft()

            self.aircraft_table.set_aircraft(aircraft)
            self._set_aircraft_status(len(aircraft), search_text)
            self._reset_aircraft_selection()

        except DatabaseOperationError as error:
            self.aircraft_table.clear_aircraft()
            self.aircraft_status_label.setText("Unable to load aircraft.")
            QMessageBox.critical(self, "Aircraft Error", str(error))
        except Exception as error:
            self.aircraft_table.clear_aircraft()
            self.aircraft_status_label.setText("Unable to load aircraft.")
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while loading aircraft:\n\n{error}",
            )

    def _search_aircraft(self, search_text: str) -> None:
        self._refresh_aircraft()

    def _refresh_flights(self) -> None:
        """Refresh the flights page."""

        page = self.pages.get("flights")

        if page is None:
            return

        if hasattr(page, "refresh_table"):
            page.refresh_table()

    def _on_schedule_generated(self) -> None:
        """Called after the schedule generator finishes. Refresh dependent pages."""
        self._refresh_flights()
        self._refresh_dashboard()

    def _set_aircraft_status(self, count: int, search_text: str) -> None:
        normalized = search_text.strip()

        if normalized:
            if count == 0:
                self.aircraft_status_label.setText(
                    f"No aircraft found for '{normalized}'."
                )
            elif count == 1:
                self.aircraft_status_label.setText(
                    f"1 aircraft found for '{normalized}'."
                )
            else:
                self.aircraft_status_label.setText(
                    f"{count} aircraft found for '{normalized}'."
                )
        else:
            if count == 0:
                self.aircraft_status_label.setText("No aircraft available.")
            elif count == 1:
                self.aircraft_status_label.setText("1 aircraft")
            else:
                self.aircraft_status_label.setText(f"{count} aircraft")

    def _on_aircraft_selection_changed(self) -> None:
        aircraft = self.aircraft_table.get_selected_aircraft()
        has_selection = aircraft is not None

        self.aircraft_edit_button.setEnabled(has_selection)
        self.aircraft_delete_button.setEnabled(has_selection)
        self.aircraft_activate_button.setEnabled(has_selection)
        self.aircraft_maintenance_button.setEnabled(has_selection)
        self.aircraft_inactive_button.setEnabled(has_selection)
        self.view_seats_button.setEnabled(has_selection)

    def _reset_aircraft_selection(self) -> None:
        self.aircraft_table.clearSelection()

        self.aircraft_edit_button.setEnabled(False)
        self.aircraft_delete_button.setEnabled(False)
        self.aircraft_activate_button.setEnabled(False)
        self.aircraft_maintenance_button.setEnabled(False)
        self.aircraft_inactive_button.setEnabled(False)
        self.view_seats_button.setEnabled(False)

    def _open_add_aircraft_dialog(self) -> None:
        dialog = AircraftFormDialog(parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            service = self._get_aircraft_service()
            service.create_aircraft(**data)
            self._refresh_aircraft()
            QMessageBox.information(
                self, "Aircraft Created",
                "Aircraft created successfully.",
            )
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Duplicate Aircraft", str(error))
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while creating the aircraft:\n\n{error}",
            )

    def _open_edit_aircraft_dialog(self) -> None:
        aircraft = self.aircraft_table.get_selected_aircraft()
        if aircraft is None:
            QMessageBox.warning(
                self, "No Selection",
                "Please select an aircraft first.",
            )
            return

        dialog = AircraftFormDialog(parent=self, aircraft=aircraft)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            service = self._get_aircraft_service()
            service.update_aircraft(aircraft.id, **data)
            self._refresh_aircraft()
            QMessageBox.information(
                self, "Aircraft Updated",
                "Aircraft updated successfully.",
            )
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Duplicate Aircraft", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Aircraft Not Found", str(error))
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while updating the aircraft:\n\n{error}",
            )

    def _change_aircraft_status(self, status) -> None:
        """Change the status of the selected aircraft."""

        aircraft = self.aircraft_table.get_selected_aircraft()

        if aircraft is None:
            QMessageBox.warning(
                self, "No Selection",
                "Please select an aircraft first.",
            )
            return

        confirmation = QMessageBox.question(
            self, "Confirm Status Change",
            (
                f"Change {aircraft.registration_number} "
                f"status to {status.value}?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = self._get_aircraft_service()
            service.update_aircraft_status(aircraft.id, status)
            self._refresh_aircraft()
            QMessageBox.information(
                self, "Aircraft Status Updated",
                "Aircraft status updated successfully.",
            )
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Aircraft Not Found", str(error))
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while updating status:\n\n{error}",
            )

    def _open_seat_view(self) -> None:
        """Open a read-only dialog showing the seats of the selected aircraft."""

        aircraft = self.aircraft_table.get_selected_aircraft()

        if aircraft is None:
            QMessageBox.warning(
                self, "No Selection",
                "Please select an aircraft first.",
            )
            return

        try:
            from app.repositories import SeatRepository

            session = self._get_aircraft_session()
            repo = SeatRepository(session)
            seats = repo.get_layout(aircraft.id)

        except Exception as error:
            QMessageBox.critical(
                self, "Seat Load Error",
                f"Unable to load seats:\n\n{error}",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(
            f"Seats — {aircraft.registration_number}"
        )
        dialog.setMinimumSize(700, 500)

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(20, 20, 20, 20)
        dialog_layout.setSpacing(12)

        header = QLabel(
            f"{aircraft.registration_number} — "
            f"{aircraft.manufacturer} {aircraft.model} "
            f"({len(seats)} seats)"
        )
        header.setObjectName("sectionTitle")
        dialog_layout.addWidget(header)

        table = SeatTable()
        table.load_seats(seats)
        dialog_layout.addWidget(table, 1)

        close_button = QPushButton("Close")
        close_button.setObjectName("refreshButton")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(dialog.accept)
        dialog_layout.addWidget(
            close_button,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

        dialog.exec()

    def _delete_aircraft(self) -> None:
        """Delete the selected aircraft after confirmation."""

        aircraft = self.aircraft_table.get_selected_aircraft()

        if aircraft is None:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select an aircraft first.",
            )
            return

        confirmation = QMessageBox.question(
            self,
            "Confirm Delete",
            (
                f"Delete aircraft {aircraft.registration_number}?\n\n"
                "This action cannot be undone."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = self._get_aircraft_service()

            service.delete_aircraft(aircraft.id)

            self._refresh_aircraft()

            QMessageBox.information(
                self,
                "Aircraft Deleted",
                "Aircraft deleted successfully.",
            )

        except ResourceConflictError as error:
            QMessageBox.warning(
                self,
                "Cannot Delete Aircraft",
                str(error),
            )

        except ResourceNotFoundError as error:
            QMessageBox.warning(
                self,
                "Aircraft Not Found",
                str(error),
            )

        except DatabaseOperationError as error:
            QMessageBox.critical(
                self,
                "Database Error",
                str(error),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Unexpected Error",
                (
                    "An unexpected error occurred while "
                    f"deleting the aircraft:\n\n{error}"
                ),
            )

    # ==================================================================
    # Passenger management
    # ==================================================================

    def _create_passenger_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.passenger_search_input = QLineEdit()
        self.passenger_search_input.setPlaceholderText(
            "Search by name, phone, or passport..."
        )
        self.passenger_search_input.setMinimumHeight(40)
        self.passenger_search_input.textChanged.connect(
            self._search_passengers
        )
        toolbar.addWidget(self.passenger_search_input, 1)

        self.passenger_refresh_button = QPushButton("Refresh")
        self.passenger_refresh_button.clicked.connect(
            self._refresh_passengers
        )
        toolbar.addWidget(self.passenger_refresh_button)

        self.add_passenger_button = QPushButton("+ Add Passenger")
        self.add_passenger_button.clicked.connect(
            self._open_add_passenger_dialog
        )
        toolbar.addWidget(self.add_passenger_button)

        self.edit_passenger_button = QPushButton("Edit Passenger")
        self.edit_passenger_button.setEnabled(False)
        self.edit_passenger_button.clicked.connect(
            self._open_edit_passenger_dialog
        )
        toolbar.addWidget(self.edit_passenger_button)

        self.delete_passenger_button = QPushButton("Delete Passenger")
        self.delete_passenger_button.setEnabled(False)
        self.delete_passenger_button.clicked.connect(
            self._delete_selected_passenger
        )
        toolbar.addWidget(self.delete_passenger_button)

        layout.addLayout(toolbar)

        self.passenger_table = PassengerTable()
        self.passenger_table.itemSelectionChanged.connect(
            self._handle_passenger_selection_changed
        )
        layout.addWidget(self.passenger_table, 1)

        self.passenger_status = QLabel()
        self.passenger_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.passenger_status)

        return page

    def _get_passenger_service(self):
        if not hasattr(self, "passenger_session"):
            self.passenger_session = SessionLocal()

        if not hasattr(self, "passenger_service"):
            from app.services.passenger_service import PassengerService
            self.passenger_service = PassengerService(
                self.passenger_session
            )

        return self.passenger_service

    def _refresh_passengers(self):
        try:
            service = self._get_passenger_service()
            search_text = self.passenger_search_input.text().strip()

            if search_text:
                passengers = service.search_passengers(search_text)
            else:
                passengers = service.get_all_passengers()

            self.passenger_table.set_passengers(passengers)
            self.passenger_status.setText(
                f"Showing {len(passengers)} passenger(s)."
            )
            self._handle_passenger_selection_changed()

        except Exception as error:
            self.passenger_status.setText("Unable to load passengers.")
            QMessageBox.critical(self, "Passenger Error", str(error))

    def _search_passengers(self, text):
        self._refresh_passengers()

    def _handle_passenger_selection_changed(self):
        has_selection = (
            self.passenger_table.get_selected_passenger()
            is not None
        )
        self.edit_passenger_button.setEnabled(has_selection)
        self.delete_passenger_button.setEnabled(has_selection)

    def _open_add_passenger_dialog(self):
        dialog = PassengerFormDialog(parent=self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            service = self._get_passenger_service()
            service.create_passenger_with_user(**data)
            self._refresh_passengers()
            QMessageBox.information(
                self, "Passenger Created",
                "Passenger created successfully.",
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Duplicate Passenger", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred:\n\n{error}",
            )

    def _open_edit_passenger_dialog(self):
        passenger = self.passenger_table.get_selected_passenger()

        if passenger is None:
            return

        dialog = PassengerFormDialog(
            parent=self, passenger=passenger
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            service = self._get_passenger_service()
            service.update_passenger(passenger.id, **data)
            self._refresh_passengers()
            QMessageBox.information(
                self, "Passenger Updated",
                "Passenger updated successfully.",
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Duplicate Passenger", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Not Found", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))

    def _delete_selected_passenger(self):
        passenger = self.passenger_table.get_selected_passenger()

        if passenger is None:
            return

        confirmation = QMessageBox.question(
            self, "Confirm Delete",
            (
                f"Delete {passenger.first_name} "
                f"{passenger.last_name}?\n\n"
                "This cannot be undone."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = self._get_passenger_service()
            service.delete_passenger(passenger.id)
            self._refresh_passengers()
            QMessageBox.information(
                self, "Passenger Deleted",
                "Passenger deleted successfully.",
            )
        except ResourceConflictError as error:
            QMessageBox.warning(
                self, "Cannot Delete", str(error)
            )
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Not Found", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))

    # ==================================================================
    # Staff management
    # ==================================================================

    def _create_staff_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.staff_search_input = QLineEdit()
        self.staff_search_input.setPlaceholderText(
            "Search by employee ID, name, or position..."
        )
        self.staff_search_input.setMinimumHeight(40)
        self.staff_search_input.textChanged.connect(
            self._search_staff
        )
        toolbar.addWidget(self.staff_search_input, 1)

        self.staff_refresh_button = QPushButton("Refresh")
        self.staff_refresh_button.clicked.connect(
            self._refresh_staff
        )
        toolbar.addWidget(self.staff_refresh_button)

        self.add_staff_button = QPushButton("+ Add Staff")
        self.add_staff_button.clicked.connect(
            self._open_add_staff_dialog
        )
        toolbar.addWidget(self.add_staff_button)

        self.edit_staff_button = QPushButton("Edit Staff")
        self.edit_staff_button.setEnabled(False)
        self.edit_staff_button.clicked.connect(
            self._open_edit_staff_dialog
        )
        toolbar.addWidget(self.edit_staff_button)

        self.delete_staff_button = QPushButton("Delete Staff")
        self.delete_staff_button.setEnabled(False)
        self.delete_staff_button.clicked.connect(
            self._delete_selected_staff
        )
        toolbar.addWidget(self.delete_staff_button)

        layout.addLayout(toolbar)

        self.staff_table = StaffTable()
        self.staff_table.itemSelectionChanged.connect(
            self._handle_staff_selection_changed
        )
        layout.addWidget(self.staff_table, 1)

        self.staff_status = QLabel()
        self.staff_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.staff_status)

        return page

    def _get_staff_service(self):
        if not hasattr(self, "staff_session"):
            self.staff_session = SessionLocal()

        if not hasattr(self, "staff_service"):
            from app.services.staff_service import StaffService
            self.staff_service = StaffService(self.staff_session)

        return self.staff_service

    def _refresh_staff(self):
        try:
            service = self._get_staff_service()
            search_text = self.staff_search_input.text().strip()

            if search_text:
                members = service.search_staff(search_text)
            else:
                members = service.get_all_staff()

            self.staff_table.set_staff(members)
            self.staff_status.setText(
                f"Showing {len(members)} staff member(s)."
            )
            self._handle_staff_selection_changed()

        except Exception as error:
            self.staff_status.setText("Unable to load staff.")
            QMessageBox.critical(self, "Staff Error", str(error))

    def _search_staff(self, text):
        self._refresh_staff()

    def _handle_staff_selection_changed(self):
        has_selection = (
            self.staff_table.get_selected_staff() is not None
        )
        self.edit_staff_button.setEnabled(has_selection)
        self.delete_staff_button.setEnabled(has_selection)

    def _open_add_staff_dialog(self):
        dialog = StaffFormDialog(parent=self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            service = self._get_staff_service()
            service.create_staff_with_user(**data)
            self._refresh_staff()
            QMessageBox.information(
                self, "Staff Created",
                "Staff member created successfully.",
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Duplicate Staff", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred:\n\n{error}",
            )

    def _open_edit_staff_dialog(self):
        staff = self.staff_table.get_selected_staff()

        if staff is None:
            return

        dialog = StaffFormDialog(parent=self, staff=staff)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            service = self._get_staff_service()
            service.update_staff(staff.id, **data)
            self._refresh_staff()
            QMessageBox.information(
                self, "Staff Updated",
                "Staff member updated successfully.",
            )
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Not Found", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))

    def _delete_selected_staff(self):
        staff = self.staff_table.get_selected_staff()

        if staff is None:
            return

        confirmation = QMessageBox.question(
            self, "Confirm Delete",
            (
                f"Delete {staff.first_name} {staff.last_name} "
                f"({staff.employee_id})?\n\n"
                "This cannot be undone."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = self._get_staff_service()
            service.delete_staff(staff.id)
            self._refresh_staff()
            QMessageBox.information(
                self, "Staff Deleted",
                "Staff member deleted successfully.",
            )
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Cannot Delete", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Not Found", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))

    # ==================================================================
    # Route management
    # ==================================================================

    def _create_route_page(self) -> QWidget:
        """Create the administrator route management interface."""

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        search_container = QWidget()
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(4)

        self.route_search_input = QLineEdit()
        self.route_search_input.setObjectName("routeSearch")
        self.route_search_input.setPlaceholderText(
            "Search by origin or destination airport..."
        )
        self.route_search_input.setClearButtonEnabled(True)
        self.route_search_input.setMinimumHeight(40)
        self.route_search_input.textChanged.connect(self._search_routes)

        search_layout.addWidget(self.route_search_input)
        toolbar.addWidget(search_container, 1)

        self.route_refresh_button = QPushButton("Refresh")
        self.route_refresh_button.setObjectName("routeRefreshButton")
        self.route_refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.route_refresh_button.clicked.connect(self._refresh_routes)
        toolbar.addWidget(self.route_refresh_button)

        self.add_route_button = QPushButton("+ Add Route")
        self.add_route_button.setObjectName("addRouteButton")
        self.add_route_button.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar.addWidget(self.add_route_button)

        self.edit_route_button = QPushButton("Edit Route")
        self.edit_route_button.setObjectName("editRouteButton")
        self.edit_route_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_route_button.setEnabled(False)
        toolbar.addWidget(self.edit_route_button)

        self.delete_route_button = QPushButton("Delete Route")
        self.delete_route_button.setObjectName("routeDeleteButton")
        self.delete_route_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_route_button.setEnabled(False)
        toolbar.addWidget(self.delete_route_button)

        self.add_route_button.clicked.connect(self._open_add_route_dialog)
        self.edit_route_button.clicked.connect(self._open_edit_route_dialog)
        self.delete_route_button.clicked.connect(self._delete_selected_route)

        layout.addLayout(toolbar)

        self.route_table = RouteTable()
        self.route_table.setMinimumHeight(350)
        self.route_table.itemSelectionChanged.connect(
            self._handle_route_selection_changed
        )
        layout.addWidget(self.route_table, 1)

        self.route_status = QLabel()
        self.route_status.setObjectName("routeStatus")
        self.route_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.route_status)

        return page

    def _create_route_service(self):
        if not hasattr(self, "route_session"):
            self.route_session = SessionLocal()

        if not hasattr(self, "route_service"):
            from app.services import RouteService
            self.route_service = RouteService(self.route_session)

        return self.route_service

    def _refresh_routes(self) -> None:
        try:
            service = self._create_route_service()
            search_text = self.route_search_input.text().strip()

            if search_text:
                routes = service.search_routes(search_text)
            else:
                routes = service.get_all_routes()

            self.route_table.set_routes(routes)
            self.route_status.setText(
                f"Showing {len(routes)} route(s)."
            )
            self._handle_route_selection_changed()

        except DatabaseOperationError as error:
            self.route_status.setText("Unable to load routes.")
            QMessageBox.critical(self, "Route Error", str(error))
        except Exception as error:
            self.route_status.setText("Unable to load routes.")
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while loading routes:\n\n{error}",
            )

    def _search_routes(self, search_text: str) -> None:
        self._refresh_routes()

    def _handle_route_selection_changed(self) -> None:
        has_selection = self.route_table.currentRow() >= 0
        self.edit_route_button.setEnabled(has_selection)
        self.delete_route_button.setEnabled(has_selection)

    def _open_add_route_dialog(self) -> None:
        session = self._create_route_service().session

        dialog = RouteFormDialog(
            parent=self,
            session=session,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            service = self._create_route_service()
            service.create_route(**data)
            self._refresh_routes()
            QMessageBox.information(
                self, "Route Created",
                "Route created successfully.",
            )
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Duplicate Route", str(error))
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Airport Not Found", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while creating the route:\n\n{error}",
            )

    def _open_edit_route_dialog(self) -> None:
        route = self.route_table.get_selected_route()

        if route is None:
            QMessageBox.warning(
                self, "No Selection",
                "Please select a route first.",
            )
            return

        session = self._create_route_service().session

        dialog = RouteFormDialog(
            parent=self,
            session=session,
            route=route,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        try:
            service = self._create_route_service()
            service.update_route(route.id, **data)
            self._refresh_routes()
            QMessageBox.information(
                self, "Route Updated",
                "Route updated successfully.",
            )
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Duplicate Route", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Route Not Found", str(error))
        except ValidationError as error:
            QMessageBox.warning(self, "Validation Error", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while updating the route:\n\n{error}",
            )

    def _delete_selected_route(self) -> None:
        route = self.route_table.get_selected_route()

        if route is None:
            QMessageBox.warning(
                self, "No Selection",
                "Please select a route first.",
            )
            return

        origin = getattr(route, "origin_airport", None)
        destination = getattr(route, "destination_airport", None)

        origin_code = origin.iata_code if origin else "?"
        destination_code = destination.iata_code if destination else "?"

        confirmation = QMessageBox.question(
            self, "Confirm Delete",
            (
                f"Delete route {origin_code} → {destination_code}?\n\n"
                "This action cannot be undone."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = self._create_route_service()
            service.delete_route(route.id)
            self._refresh_routes()
            QMessageBox.information(
                self, "Route Deleted",
                "Route deleted successfully.",
            )
        except ResourceConflictError as error:
            QMessageBox.warning(self, "Cannot Delete Route", str(error))
        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "Route Not Found", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "Unexpected Error",
                f"An unexpected error occurred while deleting the route:\n\n{error}",
            )

    def close_route_session(self) -> None:
        if getattr(self, "route_session", None) is not None:
            self.route_session.close()
            self.route_session = None
            self.route_service = None

    # ==================================================================
    # Placeholder pages
    # ==================================================================

    def _refresh_bookings(self) -> None:
        """Refresh the admin bookings page."""

        page = self.pages.get("bookings")

        if page is None:
            return

        if hasattr(page, "refresh_table"):
            page.refresh_table()

    def _refresh_reports(self) -> None:
        """Refresh the reports page."""

        page = self.pages.get("reports")

        if page is None:
            return

        if hasattr(page, "refresh"):
            page.refresh()

    def _create_placeholder_page(self, title: str, subtitle: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setObjectName("placeholderTitle")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("placeholderSubtitle")

        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)

        return page

    # ==================================================================
    # Dashboard data
    # ==================================================================

    def _create_dashboard_service(self) -> DashboardService:
        if self.dashboard_session is None:
            self.dashboard_session = SessionLocal()
            self.dashboard_service = DashboardService(self.dashboard_session)
        return self.dashboard_service

    def _show_dashboard(self) -> None:
        page = self.pages["dashboard"]
        self.stack.setCurrentWidget(page)
        self.page_title.setText("Dashboard")
        self.page_subtitle.setText("Overview of your airline operations")
        self._refresh_dashboard()

    def _refresh_dashboard(self) -> None:
        try:
            service = self._create_dashboard_service()

            # Drop cached ORM state so we see changes made by
            # other sessions (e.g. FlightManagementPage).
            self.dashboard_session.expire_all()

            statistics = service.get_dashboard_statistics()

            for key, value in statistics.items():
                card = self.dashboard_cards.get(key)
                if card is not None:
                    card.set_value(value)

            flights = service.get_recent_flights(limit=10)
            self.flight_table.set_flights(flights)

            if flights:
                self.dashboard_status.setText(
                    f"Showing {len(flights)} recent/upcoming flight(s)."
                )
            else:
                self.dashboard_status.setText(
                    "No flights have been created yet."
                )

        except PermissionError as error:
            self.dashboard_status.setText(str(error))
        except Exception as error:
            self.dashboard_status.setText("Unable to load dashboard data.")
            QMessageBox.critical(
                self, "Dashboard Error",
                f"An error occurred while loading the dashboard:\n\n{error}",
            )

    # ==================================================================
    # Navigation
    # ==================================================================

    def _handle_navigation(self, page_key: str) -> None:
        if page_key not in self.pages:
            return

        page = self.pages[page_key]
        self.stack.setCurrentWidget(page)

        page_information = {
            "dashboard": ("Dashboard", "Overview of your airline operations"),
            "airports": ("Airports", "Manage airport information"),
            "aircraft": ("Aircraft", "Manage airline aircraft"),
            "routes": ("Routes", "Manage flight routes"),
            "flights": ("Flights", "Create and manage flights"),
            "schedule": ("Schedule Generator", "Bulk-generate flights with ML fares"),
            "crew_assignment": ("Crew Assignment", "Assign crew to flights"),
            "staff": ("Staff", "Manage airline staff"),
            "bookings": ("Bookings", "View passenger bookings"),
            "passengers": ("Passengers", "View registered passengers"),
            "reports": ("Reports", "View airline reports"),
        }

        title, subtitle = page_information.get(
            page_key, ("Administrator", "")
        )

        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

        if page_key == "dashboard":
            self._refresh_dashboard()
        elif page_key == "airports":
            self._refresh_airports()
        elif page_key == "aircraft":
            self._refresh_aircraft()
        elif page_key == "flights":
            self._refresh_flights()
        elif page_key == "routes":
            self._refresh_routes()
        elif page_key == "bookings":
            self._refresh_bookings()

    # ==================================================================
    # Logout
    # ==================================================================

    def _handle_logout(self) -> None:
        result = QMessageBox.question(
            self, "Confirm Logout",
            "Are you sure you want to log out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result != QMessageBox.StandardButton.Yes:
            return

        application_context.session.logout()
        self.close()
        self.logout_requested.emit()

    # ==================================================================
    # Styles
    # ==================================================================

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #F8FAFC;
                color: #0F172A;
                font-family: "Segoe UI";
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

            QLabel#dashboardStatus,
            QLabel#airportStatus,
            QLabel#aircraftStatus {
                color: #64748B;
                font-size: 11px;
                padding: 4px;
            }

            QPushButton#refreshButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#refreshButton:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
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

            QLineEdit#airportSearch,
            QLineEdit#aircraftSearch {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                color: #0F172A;
                padding: 0 14px;
                font-size: 12px;
            }

            QLineEdit#airportSearch:focus,
            QLineEdit#aircraftSearch:focus {
                border: 1px solid #94A3B8;
            }

            QPushButton#airportRefreshButton,
            QPushButton#aircraftRefreshButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#airportRefreshButton:hover,
            QPushButton#aircraftRefreshButton:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
            }

            QPushButton#addAirportButton,
            QPushButton#addAircraftButton {
                background-color: #0F172A;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#addAirportButton:hover,
            QPushButton#addAircraftButton:hover {
                background-color: #1E293B;
            }

            QPushButton#editAirportButton,
            QPushButton#editAircraftButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 9px 16px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#editAirportButton:hover:enabled,
            QPushButton#editAircraftButton:hover:enabled {
                background-color: #F8FAFC;
                border-color: #94A3B8;
            }

            QPushButton#editAirportButton:disabled,
            QPushButton#editAircraftButton:disabled {
                background-color: #F8FAFC;
                color: #94A3B8;
                border: 1px solid #E2E8F0;
            }

            QPushButton#airportDeleteButton,
            QPushButton#aircraftDeleteButton {
                background-color: #FFFFFF;
                color: #B91C1C;
                border: 1px solid #FCA5A5;
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#airportDeleteButton:hover:enabled,
            QPushButton#aircraftDeleteButton:hover:enabled {
                background-color: #FEF2F2;
                border-color: #F87171;
            }

            QPushButton#airportDeleteButton:disabled,
            QPushButton#aircraftDeleteButton:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border-color: #E2E8F0;
            }

            QPushButton#aircraftViewSeatsButton {
                background-color: #FFFFFF;
                color: #1E40AF;
                border: 1px solid #BFDBFE;
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#aircraftViewSeatsButton:hover:enabled {
                background-color: #EFF6FF;
                border-color: #93C5FD;
            }

            QPushButton#aircraftViewSeatsButton:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border-color: #E2E8F0;
            }

            QPushButton#aircraftActivateButton {
                background-color: #ECFDF5;
                color: #047857;
                border: 1px solid #6EE7B7;
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#aircraftActivateButton:hover:enabled {
                background-color: #D1FAE5;
                border-color: #34D399;
            }

            QPushButton#aircraftActivateButton:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border-color: #E2E8F0;
            }

            QPushButton#aircraftMaintenanceButton {
                background-color: #FFFBEB;
                color: #B45309;
                border: 1px solid #FCD34D;
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#aircraftMaintenanceButton:hover:enabled {
                background-color: #FEF3C7;
                border-color: #FBBF24;
            }

            QPushButton#aircraftMaintenanceButton:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border-color: #E2E8F0;
            }

            QPushButton#aircraftInactiveButton {
                background-color: #F8FAFC;
                color: #64748B;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton#aircraftInactiveButton:hover:enabled {
                background-color: #F1F5F9;
                border-color: #94A3B8;
            }

            QPushButton#aircraftInactiveButton:disabled {
                background-color: #F1F5F9;
                color: #94A3B8;
                border-color: #E2E8F0;
            }
            """
        )

    # ==================================================================
    # Cleanup
    # ==================================================================

    def closeEvent(self, event) -> None:
        if getattr(self, "dashboard_session", None) is not None:
            self.dashboard_session.close()
            self.dashboard_session = None
            self.dashboard_service = None

        if getattr(self, "airport_session", None) is not None:
            self.airport_session.close()
            self.airport_session = None
            self.airport_service = None

        if getattr(self, "aircraft_session", None) is not None:
            self.aircraft_session.close()
            self.aircraft_session = None

        if getattr(self, "flight_session", None) is not None:
            self.flight_session.close()
            self.flight_session = None

        if getattr(self, "route_session", None) is not None:
            self.route_session.close()
            self.route_session = None
            self.route_service = None

        super().closeEvent(event)