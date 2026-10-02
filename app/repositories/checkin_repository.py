from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CheckIn


class CheckInRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, checkin_id: int) -> CheckIn | None:
        statement = select(CheckIn).where(CheckIn.id == checkin_id)
        return self.session.scalar(statement)

    def get_by_booking(self, booking_id: int) -> CheckIn | None:
        statement = select(CheckIn).where(
            CheckIn.booking_id == booking_id
        )
        return self.session.scalar(statement)

    def get_all(self) -> list[CheckIn]:
        statement = select(CheckIn).order_by(CheckIn.id.asc())
        return list(self.session.scalars(statement).all())

    def count(self) -> int:
        statement = select(func.count(CheckIn.id))
        return self.session.scalar(statement) or 0

    def create(
        self,
        *,
        booking_id: int,
        checked_in_by: int | None,
        method,
        status,
    ) -> CheckIn:
        checkin = CheckIn(
            booking_id=booking_id,
            checked_in_by=checked_in_by,
            method=method,
            status=status,
        )
        self.session.add(checkin)
        self.session.flush()
        return checkin

    def update_status(self, checkin: CheckIn, status) -> CheckIn:
        checkin.status = status
        self.session.flush()
        return checkin

    def delete(self, checkin: CheckIn) -> None:
        self.session.delete(checkin)
        self.session.flush()
