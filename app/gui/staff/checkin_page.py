from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QInputDialog,
    QHeaderView,
)

from app.config.database import SessionLocal
from app.models import (
    BookingStatus,
    CheckInMethod,
)
from app.repositories import StaffRepository
from app.services import (
    BookingService,
    CheckInService,
    BaggageService,
    BoardingPassService,
)
from app.services.application import application_context
from app.utils.pdf_generator import (
    generate_boarding_pass_pdf,
    generate_baggage_tag_pdf,
)
from app.gui.staff.pdf_preview_dialog import PdfPreviewDialog
import tempfile
from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class CheckInPage(QWidget):
    """
    Staff page: find a booking by reference, check in the
    passenger, add baggage, issue a boarding pass.
    """

    def __init__(self, session, parent=None):

        super().__init__(parent)

        self.session = session
        self.current_booking = None
        self.current_checkin = None

        self.staff_id = self._resolve_staff_id()

        self.setup_ui()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _resolve_staff_id(self):
        """
        Look up the Staff profile linked to the logged-in user.
        """

        user = application_context.session.current_user

        if user is None or not hasattr(user, "user_id"):
            return None

        try:
            repo = StaffRepository(self.session)
            staff = self.session.query(
                __import__(
                    "app.models", fromlist=["Staff"]
                ).Staff
            ).filter(
                __import__(
                    "app.models", fromlist=["Staff"]
                ).Staff.user_id == user.user_id
            ).first()

            if staff is not None:
                return staff.id

        except Exception:
            pass

        return None

    def setup_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)

        # ---- Search bar ----
        search_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Booking reference (e.g. BK8XWXSD11)"
        )
        self.search_input.setMinimumHeight(40)
        self.search_input.returnPressed.connect(
            self.search_booking
        )

        search_row.addWidget(self.search_input, 1)

        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("addAirportButton")
        self.search_button.clicked.connect(self.search_booking)
        search_row.addWidget(self.search_button)

        layout.addLayout(search_row)

        # ---- Booking detail card ----
        self.detail_frame = QFrame()
        self.detail_frame.setObjectName("loginCard")
        detail_layout = QVBoxLayout(self.detail_frame)

        self.detail_title = QLabel("No booking selected")
        self.detail_title.setObjectName("sectionTitle")
        detail_layout.addWidget(self.detail_title)

        self.detail_info = QLabel("")
        self.detail_info.setWordWrap(True)
        self.detail_info.setObjectName("pageSubtitle")
        detail_layout.addWidget(self.detail_info)

        # Booking actions
        booking_actions = QHBoxLayout()

        self.checkin_button = QPushButton("Check In")
        self.checkin_button.setEnabled(False)
        self.checkin_button.clicked.connect(self.do_check_in)
        booking_actions.addWidget(self.checkin_button)

        self.undo_checkin_button = QPushButton("Undo Check-In")
        self.undo_checkin_button.setEnabled(False)
        self.undo_checkin_button.clicked.connect(
            self.undo_check_in
        )
        booking_actions.addWidget(self.undo_checkin_button)

        booking_actions.addStretch()
        detail_layout.addLayout(booking_actions)

        layout.addWidget(self.detail_frame)

        # ---- Baggage section ----
        baggage_label = QLabel("Baggage:")
        baggage_label.setObjectName("sectionTitle")
        layout.addWidget(baggage_label)

        self.baggage_table = QTableWidget()
        self.baggage_table.setColumnCount(4)
        self.baggage_table.setHorizontalHeaderLabels(
            ["Tag", "Weight (kg)", "Status", "ID"]
        )
        self.baggage_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.baggage_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.baggage_table.verticalHeader().setVisible(False)
        self.baggage_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.baggage_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.baggage_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        # Hide the ID column
        self.baggage_table.setColumnHidden(3, True)
        self.baggage_table.setMinimumHeight(140)
        self.baggage_table.itemSelectionChanged.connect(
            self._update_actions
        )
        layout.addWidget(self.baggage_table)

        baggage_actions = QHBoxLayout()

        self.add_baggage_button = QPushButton("+ Add Baggage")
        self.add_baggage_button.setEnabled(False)
        self.add_baggage_button.clicked.connect(self.add_baggage)
        baggage_actions.addWidget(self.add_baggage_button)

        self.remove_baggage_button = QPushButton(
            "Remove Selected Baggage"
        )
        self.remove_baggage_button.setEnabled(False)
        self.remove_baggage_button.clicked.connect(
            self.remove_baggage
        )
        baggage_actions.addWidget(self.remove_baggage_button)

        self.print_tag_button = QPushButton("Print Baggage Tag")
        self.print_tag_button.setEnabled(False)
        self.print_tag_button.clicked.connect(
            self.print_baggage_tag
        )
        baggage_actions.addWidget(self.print_tag_button)

        baggage_actions.addStretch()
        layout.addLayout(baggage_actions)

        # ---- Boarding pass section ----
        boarding_label = QLabel("Boarding Pass:")
        boarding_label.setObjectName("sectionTitle")
        layout.addWidget(boarding_label)

        self.boarding_info = QLabel("No boarding pass issued.")
        self.boarding_info.setObjectName("pageSubtitle")
        layout.addWidget(self.boarding_info)

        issue_row = QHBoxLayout()

        self.issue_pass_button = QPushButton("Issue Boarding Pass")
        self.issue_pass_button.setEnabled(False)
        self.issue_pass_button.clicked.connect(
            self.issue_boarding_pass
        )
        issue_row.addWidget(self.issue_pass_button)

        self.print_pass_button = QPushButton("Print Boarding Pass")
        self.print_pass_button.setEnabled(False)
        self.print_pass_button.clicked.connect(
            self.print_boarding_pass
        )
        issue_row.addWidget(self.print_pass_button)

        issue_row.addStretch()
        layout.addLayout(issue_row)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("dashboardStatus")
        layout.addWidget(self.status_label)

        layout.addStretch()

        self._update_actions()

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_booking(self):

        reference = self.search_input.text().strip()

        if not reference:
            QMessageBox.warning(
                self,
                "Missing Reference",
                "Please enter a booking reference.",
            )
            return

        try:
            service = BookingService(self.session)
            booking = service.get_booking_by_reference(reference)

            if booking is None:
                raise ResourceNotFoundError(
                    f"No booking found for '{reference}'."
                )

            self.current_booking = booking
            self._load_checkin()
            self._render_booking()
            self._load_baggage()
            self._load_boarding_pass()
            self._update_actions()

            self.status_label.setText(
                f"Found booking {booking.booking_reference}."
            )

        except ResourceNotFoundError as error:
            self.current_booking = None
            self.current_checkin = None
            self._render_booking()
            self._update_actions()
            QMessageBox.warning(
                self, "Not Found", str(error)
            )
        except Exception as error:
            QMessageBox.critical(
                self, "Error", str(error)
            )

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_booking(self):

        booking = self.current_booking

        if booking is None:
            self.detail_title.setText("No booking selected")
            self.detail_info.setText("")
            return

        self.detail_title.setText(
            f"Booking {booking.booking_reference}"
        )

        passenger = booking.passenger
        flight = booking.flight
        seat = booking.seat

        route_text = ""
        if flight is not None and flight.route is not None:
            route = flight.route
            origin = route.origin_airport
            destination = route.destination_airport
            if origin and destination:
                route_text = (
                    f"{origin.iata_code} \u2192 "
                    f"{destination.iata_code}"
                )

        lines = [
            f"Passenger:  {passenger.first_name} "
            f"{passenger.last_name}",
            f"Passport:   {passenger.passport_number}",
            f"Flight:     {flight.flight_number} "
            f"({route_text})"
            if flight
            else "Flight:     —",
            f"Departure:  {flight.departure_time}"
            if flight
            else "Departure:  —",
            f"Seat:       {seat.seat_number}"
            if seat
            else "Seat:       —",
            f"Fare:       ${booking.fare_amount}",
            f"Status:     {booking.status.value}",
        ]

        self.detail_info.setText("\n".join(lines))

    def _load_checkin(self):

        self.current_checkin = None

        if self.current_booking is None:
            return

        try:
            service = CheckInService(self.session)
            self.current_checkin = (
                service.get_checkin_by_booking(
                    self.current_booking.id
                )
            )
        except ResourceNotFoundError:
            self.current_checkin = None
        except Exception:
            self.current_checkin = None

    def _load_baggage(self):

        self.baggage_table.setRowCount(0)

        if self.current_checkin is None:
            return

        try:
            service = BaggageService(self.session)
            bags = service.get_baggage_for_checkin(
                self.current_checkin.id
            )

            for bag in bags:
                row = self.baggage_table.rowCount()
                self.baggage_table.insertRow(row)

                tag_item = QTableWidgetItem(bag.bag_tag)
                tag_item.setData(Qt.ItemDataRole.UserRole, bag.id)

                self.baggage_table.setItem(row, 0, tag_item)
                self.baggage_table.setItem(
                    row, 1,
                    QTableWidgetItem(str(bag.weight_kg)),
                )
                self.baggage_table.setItem(
                    row, 2,
                    QTableWidgetItem(bag.status.value),
                )
                self.baggage_table.setItem(
                    row, 3,
                    QTableWidgetItem(str(bag.id)),
                )

        except Exception as error:
            QMessageBox.critical(
                self, "Baggage Error", str(error)
            )

    def _load_boarding_pass(self):

        self.boarding_info.setText("No boarding pass issued.")

        if self.current_booking is None:
            return

        try:
            service = BoardingPassService(self.session)
            bp = service.get_pass_for_booking(
                self.current_booking.id
            )

            self.boarding_info.setText(
                f"Number:  {bp.boarding_pass_number}\n"
                f"Group:   {bp.boarding_group}\n"
                f"Gate:    {bp.boarding_gate}"
            )
        except ResourceNotFoundError:
            pass
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Button enable/disable logic
    # ------------------------------------------------------------------

    def _update_actions(self):

        booking = self.current_booking
        checkin = self.current_checkin

        # No booking → everything off
        if booking is None:
            self.checkin_button.setEnabled(False)
            self.undo_checkin_button.setEnabled(False)
            self.add_baggage_button.setEnabled(False)
            self.remove_baggage_button.setEnabled(False)
            self.issue_pass_button.setEnabled(False)
            self.print_pass_button.setEnabled(False)
            self.print_tag_button.setEnabled(False)
            return

        status = booking.status

        # Check In: only when CONFIRMED
        self.checkin_button.setEnabled(
            status == BookingStatus.CONFIRMED
        )

        # Undo: only when CHECKED_IN and checkin exists
        self.undo_checkin_button.setEnabled(
            status == BookingStatus.CHECKED_IN
            and checkin is not None
        )

        # Baggage: only after check-in
        checked_in = status == BookingStatus.CHECKED_IN
        self.add_baggage_button.setEnabled(checked_in)
        self.remove_baggage_button.setEnabled(
            checked_in
            and self.baggage_table.currentRow() >= 0
        )

        # Boarding pass: only when CHECKED_IN and not yet issued
        has_pass = self.boarding_info.text().startswith("Number:")
        self.issue_pass_button.setEnabled(
            checked_in and not has_pass
        )

        # Print buttons
        self.print_pass_button.setEnabled(has_pass)

        has_bag_selected = (
            self.baggage_table.currentRow() >= 0
        )
        self.print_tag_button.setEnabled(
            checked_in and has_bag_selected
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def do_check_in(self):

        if self.current_booking is None:
            return

        try:
            service = CheckInService(self.session)
            self.current_checkin = service.check_in_booking(
                booking_id=self.current_booking.id,
                staff_id=self.staff_id,
                method=CheckInMethod.STAFF,
            )

            # Refresh the in-memory booking object
            self.session.refresh(self.current_booking)

            self._render_booking()
            self._load_baggage()
            self._update_actions()

            QMessageBox.information(
                self,
                "Checked In",
                "Passenger checked in successfully.",
            )

        except (
            ValidationError,
            ResourceConflictError,
            ResourceNotFoundError,
        ) as error:
            QMessageBox.warning(self, "Cannot Check In", str(error))
            self._update_actions()
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
            self._update_actions()

    def undo_check_in(self):

        if self.current_checkin is None:
            return

        try:
            service = CheckInService(self.session)
            service.cancel_checkin(self.current_checkin.id)

            self.session.refresh(self.current_booking)
            self.current_checkin = None

            self._render_booking()
            self._load_baggage()
            self._load_boarding_pass()
            self._update_actions()

            QMessageBox.information(
                self,
                "Check-In Cancelled",
                "Check-in was undone.",
            )

        except (
            ValidationError,
            ResourceConflictError,
            ResourceNotFoundError,
        ) as error:
            QMessageBox.warning(self, "Cannot Undo", str(error))
            self._update_actions()
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
            self._update_actions()

    def add_baggage(self):

        if self.current_checkin is None:
            return

        weight, ok = QInputDialog.getDouble(
            self,
            "Add Baggage",
            "Weight (kg):",
            20.0,
            0.1,
            40.0,
            2,
        )

        if not ok:
            return

        try:
            service = BaggageService(self.session)
            bag = service.add_baggage(
                checkin_id=self.current_checkin.id,
                weight_kg=weight,
            )

            self._load_baggage()
            self._update_actions()

            QMessageBox.information(
                self,
                "Baggage Added",
                f"Bag tag: {bag.bag_tag}",
            )

        except (
            ValidationError,
            ResourceConflictError,
            ResourceNotFoundError,
        ) as error:
            QMessageBox.warning(self, "Cannot Add Baggage", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))

    def remove_baggage(self):

        row = self.baggage_table.currentRow()

        if row < 0:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a bag to remove.",
            )
            return

        item = self.baggage_table.item(row, 0)
        if item is None:
            return

        bag_id = item.data(Qt.ItemDataRole.UserRole)

        confirmation = QMessageBox.question(
            self,
            "Remove Baggage",
            "Remove this bag from the check-in?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = BaggageService(self.session)
            service.remove_baggage(bag_id)

            self._load_baggage()
            self._update_actions()

        except Exception as error:
            QMessageBox.warning(
                self, "Cannot Remove Baggage", str(error)
            )

    def print_boarding_pass(self):

        if self.current_booking is None:
            return

        try:
            service = BoardingPassService(self.session)
            bp = service.get_pass_for_booking(
                self.current_booking.id
            )

            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            )
            tmp.close()

            generate_boarding_pass_pdf(
                bp,
                self.current_booking,
                tmp.name,
            )

            dialog = PdfPreviewDialog(
                self,
                tmp.name,
                f"boarding_pass_{bp.boarding_pass_number}.pdf",
                title="Boarding Pass Ready",
            )
            dialog.exec()

        except ResourceNotFoundError as error:
            QMessageBox.warning(self, "No Boarding Pass", str(error))
        except Exception as error:
            QMessageBox.critical(
                self, "PDF Generation Error", str(error)
            )

    def print_baggage_tag(self):

        row = self.baggage_table.currentRow()

        if row < 0:
            return

        item = self.baggage_table.item(row, 0)
        if item is None:
            return

        bag_id = item.data(Qt.ItemDataRole.UserRole)

        try:
            from app.repositories import BaggageRepository
            repo = BaggageRepository(self.session)
            bag = repo.get_by_id(bag_id)

            if bag is None:
                raise ResourceNotFoundError(
                    "Baggage was not found."
                )

            tmp = tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            )
            tmp.close()

            generate_baggage_tag_pdf(
                bag,
                self.current_checkin,
                self.current_booking,
                tmp.name,
            )

            dialog = PdfPreviewDialog(
                self,
                tmp.name,
                f"baggage_tag_{bag.bag_tag}.pdf",
                title="Baggage Tag Ready",
            )
            dialog.exec()

        except Exception as error:
            QMessageBox.critical(
                self, "PDF Generation Error", str(error)
            )

    def issue_boarding_pass(self):

        if self.current_booking is None:
            return

        gate, ok = QInputDialog.getText(
            self,
            "Issue Boarding Pass",
            "Boarding gate:",
            text="A1",
        )

        if not ok or not gate.strip():
            return

        group, ok = QInputDialog.getText(
            self,
            "Issue Boarding Pass",
            "Boarding group:",
            text="A",
        )

        if not ok or not group.strip():
            return

        try:
            service = BoardingPassService(self.session)
            bp = service.issue_boarding_pass(
                booking_id=self.current_booking.id,
                boarding_gate=gate.strip(),
                boarding_group=group.strip(),
                issued_by=self.staff_id,
            )

            self._load_boarding_pass()
            self._update_actions()

            QMessageBox.information(
                self,
                "Boarding Pass Issued",
                f"Pass number: {bp.boarding_pass_number}",
            )

        except (
            ValidationError,
            ResourceConflictError,
            ResourceNotFoundError,
        ) as error:
            QMessageBox.warning(
                self, "Cannot Issue Pass", str(error)
            )
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
