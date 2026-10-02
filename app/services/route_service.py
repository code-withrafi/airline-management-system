from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Airport, Route, UserRole
from app.repositories import AirportRepository, RouteRepository
from app.services.application import application_context
from app.services.exceptions import (
    AuthorizationError,
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class RouteService:
    """
    Service layer for administrator route management.
    """

    MIN_DISTANCE_KM = 1
    MAX_DISTANCE_KM = 20000
    MIN_DURATION_MINUTES = 1
    MAX_DURATION_MINUTES = 1440  # 24 hours

    def __init__(self, session: Session):
        self.session = session
        self.repository = RouteRepository(session)
        self.airport_repository = AirportRepository(session)

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    def _require_admin(self) -> None:
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
    def _validate_positive_int(
        value,
        field_name: str,
        minimum: int,
        maximum: int,
    ) -> int:
        if isinstance(value, bool):
            raise ValidationError(
                f"{field_name} must be a positive integer."
            )

        if not isinstance(value, int):
            raise ValidationError(
                f"{field_name} must be a positive integer."
            )

        if value < minimum or value > maximum:
            raise ValidationError(
                f"{field_name} must be between "
                f"{minimum} and {maximum}."
            )

        return value

    @staticmethod
    def _validate_airport_id(
        airport_id,
        field_name: str,
    ) -> int:
        if isinstance(airport_id, bool):
            raise ValidationError(
                f"{field_name} must be a positive integer."
            )

        if not isinstance(airport_id, int):
            raise ValidationError(
                f"{field_name} must be a positive integer."
            )

        if airport_id <= 0:
            raise ValidationError(
                f"{field_name} must be a positive integer."
            )

        return airport_id

    def _validate_route_data(
        self,
        *,
        origin_airport_id: int,
        destination_airport_id: int,
        distance_km: int,
        estimated_duration_minutes: int,
    ) -> dict:
        origin_id = self._validate_airport_id(
            origin_airport_id,
            "Origin airport ID",
        )
        destination_id = self._validate_airport_id(
            destination_airport_id,
            "Destination airport ID",
        )

        if origin_id == destination_id:
            raise ValidationError(
                "Origin and destination airports must be different."
            )

        distance = self._validate_positive_int(
            distance_km,
            "Distance (km)",
            self.MIN_DISTANCE_KM,
            self.MAX_DISTANCE_KM,
        )

        duration = self._validate_positive_int(
            estimated_duration_minutes,
            "Estimated duration (minutes)",
            self.MIN_DURATION_MINUTES,
            self.MAX_DURATION_MINUTES,
        )

        return {
            "origin_airport_id": origin_id,
            "destination_airport_id": destination_id,
            "distance_km": distance,
            "estimated_duration_minutes": duration,
        }

    def _require_airport_exists(self, airport_id: int) -> Airport:
        airport = self.airport_repository.get_by_id(airport_id)

        if airport is None:
            raise ResourceNotFoundError(
                f"Airport with ID {airport_id} was not found."
            )

        return airport

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_all_routes(self) -> list[Route]:
        self._require_admin()

        try:
            return self.repository.get_all()
        except SQLAlchemyError as error:
            raise DatabaseOperationError(
                "Unable to retrieve routes."
            ) from error

    def get_route(self, route_id: int) -> Route:
        self._require_admin()

        if route_id is None:
            raise ValidationError("Route ID is required.")

        try:
            route = self.repository.get_by_id(route_id)

            if route is None:
                raise ResourceNotFoundError(
                    "Route was not found."
                )

            return route

        except ResourceNotFoundError:
            raise

        except SQLAlchemyError as error:
            raise DatabaseOperationError(
                "Unable to retrieve the route."
            ) from error

    def search_routes(self, search_text: str) -> list[Route]:
        self._require_admin()

        search_text = (
            search_text.strip()
            if search_text is not None
            else ""
        )

        try:
            return self.repository.search(search_text)
        except SQLAlchemyError as error:
            raise DatabaseOperationError(
                "Unable to search routes."
            ) from error

    def get_route_count(self) -> int:
        self._require_admin()

        try:
            return self.repository.count()
        except SQLAlchemyError as error:
            raise DatabaseOperationError(
                "Unable to retrieve the route count."
            ) from error

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_route(
        self,
        *,
        origin_airport_id: int,
        destination_airport_id: int,
        distance_km: int,
        estimated_duration_minutes: int,
        is_active: bool = True,
    ) -> Route:
        self._require_admin()

        data = self._validate_route_data(
            origin_airport_id=origin_airport_id,
            destination_airport_id=destination_airport_id,
            distance_km=distance_km,
            estimated_duration_minutes=estimated_duration_minutes,
        )

        try:
            # Verify both airports exist
            self._require_airport_exists(data["origin_airport_id"])
            self._require_airport_exists(data["destination_airport_id"])

            # Reject duplicate (origin, destination)
            existing = self.repository.get_by_airports(
                data["origin_airport_id"],
                data["destination_airport_id"],
            )

            if existing is not None:
                raise ResourceConflictError(
                    "A route between these two airports already exists."
                )

            route = self.repository.create(
                origin_airport_id=data["origin_airport_id"],
                destination_airport_id=data["destination_airport_id"],
                distance_km=data["distance_km"],
                estimated_duration_minutes=data["estimated_duration_minutes"],
                is_active=bool(is_active),
            )

            self.session.commit()

            return route

        except (
            ValidationError,
            ResourceConflictError,
            ResourceNotFoundError,
        ):
            self.session.rollback()
            raise

        except IntegrityError as error:
            self.session.rollback()
            raise ResourceConflictError(
                "The route could not be created because of a database conflict."
            ) from error

        except SQLAlchemyError as error:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to create the route."
            ) from error

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_route(
        self,
        route_id: int,
        *,
        origin_airport_id: int,
        destination_airport_id: int,
        distance_km: int,
        estimated_duration_minutes: int,
        is_active: bool,
    ) -> Route:
        self._require_admin()

        if route_id is None:
            raise ValidationError("Route ID is required.")

        data = self._validate_route_data(
            origin_airport_id=origin_airport_id,
            destination_airport_id=destination_airport_id,
            distance_km=distance_km,
            estimated_duration_minutes=estimated_duration_minutes,
        )

        try:
            route = self.repository.get_by_id(route_id)

            if route is None:
                raise ResourceNotFoundError(
                    "Route was not found."
                )

            self._require_airport_exists(data["origin_airport_id"])
            self._require_airport_exists(data["destination_airport_id"])

            existing = self.repository.get_by_airports(
                data["origin_airport_id"],
                data["destination_airport_id"],
            )

            if existing is not None and existing.id != route.id:
                raise ResourceConflictError(
                    "A route between these two airports already exists."
                )

            route = self.repository.update(
                route,
                origin_airport_id=data["origin_airport_id"],
                destination_airport_id=data["destination_airport_id"],
                distance_km=data["distance_km"],
                estimated_duration_minutes=data["estimated_duration_minutes"],
                is_active=bool(is_active),
            )

            self.session.commit()

            return route

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
                "The route could not be updated because of a database conflict."
            ) from error

        except SQLAlchemyError as error:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to update the route."
            ) from error

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_route(self, route_id: int) -> None:
        self._require_admin()

        if route_id is None:
            raise ValidationError("Route ID is required.")

        try:
            route = self.repository.get_by_id(route_id)

            if route is None:
                raise ResourceNotFoundError(
                    "Route was not found."
                )

            self.repository.delete(route)
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
                "This route cannot be deleted because it is being used by an existing flight."
            ) from error

        except SQLAlchemyError as error:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to delete the route."
            ) from error