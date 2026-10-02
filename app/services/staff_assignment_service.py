from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from sqlalchemy.orm import Session


from app.models import (
    AssignmentRole,
    FlightStaff,
    Staff,
)

from app.repositories import (
    FlightRepository,
    FlightStaffRepository,
    StaffRepository,
)

from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)

from app.services.staff_availability_service import (
    StaffAvailabilityService,
)


class StaffAssignmentService:
    """
    Business service responsible for assigning
    staff members to flights.
    """

    def __init__(
        self,
        session: Session,
    ):

        self.session = session

        self.staff_repository = (
            StaffRepository(
                session
            )
        )

        self.flight_repository = (
            FlightRepository(
                session
            )
        )

        self.flight_staff_repository = (
            FlightStaffRepository(
                session
            )
        )

        self.availability_service = (
            StaffAvailabilityService(
                session
            )
        )

    @staticmethod
    def _validate_id(
        value: int,
        name: str,
    ) -> None:

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

    @staticmethod
    def _validate_role(
        role,
    ) -> AssignmentRole:

        if isinstance(
            role,
            AssignmentRole
        ):

            return role

        try:

            return AssignmentRole(
                role
            )

        except (
            ValueError,
            TypeError,
        ) as exc:

            raise ValidationError(
                "Invalid assignment role."
            ) from exc

    def get_flight_crew(
        self,
        flight_id: int,
    ) -> list[FlightStaff]:

        self._validate_id(
            flight_id,
            "Flight ID"
        )

        try:

            return (
                self.flight_staff_repository
                .get_by_flight(
                    flight_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve flight crew."
            ) from exc

    def assign_staff(
        self,
        *,
        flight_id: int,
        staff_id: int,
        assigned_role,
    ) -> FlightStaff:

        self._validate_id(
            flight_id,
            "Flight ID"
        )

        self._validate_id(
            staff_id,
            "Staff ID"
        )

        assigned_role = (
            self._validate_role(
                assigned_role
            )
        )

        try:

            staff = (
                self.staff_repository
                .get_by_id(
                    staff_id
                )
            )

            if staff is None:

                raise ResourceNotFoundError(
                    "Staff member was not found."
                )

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

            existing = (
                self.flight_staff_repository
                .get_by_flight_and_staff(
                    flight_id,
                    staff_id,
                )
            )

            if existing is not None:

                raise ResourceConflictError(
                    "Staff member is already assigned to this flight."
                )

            # Time-overlap check
            self.availability_service.validate_staff_available(
                staff_id=staff_id,
                departure_time=flight.departure_time,
                arrival_time=flight.arrival_time,
                ignore_flight_id=flight_id,
            )

            assignment = (
                self.flight_staff_repository
                .create(
                    flight_id=flight_id,
                    staff_id=staff_id,
                    assigned_role=assigned_role,
                )
            )

            self.session.commit()

            return assignment

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            self.session.rollback()

            raise

        except IntegrityError as exc:

            self.session.rollback()

            raise ResourceConflictError(
                "Staff assignment already exists."
            ) from exc

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to assign staff."
            ) from exc

    def remove_staff(
        self,
        *,
        flight_id: int,
        staff_id: int,
    ) -> None:

        self._validate_id(
            flight_id,
            "Flight ID"
        )

        self._validate_id(
            staff_id,
            "Staff ID"
        )

        try:

            assignment = (
                self.flight_staff_repository
                .get_by_flight_and_staff(
                    flight_id,
                    staff_id,
                )
            )

            if assignment is None:

                raise ResourceNotFoundError(
                    "Staff assignment was not found."
                )

            self.flight_staff_repository.delete(
                assignment
            )

            self.session.commit()

        except ResourceNotFoundError:

            self.session.rollback()

            raise

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to remove staff assignment."
            ) from exc