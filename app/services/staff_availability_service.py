from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories import FlightStaffRepository
from app.models import FlightStaff

from app.services.exceptions import (
    DatabaseOperationError,
    ValidationError,
)



class StaffAvailabilityService:
    """
    Service responsible for checking whether
    a staff member is available for a flight.
    """



    def __init__(
        self,
        session: Session,
    ):

        self.session = session

        self.flight_staff_repository = (
            FlightStaffRepository(
                session
            )
        )



    @staticmethod
    def _validate_datetime(
        value,
        name: str,
    ):

        if not isinstance(
            value,
            datetime
        ):

            raise ValidationError(
                f"{name} must be a valid datetime."
            )



    @staticmethod
    def _has_overlap(
        existing_start: datetime,
        existing_end: datetime,
        new_start: datetime,
        new_end: datetime,
    ) -> bool:


        return (
            new_start < existing_end
            and
            new_end > existing_start
        )



    def is_staff_available(
        self,
        *,
        staff_id: int,
        departure_time: datetime,
        arrival_time: datetime,
        ignore_flight_id: int | None = None,
    ) -> bool:
        """
        Returns True if staff member can be assigned.
        """


        self._validate_datetime(
            departure_time,
            "Departure time"
        )


        self._validate_datetime(
            arrival_time,
            "Arrival time"
        )


        if departure_time >= arrival_time:

            raise ValidationError(
                "Departure time must be before arrival time."
            )


        try:

            assignments = (
                self._get_staff_assignments(
                    staff_id
                )
            )


            for assignment in assignments:


                flight = assignment.flight


                if (
                    ignore_flight_id
                    and
                    flight.id
                    ==
                    ignore_flight_id
                ):
                    continue



                if self._has_overlap(
                    flight.departure_time,
                    flight.arrival_time,
                    departure_time,
                    arrival_time,
                ):

                    return False



            return True



        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to check staff availability."
            ) from exc



    def validate_staff_available(
        self,
        *,
        staff_id: int,
        departure_time: datetime,
        arrival_time: datetime,
        ignore_flight_id: int | None = None,
    ) -> None:


        available = (
            self.is_staff_available(
                staff_id=staff_id,
                departure_time=departure_time,
                arrival_time=arrival_time,
                ignore_flight_id=ignore_flight_id,
            )
        )


        if not available:

            raise ValidationError(
                "Staff member is already assigned during this time."
            )



    def _get_staff_assignments(
        self,
        staff_id: int,
    ) -> list[FlightStaff]:
        """
        Retrieves all flight assignments
        for a staff member.
        """


        statement = (
            self.session.query(
                FlightStaff
            )
            .filter(
                FlightStaff.staff_id
                ==
                staff_id
            )
        )


        return list(
            statement.all()
        )