from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


from app.models import (
    Aircraft,
    AircraftStatus,
)


from app.repositories import (
    AircraftRepository,
)


from app.services.exceptions import (
    DatabaseOperationError,
    ResourceNotFoundError,
    ValidationError,
)



class FlightAssignmentService:


    def __init__(
        self,
        session: Session,
    ):

        self.session = session


        self.aircraft_repository = (
            AircraftRepository(
                session
            )
        )



    def get_available_aircraft(
        self,
    ) -> list[Aircraft]:
        """
        Returns aircraft that can be assigned
        to flights.
        """

        try:

            aircraft_list = (
                self.aircraft_repository
                .get_all()
            )


            return [

                aircraft

                for aircraft in aircraft_list

                if aircraft.status
                ==
                AircraftStatus.ACTIVE

            ]


        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve available aircraft."
            ) from exc



    def validate_aircraft_assignment(
        self,
        aircraft_id: int,
    ) -> Aircraft:
        """
        Validate aircraft before assigning
        to a flight.
        """

        aircraft = (
            self.aircraft_repository
            .get_by_id(
                aircraft_id
            )
        )


        if aircraft is None:

            raise ResourceNotFoundError(
                "Aircraft was not found."
            )


        if (
            aircraft.status
            !=
            AircraftStatus.ACTIVE
        ):

            raise ValidationError(
                (
                    "Aircraft cannot be assigned. "
                    f"Current status: "
                    f"{aircraft.status.value}"
                )
            )


        return aircraft



    def assign_aircraft(
        self,
        flight,
        aircraft_id: int,
    ):
        """
        Validate and assign an aircraft to a flight.
        """

        aircraft = (
            self.validate_aircraft_assignment(
                aircraft_id
            )
        )


        if (
            flight.aircraft_id
            ==
            aircraft.id
        ):

            raise ValidationError(
                "Aircraft is already assigned to this flight."
            )


        flight.aircraft_id = (
            aircraft.id
        )


        self.session.flush()


        return flight