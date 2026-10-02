from app.models import Seat
from app.repositories import SeatRepository
from app.services.seat_generator import SeatGenerator


class SeatManagementService:


    def __init__(
        self,
        session,
    ):

        self.session = session

        self.repository = (
            SeatRepository(
                session
            )
        )


    def synchronize_capacity(
        self,
        aircraft,
        new_capacity: int,
    ):

        current_count = (
            self.repository
            .count_by_aircraft(
                aircraft.id
            )
        )


        if new_capacity > current_count:

            self._add_seats(
                aircraft,
                current_count,
                new_capacity,
            )


        elif new_capacity < current_count:

            self._remove_unused_seats(
                aircraft,
                new_capacity,
            )



    def _add_seats(
        self,
        aircraft,
        current_count,
        new_capacity,
    ):

        generated = SeatGenerator.generate(
            new_capacity
        )


        existing_numbers = {
            seat.seat_number
            for seat in aircraft.seats
        }


        for seat_data in generated:

            if (
                seat_data["seat_number"]
                not in existing_numbers
            ):

                self.repository.create(
                    aircraft_id=aircraft.id,
                    **seat_data,
                )



    def _remove_unused_seats(
        self,
        aircraft,
        new_capacity,
    ):

        seats = sorted(
            aircraft.seats,
            key=lambda x: x.row_number,
            reverse=True,
        )


        removable = (
            len(seats)
            -
            new_capacity
        )


        removed = 0


        for seat in seats:

            if removed >= removable:
                break


            if not seat.bookings:

                self.session.delete(
                    seat
                )

                removed += 1