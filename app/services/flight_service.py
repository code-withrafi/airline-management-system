from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    Aircraft,
    AircraftStatus,
    UserRole,
)
from app.models.flight import (
    Flight,
    FlightStatus,
)
from app.models.route import Route
from app.repositories import (
    AircraftRepository,
    FlightRepository,
)
from app.services.application import application_context
from app.services.flight_assignment_service import (
    FlightAssignmentService,
)
from app.services.exceptions import (
    AuthorizationError,
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.validators.flight_status_validator import (
    FlightStatusValidator,
)


class FlightService:
    """Service layer for flight management."""

    def __init__(self, session: Session):
        self.session = session
        self.repository = FlightRepository(session)
        self.aircraft_repository = AircraftRepository(session)
        self.assignment_service = FlightAssignmentService(session)

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    @staticmethod
    def _require_admin() -> None:
        try:
            application_context.session.require_role(
                UserRole.ADMIN
            )
        except PermissionError as exc:
            raise AuthorizationError(
                "Only administrators can manage flights."
            ) from exc

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_flight_number(
        flight_number: str,
    ) -> str:
        if not isinstance(flight_number, str):
            raise ValidationError(
                "Flight number must be text."
            )

        value = flight_number.strip().upper()

        if not value:
            raise ValidationError(
                "Flight number is required."
            )

        if len(value) < 3:
            raise ValidationError(
                "Flight number is too short."
            )

        if len(value) > 20:
            raise ValidationError(
                "Flight number must not exceed 20 characters."
            )

        return value

    @staticmethod
    def _validate_times(
        departure_time,
        arrival_time,
    ) -> None:
        if not isinstance(departure_time, datetime):
            raise ValidationError(
                "Departure time must be a valid datetime."
            )

        if not isinstance(arrival_time, datetime):
            raise ValidationError(
                "Arrival time must be a valid datetime."
            )

        if departure_time >= arrival_time:
            raise ValidationError(
                "Arrival time must be after departure time."
            )

    @staticmethod
    def _validate_base_fare(
        base_fare,
    ) -> Decimal:
        if isinstance(base_fare, bool):
            raise ValidationError(
                "Base fare must be a positive number."
            )

        if not isinstance(base_fare, (int, float, Decimal)):
            raise ValidationError(
                "Base fare must be a positive number."
            )

        value = Decimal(str(base_fare))

        if value < 0:
            raise ValidationError(
                "Base fare cannot be negative."
            )

        return value

    @staticmethod
    def _validate_status(
        status,
    ) -> FlightStatus:
        if isinstance(status, FlightStatus):
            return status

        try:
            return FlightStatus(status)
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                "Invalid flight status."
            ) from exc

    @staticmethod
    def _validate_flight_id(
        flight_id: int,
    ) -> None:
        if isinstance(flight_id, bool):
            raise ValidationError(
                "Flight ID must be a positive integer."
            )

        if not isinstance(flight_id, int):
            raise ValidationError(
                "Flight ID must be a positive integer."
            )

        if flight_id <= 0:
            raise ValidationError(
                "Flight ID must be a positive integer."
            )

    def _validate_aircraft_for_flight(
        self,
        aircraft_id: int,
    ) -> Aircraft:
        if not isinstance(aircraft_id, int) or aircraft_id <= 0:
            raise ValidationError(
                "Aircraft ID must be a positive integer."
            )

        aircraft = self.aircraft_repository.get_by_id(
            aircraft_id
        )

        if aircraft is None:
            raise ResourceNotFoundError(
                "Aircraft was not found."
            )

        if aircraft.status != AircraftStatus.ACTIVE:
            raise ResourceConflictError(
                f"Aircraft '{aircraft.registration_number}' "
                f"is not available (status: {aircraft.status.value})."
            )

        return aircraft

    def _validate_route_for_flight(
        self,
        route_id: int,
    ) -> Route:
        if not isinstance(route_id, int) or route_id <= 0:
            raise ValidationError(
                "Route ID must be a positive integer."
            )

        route = self.session.get(Route, route_id)

        if route is None:
            raise ResourceNotFoundError(
                "Route was not found."
            )

        if not route.is_active:
            raise ResourceConflictError(
                "This route is inactive and cannot be used "
                "for new flights."
            )

        return route

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all_flights(self) -> list[Flight]:
        self._require_admin()

        try:
            return self.repository.get_all()
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to retrieve flights."
            ) from exc

    def get_flight(
        self,
        flight_id: int,
    ) -> Flight:
        self._require_admin()
        self._validate_flight_id(flight_id)

        try:
            flight = self.repository.get_by_id(flight_id)
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to retrieve flight."
            ) from exc

        if flight is None:
            raise ResourceNotFoundError(
                "Flight was not found."
            )

        return flight

    def search_flights(
        self,
        *,
        keyword: str = "",
        status=None,
        route_id=None,
        aircraft_id=None,
        start_date=None,
        end_date=None,
    ) -> list[Flight]:
        self._require_admin()

        if keyword is not None and not isinstance(keyword, str):
            raise ValidationError(
                "Search keyword must be text."
            )

        try:
            return self.repository.search(
                keyword=keyword or "",
                status=status,
                route_id=route_id,
                aircraft_id=aircraft_id,
                start_date=start_date,
                end_date=end_date,
            )
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to search flights."
            ) from exc

    def count_flights(self) -> int:
        self._require_admin()

        try:
            return self.repository.count()
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to count flights."
            ) from exc

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_flight(
        self,
        *,
        flight_number: str,
        route_id: int,
        aircraft_id: int,
        departure_time,
        arrival_time,
        base_fare,
        boarding_gate=None,
    ) -> Flight:
        self._require_admin()

        flight_number = self._normalize_flight_number(
            flight_number
        )
        self._validate_times(departure_time, arrival_time)
        base_fare = self._validate_base_fare(base_fare)

        self._validate_aircraft_for_flight(aircraft_id)
        self._validate_route_for_flight(route_id)

        try:
            # A flight number may repeat across different days
            # (e.g. daily SN101). It must only be unique per
            # exact departure datetime.
            if self.repository.exists_by_flight_number_and_time(
                flight_number,
                departure_time,
            ):
                raise ResourceConflictError(
                    f"Flight '{flight_number}' is already "
                    f"scheduled for "
                    f"{departure_time:%Y-%m-%d %H:%M}."
                )

            flight = self.repository.create(
                flight_number=flight_number,
                route_id=route_id,
                aircraft_id=aircraft_id,
                departure_time=departure_time,
                arrival_time=arrival_time,
                base_fare=base_fare,
                status=FlightStatus.SCHEDULED,
                boarding_gate=boarding_gate,
            )

            self.session.commit()

            return flight

        except ResourceConflictError:
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "The flight could not be created because of "
                "a database conflict."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to create flight."
            ) from exc

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_flight(
        self,
        flight_id: int,
        *,
        flight_number=None,
        route_id=None,
        aircraft_id=None,
        departure_time=None,
        arrival_time=None,
        base_fare=None,
        boarding_gate=None,
    ) -> Flight:
        self._require_admin()
        self._validate_flight_id(flight_id)

        try:
            flight = self.repository.get_by_id(flight_id)

            if flight is None:
                raise ResourceNotFoundError(
                    "Flight was not found."
                )

            # ---- resolve target values up front ----
            target_number = (
                self._normalize_flight_number(flight_number)
                if flight_number is not None
                else flight.flight_number
            )

            target_departure = (
                departure_time
                if departure_time is not None
                else flight.departure_time
            )

            target_arrival = (
                arrival_time
                if arrival_time is not None
                else flight.arrival_time
            )

            self._validate_times(
                target_departure,
                target_arrival,
            )

            # ---- uniqueness: number + exact departure datetime ----
            number_changed = (
                target_number != flight.flight_number
            )
            time_changed = (
                target_departure != flight.departure_time
            )

            if number_changed or time_changed:
                if self.repository.exists_by_flight_number_and_time(
                    target_number,
                    target_departure,
                    exclude_id=flight.id,
                ):
                    raise ResourceConflictError(
                        f"Flight '{target_number}' is already "
                        f"scheduled for "
                        f"{target_departure:%Y-%m-%d %H:%M}."
                    )

            # ---- apply ----
            flight.flight_number = target_number
            flight.departure_time = target_departure
            flight.arrival_time = target_arrival

            if aircraft_id is not None:
                self._validate_aircraft_for_flight(aircraft_id)
                flight.aircraft_id = aircraft_id

            if route_id is not None:
                self._validate_route_for_flight(route_id)
                flight.route_id = route_id

            if base_fare is not None:
                flight.base_fare = self._validate_base_fare(
                    base_fare
                )

            if boarding_gate is not None:
                flight.boarding_gate = boarding_gate

            self.repository.update(flight)
            self.session.commit()

            return flight

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
                "The flight could not be updated because of "
                "a database conflict."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to update flight."
            ) from exc

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def update_status(
        self,
        flight_id: int,
        status,
    ) -> Flight:
        self._require_admin()
        self._validate_flight_id(flight_id)
        status = self._validate_status(status)

        try:
            flight = self.repository.get_by_id(flight_id)

            if flight is None:
                raise ResourceNotFoundError(
                    "Flight was not found."
                )

            if flight.status == status:
                return flight

            FlightStatusValidator.validate_transition(
                flight.status,
                status,
            )

            flight.status = status
            self.session.commit()

            return flight

        except (
            ResourceNotFoundError,
            ValidationError,
        ):
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to update flight status."
            ) from exc

    def change_aircraft(
        self,
        flight_id: int,
        aircraft_id: int,
    ) -> Flight:
        """Change the aircraft assigned to an existing flight."""

        self._require_admin()
        self._validate_flight_id(flight_id)

        flight = self.repository.get_by_id(flight_id)

        if flight is None:
            raise ResourceNotFoundError("Flight was not found.")

        self.assignment_service.assign_aircraft(
            flight,
            aircraft_id,
        )

        self.session.commit()

        return flight

    def cancel_flight(
        self,
        flight_id: int,
    ) -> Flight:
        """Convenience wrapper for cancelling a flight."""
        return self.update_status(
            flight_id,
            FlightStatus.CANCELLED,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_flight(
        self,
        flight_id: int,
    ) -> None:
        self._require_admin()
        self._validate_flight_id(flight_id)

        try:
            flight = self.repository.get_by_id(flight_id)

            if flight is None:
                raise ResourceNotFoundError(
                    "Flight was not found."
                )

            self.repository.delete(flight)
            self.session.commit()

        except ResourceNotFoundError:
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "This flight cannot be deleted because it has "
                "existing bookings."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to delete flight."
            ) from exc