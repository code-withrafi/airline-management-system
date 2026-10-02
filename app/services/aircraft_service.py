from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Aircraft, AircraftStatus, UserRole
from app.repositories import AircraftRepository, SeatRepository
from app.services.application import application_context
from app.services.exceptions import (
    AuthorizationError,
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.seat_generator import SeatGenerator
from app.services.seat_management_service import (
    SeatManagementService,
)


class AircraftService:
    def __init__(
        self,
        session: Session,
    ):

        self.session = session

        self.repository = (
            AircraftRepository(
                session
            )
        )

        self.seat_repository = (
            SeatRepository(
                session
            )
        )

    @staticmethod
    def _require_admin() -> None:
        try:
            application_context.session.require_role(
                UserRole.ADMIN
            )
        except PermissionError as exc:
            raise AuthorizationError(
                "Only administrators can manage aircraft."
            ) from exc

    @staticmethod
    def _normalize_registration_number(
        registration_number: str,
    ) -> str:
        if not isinstance(registration_number, str):
            raise ValidationError(
                "Registration number must be text."
            )

        value = registration_number.strip().upper()

        if not value:
            raise ValidationError(
                "Registration number is required."
            )

        if len(value) > 20:
            raise ValidationError(
                "Registration number must not exceed 20 characters."
            )

        return value

    @staticmethod
    def _normalize_manufacturer(manufacturer: str) -> str:
        if not isinstance(manufacturer, str):
            raise ValidationError(
                "Aircraft manufacturer must be text."
            )

        value = manufacturer.strip()

        if not value:
            raise ValidationError(
                "Aircraft manufacturer is required."
            )

        if len(value) > 100:
            raise ValidationError(
                "Aircraft manufacturer must not exceed 100 characters."
            )

        return value

    @staticmethod
    def _normalize_model(model: str) -> str:
        if not isinstance(model, str):
            raise ValidationError(
                "Aircraft model must be text."
            )

        value = model.strip()

        if not value:
            raise ValidationError(
                "Aircraft model is required."
            )

        if len(value) > 100:
            raise ValidationError(
                "Aircraft model must not exceed 100 characters."
            )

        return value

    @staticmethod
    def _validate_seat_capacity(seat_capacity: int) -> int:
        if isinstance(seat_capacity, bool):
            raise ValidationError(
                "Aircraft seat capacity must be a positive integer."
            )

        if not isinstance(seat_capacity, int):
            raise ValidationError(
                "Aircraft seat capacity must be a positive integer."
            )

        if seat_capacity <= 0:
            raise ValidationError(
                "Aircraft seat capacity must be greater than zero."
            )

        if seat_capacity > 1000:
            raise ValidationError(
                "Aircraft seat capacity must not exceed 1000 seats."
            )

        return seat_capacity

    @staticmethod
    def _validate_status(status) -> AircraftStatus:
        if isinstance(status, AircraftStatus):
            return status

        try:
            return AircraftStatus(status)
        except (ValueError, TypeError) as exc:
            raise ValidationError(
                "Invalid aircraft status."
            ) from exc

    @staticmethod
    def _validate_aircraft_id(aircraft_id: int) -> None:
        if isinstance(aircraft_id, bool):
            raise ValidationError(
                "Aircraft ID must be a positive integer."
            )

        if not isinstance(aircraft_id, int):
            raise ValidationError(
                "Aircraft ID must be a positive integer."
            )

        if aircraft_id <= 0:
            raise ValidationError(
                "Aircraft ID must be a positive integer."
            )

    def _generate_aircraft_seats(
        self,
        aircraft,
    ):
        """
        Generate seats after aircraft creation.
        """

        seats = SeatGenerator.generate(
            aircraft.seat_capacity
        )

        for seat_data in seats:

            self.seat_repository.create(
                aircraft_id=aircraft.id,
                **seat_data,
            )

    def get_all_aircraft(self) -> list[Aircraft]:
        self._require_admin()

        try:
            return self.repository.get_all()
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to retrieve aircraft."
            ) from exc

    def get_aircraft_by_id(self, aircraft_id: int) -> Aircraft:
        self._require_admin()
        self._validate_aircraft_id(aircraft_id)

        try:
            aircraft = self.repository.get_by_id(aircraft_id)
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to retrieve aircraft."
            ) from exc

        if aircraft is None:
            raise ResourceNotFoundError(
                "Aircraft was not found."
            )

        return aircraft

    def search_aircraft(self, search_text: str) -> list[Aircraft]:
        self._require_admin()

        if not isinstance(search_text, str):
            raise ValidationError(
                "Search text must be text."
            )

        try:
            return self.repository.search(search_text)
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to search aircraft."
            ) from exc

    def count_aircraft(self) -> int:
        self._require_admin()

        try:
            return self.repository.count()
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to count aircraft."
            ) from exc

    def create_aircraft(
        self,
        *,
        registration_number: str,
        manufacturer: str,
        model: str,
        seat_capacity: int,
        status=AircraftStatus.ACTIVE,
    ) -> Aircraft:
        self._require_admin()

        registration_number = (
            self._normalize_registration_number(
                registration_number
            )
        )
        manufacturer = self._normalize_manufacturer(manufacturer)
        model = self._normalize_model(model)
        seat_capacity = self._validate_seat_capacity(seat_capacity)
        status = self._validate_status(status)

        try:
            existing = (
                self.repository
                .get_by_registration_number(
                    registration_number
                )
            )

            if existing is not None:
                raise ResourceConflictError(
                    "An aircraft with this registration number already exists."
                )

            aircraft = self.repository.create(
                registration_number=registration_number,
                manufacturer=manufacturer,
                model=model,
                seat_capacity=seat_capacity,
                status=status,
            )

            self.session.flush()

            self._generate_aircraft_seats(
                aircraft
            )

            self.session.commit()

            return aircraft

        except ResourceConflictError:
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "An aircraft with this registration number already exists."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to create aircraft."
            ) from exc

    def update_aircraft(
        self,
        aircraft_id: int,
        *,
        registration_number: str,
        manufacturer: str,
        model: str,
        seat_capacity: int,
        status,
    ) -> Aircraft:
        self._require_admin()
        self._validate_aircraft_id(aircraft_id)

        registration_number = (
            self._normalize_registration_number(
                registration_number
            )
        )
        manufacturer = self._normalize_manufacturer(manufacturer)
        model = self._normalize_model(model)
        seat_capacity = self._validate_seat_capacity(seat_capacity)
        status = self._validate_status(status)

        try:
            aircraft = self.repository.get_by_id(aircraft_id)

            if aircraft is None:
                raise ResourceNotFoundError(
                    "Aircraft was not found."
                )

            existing = (
                self.repository
                .get_by_registration_number(
                    registration_number
                )
            )

            if existing is not None and existing.id != aircraft.id:
                raise ResourceConflictError(
                    "An aircraft with this registration number already exists."
                )

            old_capacity = aircraft.seat_capacity

            aircraft = self.repository.update(
                aircraft,
                registration_number=registration_number,
                manufacturer=manufacturer,
                model=model,
                seat_capacity=seat_capacity,
                status=status,
            )

            if old_capacity != seat_capacity:

                self.session.flush()

                seat_management = (
                    SeatManagementService(
                        self.session
                    )
                )

                seat_management.synchronize_capacity(
                    aircraft,
                    seat_capacity,
                )

            self.session.commit()

            return aircraft

        except (
            ResourceNotFoundError,
            ResourceConflictError,
        ):
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "The aircraft could not be updated because of a database conflict."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to update aircraft."
            ) from exc

    def update_aircraft_status(
        self,
        aircraft_id: int,
        status,
    ) -> Aircraft:
        self._require_admin()
        self._validate_aircraft_id(aircraft_id)
        status = self._validate_status(status)

        try:
            aircraft = self.repository.get_by_id(aircraft_id)

            if aircraft is None:
                raise ResourceNotFoundError(
                    "Aircraft was not found."
                )

            aircraft.status = status
            self.session.commit()

            return aircraft

        except ResourceNotFoundError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to update aircraft status."
            ) from exc

    def delete_aircraft(self, aircraft_id: int) -> None:
        self._require_admin()
        self._validate_aircraft_id(aircraft_id)

        try:
            aircraft = self.repository.get_by_id(aircraft_id)

            if aircraft is None:
                raise ResourceNotFoundError(
                    "Aircraft was not found."
                )

            self.repository.delete(aircraft)
            self.session.commit()

        except ResourceNotFoundError:
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "This aircraft cannot be deleted because it is being used by an existing flight."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to delete aircraft."
            ) from exc