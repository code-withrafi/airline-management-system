from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import BookingStatus

from app.repositories import (
    BookingRepository,
    FlightRepository,
    SeatRepository,
)

from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class BookingAvailabilityService:
    """
    Service responsible for validating
    seat availability before booking.
    """


    def __init__(
        self,
        session: Session,
    ):

        self.session = session

        self.booking_repository = (
            BookingRepository(
                session
            )
        )

        self.flight_repository = (
            FlightRepository(
                session
            )
        )

        self.seat_repository = (
            SeatRepository(
                session
            )
        )


    @staticmethod
    def _validate_id(
        value: int,
        name: str,
    ):

        if isinstance(value, bool):

            raise ValidationError(
                f"{name} must be a positive integer."
            )

        if not isinstance(value, int):

            raise ValidationError(
                f"{name} must be a positive integer."
            )

        if value <= 0:

            raise ValidationError(
                f"{name} must be a positive integer."
            )


    def validate_seat_available(
        self,
        *,
        flight_id: int,
        seat_id: int,
    ) -> bool:
        """
        Validate whether a seat can be booked
        for a specific flight.
        """


        self._validate_id(
            flight_id,
            "Flight ID"
        )

        self._validate_id(
            seat_id,
            "Seat ID"
        )


        try:

            flight = (
                self.flight_repository
                .get_by_id(
                    flight_id
                )
            )

            if flight is None:

                raise ResourceNotFoundError(
                    "Flight was not found."
                )


            seat = (
                self.seat_repository
                .get_by_id(
                    seat_id
                )
            )

            if seat is None:

                raise ResourceNotFoundError(
                    "Seat was not found."
                )


            if seat.aircraft_id != flight.aircraft_id:

                raise ResourceConflictError(
                    "Selected seat does not belong to this aircraft."
                )


            booking = (
                self.booking_repository
                .get_by_flight_and_seat(
                    flight_id,
                    seat_id,
                )
            )


            if booking is not None:

                if booking.status != BookingStatus.CANCELLED:

                    raise ResourceConflictError(
                        "Seat is already booked for this flight."
                    )


            return True


        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            raise


        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to validate seat availability."
            ) from exc