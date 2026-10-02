from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Aircraft


class AircraftRepository:
    """
    Repository responsible for database operations related to aircraft.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Aircraft]:
        statement = (
            select(Aircraft)
            .order_by(Aircraft.registration_number.asc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def get_by_id(self, aircraft_id: int) -> Aircraft | None:
        statement = select(Aircraft).where(
            Aircraft.id == aircraft_id
        )

        return self.session.scalar(statement)

    def get_by_registration_number(
        self,
        registration_number: str,
    ) -> Aircraft | None:
        normalized = registration_number.strip().upper()

        statement = select(Aircraft).where(
            func.upper(Aircraft.registration_number)
            == normalized
        )

        return self.session.scalar(statement)

    def search(
        self,
        search_text: str,
    ) -> list[Aircraft]:
        normalized_text = search_text.strip()

        if not normalized_text:
            return self.get_all()

        pattern = f"%{normalized_text}%"

        statement = (
            select(Aircraft)
            .where(
                or_(
                    Aircraft.registration_number.ilike(pattern),
                    Aircraft.manufacturer.ilike(pattern),
                    Aircraft.model.ilike(pattern),
                )
            )
            .order_by(Aircraft.registration_number.asc())
        )

        return list(
            self.session.scalars(statement).all()
        )

    def create(
        self,
        *,
        registration_number: str,
        manufacturer: str,
        model: str,
        seat_capacity: int,
        status,
    ) -> Aircraft:
        aircraft = Aircraft(
            registration_number=registration_number,
            manufacturer=manufacturer,
            model=model,
            seat_capacity=seat_capacity,
            status=status,
        )

        self.session.add(aircraft)
        self.session.flush()

        return aircraft

    def update(
        self,
        aircraft: Aircraft,
        *,
        registration_number: str,
        manufacturer: str,
        model: str,
        seat_capacity: int,
        status,
    ) -> Aircraft:
        aircraft.registration_number = registration_number
        aircraft.manufacturer = manufacturer
        aircraft.model = model
        aircraft.seat_capacity = seat_capacity
        aircraft.status = status

        self.session.flush()

        return aircraft

    def delete(
        self,
        aircraft: Aircraft,
    ) -> None:
        self.session.delete(aircraft)
        self.session.flush()

    def count(self) -> int:
        statement = select(
            func.count(Aircraft.id)
        )

        return self.session.scalar(statement) or 0
