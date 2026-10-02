from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Baggage


class BaggageRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, baggage_id: int) -> Baggage | None:
        statement = select(Baggage).where(Baggage.id == baggage_id)
        return self.session.scalar(statement)

    def get_by_checkin(self, checkin_id: int) -> list[Baggage]:
        statement = (
            select(Baggage)
            .where(Baggage.checkin_id == checkin_id)
            .order_by(Baggage.id.asc())
        )
        return list(self.session.scalars(statement).all())

    def get_by_tag(self, bag_tag: str) -> Baggage | None:
        statement = select(Baggage).where(
            func.upper(Baggage.bag_tag) == bag_tag.strip().upper()
        )
        return self.session.scalar(statement)

    def count(self) -> int:
        statement = select(func.count(Baggage.id))
        return self.session.scalar(statement) or 0

    def create(
        self,
        *,
        checkin_id: int,
        bag_tag: str,
        weight_kg,
        status,
    ) -> Baggage:
        baggage = Baggage(
            checkin_id=checkin_id,
            bag_tag=bag_tag,
            weight_kg=weight_kg,
            status=status,
        )
        self.session.add(baggage)
        self.session.flush()
        return baggage

    def delete(self, baggage: Baggage) -> None:
        self.session.delete(baggage)
        self.session.flush()
