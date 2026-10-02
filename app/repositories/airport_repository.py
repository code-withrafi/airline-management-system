from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Airport


class AirportRepository:
    """Repository for airport persistence operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(self):
        statement = (
            select(Airport)
            .order_by(Airport.iata_code.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_by_id(self, airport_id):
        statement = select(Airport).where(Airport.id == airport_id)
        return self.session.scalar(statement)

    def get_by_iata_code(self, iata_code):
        code = iata_code.strip().upper()
        statement = select(Airport).where(
            func.upper(Airport.iata_code) == code
        )
        return self.session.scalar(statement)

    def get_by_icao_code(self, icao_code):
        code = icao_code.strip().upper()
        statement = select(Airport).where(
            func.upper(Airport.icao_code) == code
        )
        return self.session.scalar(statement)

    def search(self, search_text):
        text = search_text.strip()
        if not text:
            return self.get_all()

        pattern = f"%{text}%"
        statement = (
            select(Airport)
            .where(
                or_(
                    Airport.iata_code.ilike(pattern),
                    Airport.icao_code.ilike(pattern),
                    Airport.name.ilike(pattern),
                    Airport.city.ilike(pattern),
                    Airport.country.ilike(pattern),
                )
            )
            .order_by(Airport.iata_code.asc())
        )
        return list(self.session.scalars(statement).all())

    def create(self, *, iata_code, icao_code, name, city, country, timezone):
        airport = Airport(
            iata_code=iata_code,
            icao_code=icao_code,
            name=name,
            city=city,
            country=country,
            timezone=timezone,
        )
        self.session.add(airport)
        self.session.flush()
        return airport

    def update(self, airport, *, iata_code, icao_code, name, city, country, timezone):
        airport.iata_code = iata_code
        airport.icao_code = icao_code
        airport.name = name
        airport.city = city
        airport.country = country
        airport.timezone = timezone
        self.session.flush()
        return airport

    def delete(self, airport):
        self.session.delete(airport)
        self.session.flush()

    def count(self):
        statement = select(func.count(Airport.id))
        return self.session.scalar(statement) or 0
