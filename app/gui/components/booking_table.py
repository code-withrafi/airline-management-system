from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
)


class BookingTable(QTableWidget):

    HEADERS = [
        "Reference",
        "Flight",
        "Seat",
        "Fare",
        "Status",
        "Refund",
        "Booked Date",
    ]

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setColumnCount(len(self.HEADERS))

        self.setHorizontalHeaderLabels(self.HEADERS)

        self.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        self.verticalHeader().setVisible(False)

        self.horizontalHeader().setStretchLastSection(True)

    def set_bookings(
        self,
        bookings,
    ):

        self.setRowCount(0)

        for booking in bookings:

            row = self.rowCount()

            self.insertRow(row)

            reference_item = QTableWidgetItem(
                booking.booking_reference
            )

            reference_item.setData(
                Qt.ItemDataRole.UserRole,
                booking.id,
            )

            self.setItem(row, 0, reference_item)

            self.setItem(
                row,
                1,
                QTableWidgetItem(
                    booking.flight.flight_number
                ),
            )

            self.setItem(
                row,
                2,
                QTableWidgetItem(
                    booking.seat.seat_number
                ),
            )

            self.setItem(
                row,
                3,
                QTableWidgetItem(
                    f"{booking.fare_amount}"
                ),
            )

            self.setItem(
                row,
                4,
                QTableWidgetItem(
                    booking.status.value
                ),
            )

            refund_text = (
                f"{booking.refund_amount}"
                if booking.refund_amount is not None
                else ""
            )

            self.setItem(
                row,
                5,
                QTableWidgetItem(refund_text),
            )

            self.setItem(
                row,
                6,
                QTableWidgetItem(
                    booking.booked_at.strftime(
                        "%Y-%m-%d"
                    )
                ),
            )

    def get_selected_booking_id(self):

        row = self.currentRow()

        if row < 0:
            return None

        item = self.item(row, 0)

        if item is None:
            return None

        return item.data(Qt.ItemDataRole.UserRole)

    def clear_bookings(self):

        self.setRowCount(0)
