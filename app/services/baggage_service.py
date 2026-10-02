import random
import string
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Baggage, BaggageStatus
from app.repositories import (
    BaggageRepository,
    CheckInRepository,
)
from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class BaggageService:

    MAX_WEIGHT_KG = Decimal("40.00")

    def __init__(self, session: Session):
        self.session = session
        self.repository = BaggageRepository(session)
        self.checkin_repository = CheckInRepository(session)

    @staticmethod
    def _generate_tag() -> str:
        prefix = "BG"
        random_part = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=8,
            )
        )
        return f"{prefix}{random_part}"

    def get_baggage_for_checkin(
        self, checkin_id: int
    ) -> list[Baggage]:
        if not isinstance(checkin_id, int) or checkin_id <= 0:
            raise ValidationError(
                "Check-in ID must be a positive integer."
            )
        try:
            return self.repository.get_by_checkin(checkin_id)
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to retrieve baggage."
            ) from exc

    def add_baggage(
        self,
        *,
        checkin_id: int,
        weight_kg,
    ) -> Baggage:

        if not isinstance(checkin_id, int) or checkin_id <= 0:
            raise ValidationError(
                "Check-in ID must be a positive integer."
            )

        try:
            weight = Decimal(str(weight_kg))
        except Exception:
            raise ValidationError(
                "Baggage weight must be numeric."
            )

        if weight <= 0:
            raise ValidationError(
                "Baggage weight must be greater than zero."
            )

        if weight > self.MAX_WEIGHT_KG:
            raise ValidationError(
                f"Baggage weight must not exceed "
                f"{self.MAX_WEIGHT_KG} kg."
            )

        checkin = self.checkin_repository.get_by_id(checkin_id)
        if checkin is None:
            raise ResourceNotFoundError("Check-in was not found.")

        for _ in range(5):
            tag = self._generate_tag()
            if self.repository.get_by_tag(tag) is None:
                break
        else:
            raise ResourceConflictError(
                "Unable to generate a unique baggage tag."
            )

        try:
            baggage = self.repository.create(
                checkin_id=checkin_id,
                bag_tag=tag,
                weight_kg=weight,
                status=BaggageStatus.CHECKED,
            )
            self.session.commit()
            return baggage

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "Baggage with this tag already exists."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to add baggage."
            ) from exc

    def remove_baggage(self, baggage_id: int) -> None:

        baggage = self.repository.get_by_id(baggage_id)
        if baggage is None:
            raise ResourceNotFoundError("Baggage was not found.")

        try:
            self.repository.delete(baggage)
            self.session.commit()

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to remove baggage."
            ) from exc
