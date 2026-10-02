from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BoardingPass


class BoardingPassRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, pass_id: int) -> BoardingPass | None:
        statement = select(BoardingPass).where(
            BoardingPass.id == pass_id
        )
        return self.session.scalar(statement)

    def get_by_booking(self, booking_id: int) -> BoardingPass | None:
        statement = select(BoardingPass).where(
            BoardingPass.booking_id == booking_id
        )
        return self.session.scalar(statement)

    def get_by_number(
        self, pass_number: str
    ) -> BoardingPass | None:
        statement = select(BoardingPass).where(
            func.upper(BoardingPass.boarding_pass_number)
            == pass_number.strip().upper()
        )
        return self.session.scalar(statement)

    def count(self) -> int:
        statement = select(func.count(BoardingPass.id))
        return self.session.scalar(statement) or 0

    def create(
        self,
        *,
        booking_id: int,
        boarding_pass_number: str,
        boarding_group: str,
        boarding_gate: str,
        issued_by: int | None,
    ) -> BoardingPass:
        boarding_pass = BoardingPass(
            booking_id=booking_id,
            boarding_pass_number=boarding_pass_number,
            boarding_group=boarding_group,
            boarding_gate=boarding_gate,
            issued_by=issued_by,
        )
        self.session.add(boarding_pass)
        self.session.flush()
        return boarding_pass

    def delete(self, boarding_pass: BoardingPass) -> None:
        self.session.delete(boarding_pass)
        self.session.flush()
