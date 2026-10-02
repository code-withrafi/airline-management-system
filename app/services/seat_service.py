from app.repositories import SeatRepository


class SeatService:


    def __init__(
        self,
        session,
    ):

        self.repository = (
            SeatRepository(
                session
            )
        )


    def get_aircraft_seats(
        self,
        aircraft_id: int,
    ):

        return (
            self.repository
            .get_layout(
                aircraft_id
            )
        )