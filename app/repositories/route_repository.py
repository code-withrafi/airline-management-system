from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Route


class RouteRepository:
    """
    Repository responsible for database operations related to routes.

    Persistence only. Business rules and validation belong in the
    service layer.
    """

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_all(self) -> list[Route]:
        statement = (
            select(Route)
            .options(
                selectinload(Route.origin_airport),
                selectinload(Route.destination_airport),
            )
            .order_by(Route.id.asc())
        )

        return list(self.session.scalars(statement).all())

    def get_by_id(self, route_id: int) -> Route | None:
        statement = (
            select(Route)
            .where(Route.id == route_id)
            .options(
                selectinload(Route.origin_airport),
                selectinload(Route.destination_airport),
            )
        )

        return self.session.scalar(statement)

    def get_by_airports(
        self,
        origin_airport_id: int,
        destination_airport_id: int,
    ) -> Route | None:
        statement = select(Route).where(
            Route.origin_airport_id == origin_airport_id,
            Route.destination_airport_id == destination_airport_id,
        )

        return self.session.scalar(statement)

    def search(self, search_text: str) -> list[Route]:
        """
        Search routes by origin/destination IATA or ICAO code.

        Route has no name/city of its own — those belong to Airport.
        This does a simple join and matches against the codes.
        """

        normalized = search_text.strip().upper()

        if not normalized:
            return self.get_all()

        pattern = f"%{normalized}%"

        from app.models import Airport

        statement = (
            select(Route)
            .join(
                Airport,
                Route.origin_airport_id == Airport.id,
            )
            .join(
                Airport,
                Route.destination_airport_id == Airport.id,
                aliased=True,
            )
            .where(
                or_(
                    Route.origin_airport_id.in_(
                        select(Airport.id).where(
                            or_(
                                Airport.iata_code.ilike(pattern),
                                Airport.icao_code.ilike(pattern),
                            )
                        )
                    ),
                    Route.destination_airport_id.in_(
                        select(Airport.id).where(
                            or_(
                                Airport.iata_code.ilike(pattern),
                                Airport.icao_code.ilike(pattern),
                            )
                        )
                    ),
                )
            )
            .options(
                selectinload(Route.origin_airport),
                selectinload(Route.destination_airport),
            )
            .order_by(Route.id.asc())
        )

        return list(self.session.scalars(statement).all())

    def count(self) -> int:
        statement = select(func.count(Route.id))
        return self.session.scalar(statement) or 0

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        origin_airport_id: int,
        destination_airport_id: int,
        distance_km: int,
        estimated_duration_minutes: int,
        is_active: bool = True,
    ) -> Route:
        route = Route(
            origin_airport_id=origin_airport_id,
            destination_airport_id=destination_airport_id,
            distance_km=distance_km,
            estimated_duration_minutes=estimated_duration_minutes,
            is_active=is_active,
        )

        self.session.add(route)
        self.session.flush()

        return route

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        route: Route,
        *,
        origin_airport_id: int,
        destination_airport_id: int,
        distance_km: int,
        estimated_duration_minutes: int,
        is_active: bool,
    ) -> Route:
        route.origin_airport_id = origin_airport_id
        route.destination_airport_id = destination_airport_id
        route.distance_km = distance_km
        route.estimated_duration_minutes = estimated_duration_minutes
        route.is_active = is_active

        self.session.flush()

        return route

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, route: Route) -> None:
        self.session.delete(route)
        self.session.flush()

    def get_all_by_airports(
        self,
        origin_airport_id: int,
        destination_airport_id: int,
    ) -> list[Route]:
        """
        Return all routes matching an origin/destination airport pair.

        A pair may have multiple routes (e.g. seasonal variants).
        """

        statement = (
            select(Route)
            .where(
                Route.origin_airport_id == origin_airport_id,
                Route.destination_airport_id == destination_airport_id,
            )
            .options(
                selectinload(Route.origin_airport),
                selectinload(Route.destination_airport),
            )
            .order_by(Route.id.asc())
        )

        return list(self.session.scalars(statement).all())
