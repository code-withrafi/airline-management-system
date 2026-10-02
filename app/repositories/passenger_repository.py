from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Passenger


class PassengerRepository:
    """
    Repository responsible for database operations
    related to passengers.
    """

    def __init__(
        self,
        session: Session,
    ):
        self.session = session


    def get_all(self) -> list[Passenger]:

        statement = (
            select(Passenger)
            .order_by(
                Passenger.last_name.asc(),
                Passenger.first_name.asc(),
            )
        )

        return list(
            self.session.scalars(statement).all()
        )


    def get_by_id(
        self,
        passenger_id: int,
    ) -> Passenger | None:

        statement = select(Passenger).where(
            Passenger.id == passenger_id
        )

        return self.session.scalar(
            statement
        )


    def get_by_user_id(
        self,
        user_id: int,
    ) -> Passenger | None:

        statement = select(Passenger).where(
            Passenger.user_id == user_id
        )

        return self.session.scalar(
            statement
        )

    def get_by_passport_number(
        self,
        passport_number: str,
    ) -> Passenger | None:

        normalized = (
            passport_number
            .strip()
            .upper()
        )

        statement = select(Passenger).where(
            func.upper(
                Passenger.passport_number
            )
            == normalized
        )

        return self.session.scalar(
            statement
        )


    def search(
        self,
        search_text: str,
    ) -> list[Passenger]:

        normalized_text = (
            search_text.strip()
        )

        if not normalized_text:
            return self.get_all()


        pattern = f"%{normalized_text}%"


        statement = (
            select(Passenger)
            .where(
                or_(
                    Passenger.first_name.ilike(pattern),
                    Passenger.last_name.ilike(pattern),
                    Passenger.phone.ilike(pattern),
                    Passenger.passport_number.ilike(pattern),
                )
            )
            .order_by(
                Passenger.last_name.asc(),
                Passenger.first_name.asc(),
            )
        )


        return list(
            self.session.scalars(statement).all()
        )


    def create(
        self,
        *,
        user_id: int,
        first_name: str,
        last_name: str,
        phone: str,
        date_of_birth,
        passport_number: str,
        address: str | None = None,
    ) -> Passenger:


        passenger = Passenger(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            date_of_birth=date_of_birth,
            passport_number=passport_number,
            address=address,
        )


        self.session.add(
            passenger
        )

        self.session.flush()


        return passenger


    def update(
        self,
        passenger: Passenger,
        *,
        first_name: str,
        last_name: str,
        phone: str,
        date_of_birth,
        passport_number: str,
        address: str | None,
    ) -> Passenger:


        passenger.first_name = first_name
        passenger.last_name = last_name
        passenger.phone = phone
        passenger.date_of_birth = date_of_birth
        passenger.passport_number = passport_number
        passenger.address = address


        self.session.flush()


        return passenger


    def delete(
        self,
        passenger: Passenger,
    ) -> None:


        self.session.delete(
            passenger
        )

        self.session.flush()


    def count(self) -> int:

        statement = select(
            func.count(
                Passenger.id
            )
        )

        return (
            self.session.scalar(statement)
            or 0
        )