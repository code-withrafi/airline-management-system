from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
)


class SeatTable(QTableWidget):


    def __init__(
        self,
        parent=None,
    ):

        super().__init__(
            parent
        )


        self.setColumnCount(
            4
        )


        self.setHorizontalHeaderLabels(
            [
                "Seat",
                "Class",
                "Position",
                "Status",
            ]
        )



    def load_seats(
        self,
        seats,
    ):

        self.setRowCount(
            len(seats)
        )


        for row, seat in enumerate(seats):

            self.setItem(
                row,
                0,
                QTableWidgetItem(
                    seat.seat_number
                )
            )


            self.setItem(
                row,
                1,
                QTableWidgetItem(
                    seat.seat_class.value
                )
            )


            self.setItem(
                row,
                2,
                QTableWidgetItem(
                    seat.position.value
                )
            )


            status = (
                "BOOKED"
                if seat.bookings
                else
                "AVAILABLE"
            )


            self.setItem(
                row,
                3,
                QTableWidgetItem(
                    status
                )
            )