from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QComboBox,
)

from PySide6.QtCore import Qt

from app.gui.components.booking_table import BookingTable

from app.models import BookingStatus
from app.services.booking_service import BookingService
from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class AdminBookingManagementPage(QWidget):
    """
    Admin view for managing all bookings.
    """

    def __init__(self, session, parent=None):

        super().__init__(parent)

        self.session = session

        self.setup_ui()

    def setup_ui(self):

        layout = QVBoxLayout()

        title = QLabel("All Bookings")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ---- filter bar ----

        filter_bar = QHBoxLayout()

        filter_bar.addWidget(QLabel("Filter by status:"))

        self.status_filter = QComboBox()
        self.status_filter.addItem("All", None)

        for status in BookingStatus:
            self.status_filter.addItem(status.value, status)

        self.status_filter.currentIndexChanged.connect(
            self.refresh_table
        )

        filter_bar.addWidget(self.status_filter)
        filter_bar.addStretch()

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_table)
        filter_bar.addWidget(self.refresh_button)

        layout.addLayout(filter_bar)

        # ---- table ----

        self.booking_table = BookingTable()
        self.booking_table.itemSelectionChanged.connect(
            self._on_selection_changed
        )
        layout.addWidget(self.booking_table, 1)

        # ---- action bar ----

        action_bar = QHBoxLayout()

        self.mark_paid_button = QPushButton("Mark as Paid")
        self.check_in_button = QPushButton("Check In")
        self.complete_button = QPushButton("Complete")
        self.cancel_button = QPushButton("Cancel Booking")
        self.approve_refund_button = QPushButton("Approve Refund")
        self.reject_refund_button = QPushButton("Reject Refund")

        buttons = [
            self.mark_paid_button,
            self.check_in_button,
            self.complete_button,
            self.cancel_button,
            self.approve_refund_button,
            self.reject_refund_button,
        ]

        for button in buttons:
            button.setEnabled(False)
            action_bar.addWidget(button)

        action_bar.addStretch()
        layout.addLayout(action_bar)

        self.mark_paid_button.clicked.connect(
            lambda: self._apply_action(
                "mark_as_paid",
                "Mark as Paid",
            )
        )
        self.check_in_button.clicked.connect(
            lambda: self._apply_action(
                "check_in",
                "Check In",
            )
        )
        self.complete_button.clicked.connect(
            lambda: self._apply_action(
                "complete_booking",
                "Complete",
            )
        )
        self.cancel_button.clicked.connect(
            lambda: self._apply_action(
                "cancel_booking",
                "Cancel",
            )
        )
        self.approve_refund_button.clicked.connect(
            lambda: self._apply_action(
                "approve_refund",
                "Approve Refund",
            )
        )
        self.reject_refund_button.clicked.connect(
            lambda: self._apply_action(
                "reject_refund",
                "Reject Refund",
            )
        )

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.refresh_table()

    # ------------------------------------------------------------------

    def refresh_table(self):

        try:
            service = BookingService(self.session)

            status_filter = self.status_filter.currentData()

            if status_filter is None:
                bookings = service.get_all_bookings()
            else:
                bookings = [
                    b for b in service.get_all_bookings()
                    if b.status == status_filter
                ]

            self.booking_table.set_bookings(bookings)

            self.status_label.setText(
                f"Showing {len(bookings)} booking(s)."
            )

            self._on_selection_changed()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Booking Load Error",
                str(error),
            )

    def _on_selection_changed(self):

        booking_id = self.booking_table.get_selected_booking_id()

        if booking_id is None:
            for button in self._all_buttons():
                button.setEnabled(False)
            return

        # Find the booking's status from the current table
        row = self.booking_table.currentRow()
        # We can't easily get the status from the row here — re-query
        # for a clean state.

        try:
            service = BookingService(self.session)
            booking = service.get_booking_by_id(booking_id)
        except Exception:
            return

        status = booking.status

        self.mark_paid_button.setEnabled(status == BookingStatus.UNPAID)
        self.check_in_button.setEnabled(status == BookingStatus.CONFIRMED)
        self.complete_button.setEnabled(status == BookingStatus.CHECKED_IN)
        self.cancel_button.setEnabled(
            status in (BookingStatus.UNPAID, BookingStatus.CONFIRMED)
        )
        self.approve_refund_button.setEnabled(
            status == BookingStatus.REFUND_REQUESTED
        )
        self.reject_refund_button.setEnabled(
            status == BookingStatus.REFUND_REQUESTED
        )

    def _all_buttons(self):
        return [
            self.mark_paid_button,
            self.check_in_button,
            self.complete_button,
            self.cancel_button,
            self.approve_refund_button,
            self.reject_refund_button,
        ]

    def _apply_action(self, method_name, action_label):

        booking_id = self.booking_table.get_selected_booking_id()

        if booking_id is None:
            return

        message = (
            f"Are you sure you want to {action_label.lower()} "
            "this booking?"
        )

        if method_name == "approve_refund":
            try:
                service = BookingService(self.session)
                preview = service.preview_refund(booking_id)
                pct = int(preview["percentage"] * 100)
                message = (
                    "Approve refund for this booking?\n\n"
                    f"Refund tier: {pct}% of fare\n"
                    f"Refund amount: ${preview['amount']}\n\n"
                    "This action cannot be undone."
                )
            except Exception as error:
                QMessageBox.warning(self, "Preview Error", str(error))
                return

        confirmation = QMessageBox.question(
            self,
            f"Confirm {action_label}",
            message,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirmation != QMessageBox.StandardButton.Yes:
            return

        try:
            service = BookingService(self.session)
            method = getattr(service, method_name)
            method(booking_id)

            self.refresh_table()

            if method_name == "approve_refund":
                refreshed = service.get_booking_by_id(booking_id)
                QMessageBox.information(
                    self,
                    "Refund Approved",
                    (
                        "Refund approved.\n\n"
                        f"Amount refunded: "
                        f"${refreshed.refund_amount}"
                    ),
                )
            else:
                QMessageBox.information(
                    self,
                    f"{action_label} Successful",
                    f"Booking {action_label.lower()}ed successfully.",
                )

        except (
            ValidationError,
            ResourceConflictError,
            ResourceNotFoundError,
        ) as error:
            QMessageBox.warning(self, "Action Failed", str(error))
        except DatabaseOperationError as error:
            QMessageBox.critical(self, "Database Error", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Unexpected Error", str(error))