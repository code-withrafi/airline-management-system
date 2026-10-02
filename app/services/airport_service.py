from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Airport, UserRole
from app.repositories.airport_repository import AirportRepository
from app.services.application import application_context
from app.services.exceptions import (
    AuthorizationError,
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class AirportService:
    """
    Service layer for administrator airport management.

    This class contains business rules, validation, authorization,
    and transaction handling for airport operations.
    """

    def __init__(self, session: Session):
        self.session = session
        self.repository = AirportRepository(session)

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    def _require_admin(self) -> None:
        """
        Ensure that the current user is an administrator.
        """

        try:
            application_context.session.require_role(
                UserRole.ADMIN
            )
        except PermissionError as error:
            raise AuthorizationError(
                "Administrator permission is required."
            ) from error

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_code(
        value: str,
        field_name: str,
        length: int,
    ) -> str:
        """
        Normalize and validate an airport code.
        """

        if value is None:
            raise ValidationError(
                f"{field_name} is required."
            )

        normalized = value.strip().upper()

        if not normalized:
            raise ValidationError(
                f"{field_name} is required."
            )

        if len(normalized) != length:
            raise ValidationError(
                f"{field_name} must contain exactly {length} characters."
            )

        if not normalized.isalpha():
            raise ValidationError(
                f"{field_name} must contain letters only."
            )

        return normalized

    @staticmethod
    def _normalize_text(
        value: str,
        field_name: str,
    ) -> str:
        """
        Normalize and validate a required text field.
        """

        if value is None:
            raise ValidationError(
                f"{field_name} is required."
            )

        normalized = value.strip()

        if not normalized:
            raise ValidationError(
                f"{field_name} is required."
            )

        return normalized

    def _validate_airport_data(
        self,
        *,
        iata_code: str,
        icao_code: str,
        name: str,
        city: str,
        country: str,
        timezone: str,
    ) -> dict[str, str]:
        """
        Validate and normalize airport data.
        """

        normalized_iata = self._normalize_code(
            iata_code,
            "IATA code",
            3,
        )

        normalized_icao = self._normalize_code(
            icao_code,
            "ICAO code",
            4,
        )

        normalized_name = self._normalize_text(
            name,
            "Airport name",
        )

        normalized_city = self._normalize_text(
            city,
            "City",
        )

        normalized_country = self._normalize_text(
            country,
            "Country",
        )

        normalized_timezone = self._normalize_text(
            timezone,
            "Timezone",
        )

        return {
            "iata_code": normalized_iata,
            "icao_code": normalized_icao,
            "name": normalized_name,
            "city": normalized_city,
            "country": normalized_country,
            "timezone": normalized_timezone,
        }

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_all_airports(self) -> list[Airport]:
        """
        Return all airports.

        Reading airport data is allowed for administrators.
        """

        self._require_admin()

        try:
            return self.repository.get_all()

        except SQLAlchemyError as error:
            raise DatabaseOperationError(
                "Unable to retrieve airports."
            ) from error

    def get_airport(
        self,
        airport_id: int,
    ) -> Airport:
        """
        Return an airport by ID.
        """

        self._require_admin()

        if airport_id is None:
            raise ValidationError(
                "Airport ID is required."
            )

        try:
            airport = self.repository.get_by_id(
                airport_id
            )

            if airport is None:
                raise ResourceNotFoundError(
                    "Airport was not found."
                )

            return airport

        except ResourceNotFoundError:
            raise

        except SQLAlchemyError as error:
            raise DatabaseOperationError(
                "Unable to retrieve the airport."
            ) from error

    def search_airports(
        self,
        search_text: str,
    ) -> list[Airport]:
        """
        Search airports by code, name, city, or country.
        """

        self._require_admin()

        search_text = (
            search_text.strip()
            if search_text is not None
            else ""
        )

        try:
            return self.repository.search(
                search_text
            )

        except SQLAlchemyError as error:
            raise DatabaseOperationError(
                "Unable to search airports."
            ) from error

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_airport(
        self,
        *,
        iata_code: str,
        icao_code: str,
        name: str,
        city: str,
        country: str,
        timezone: str,
    ) -> Airport:
        """
        Create a new airport.
        """

        self._require_admin()

        data = self._validate_airport_data(
            iata_code=iata_code,
            icao_code=icao_code,
            name=name,
            city=city,
            country=country,
            timezone=timezone,
        )

        try:
            existing_iata = (
                self.repository.get_by_iata_code(
                    data["iata_code"]
                )
            )

            if existing_iata is not None:
                raise ResourceConflictError(
                    f"IATA code '{data['iata_code']}' "
                    "is already registered."
                )

            existing_icao = (
                self.repository.get_by_icao_code(
                    data["icao_code"]
                )
            )

            if existing_icao is not None:
                raise ResourceConflictError(
                    f"ICAO code '{data['icao_code']}' "
                    "is already registered."
                )

            airport = self.repository.create(
                **data
            )

            self.session.commit()

            return airport

        except (
            ValidationError,
            ResourceConflictError,
        ):
            self.session.rollback()
            raise

        except IntegrityError as error:
            self.session.rollback()

            raise ResourceConflictError(
                "The airport could not be created because "
                "one or more airport codes already exist."
            ) from error

        except SQLAlchemyError as error:
            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to create the airport."
            ) from error

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_airport(
        self,
        airport_id: int,
        *,
        iata_code: str,
        icao_code: str,
        name: str,
        city: str,
        country: str,
        timezone: str,
    ) -> Airport:
        """
        Update an existing airport.
        """

        self._require_admin()

        if airport_id is None:
            raise ValidationError(
                "Airport ID is required."
            )

        data = self._validate_airport_data(
            iata_code=iata_code,
            icao_code=icao_code,
            name=name,
            city=city,
            country=country,
            timezone=timezone,
        )

        try:
            airport = self.repository.get_by_id(
                airport_id
            )

            if airport is None:
                raise ResourceNotFoundError(
                    "Airport was not found."
                )

            existing_iata = (
                self.repository.get_by_iata_code(
                    data["iata_code"]
                )
            )

            if (
                existing_iata is not None
                and existing_iata.id != airport.id
            ):
                raise ResourceConflictError(
                    f"IATA code '{data['iata_code']}' "
                    "is already registered."
                )

            existing_icao = (
                self.repository.get_by_icao_code(
                    data["icao_code"]
                )
            )

            if (
                existing_icao is not None
                and existing_icao.id != airport.id
            ):
                raise ResourceConflictError(
                    f"ICAO code '{data['icao_code']}' "
                    "is already registered."
                )

            updated_airport = self.repository.update(
                airport,
                **data,
            )

            self.session.commit()

            return updated_airport

        except (
            ValidationError,
            ResourceNotFoundError,
            ResourceConflictError,
        ):
            self.session.rollback()
            raise

        except IntegrityError as error:
            self.session.rollback()

            raise ResourceConflictError(
                "The airport could not be updated because "
                "one or more airport codes already exist."
            ) from error

        except SQLAlchemyError as error:
            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to update the airport."
            ) from error

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_airport(
        self,
        airport_id: int,
    ) -> None:
        """
        Delete an airport.

        PostgreSQL foreign-key restrictions may prevent deletion
        when the airport is referenced by routes.
        """

        self._require_admin()

        if airport_id is None:
            raise ValidationError(
                "Airport ID is required."
            )

        try:
            airport = self.repository.get_by_id(
                airport_id
            )

            if airport is None:
                raise ResourceNotFoundError(
                    "Airport was not found."
                )

            self.repository.delete(airport)

            self.session.commit()

        except (
            ValidationError,
            ResourceNotFoundError,
        ):
            self.session.rollback()
            raise

        except IntegrityError as error:
            self.session.rollback()

            raise ResourceConflictError(
                "This airport cannot be deleted because "
                "it is being used by an existing route."
            ) from error

        except SQLAlchemyError as error:
            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to delete the airport."
            ) from error

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_airport_count(self) -> int:
        """
        Return the number of registered airports.
        """

        self._require_admin()

        try:
            return self.repository.count()

        except SQLAlchemyError as error:
            raise DatabaseOperationError(
                "Unable to retrieve the airport count."
            ) from error