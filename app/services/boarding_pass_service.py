import random
import string

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    BookingStatus,
    BoardingPass,
)
from app.repositories import (
    BookingRepository,
    BoardingPassRepository,
)
from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class BoardingPassService:

    def __init__(self, session: Session):
        self.session = session
        self.repository = BoardingPassRepository(session)
        self.booking_repository = BookingRepository(session)

    @staticmethod
    def _generate_number() -> str:
        prefix = "BP"
        random_part = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=8,
            )
        )
        return f"{prefix}{random_part}"

    def get_pass_for_booking(
        self, booking_id: int
    ) -> BoardingPass:
        boarding_pass = self.repository.get_by_booking(
            booking_id
        )
        if boarding_pass is None:
            raise ResourceNotFoundError(
                "This booking has no boarding pass yet."
            )
        return boarding_pass

    def issue_boarding_pass(
        self,
        *,
        booking_id: int,
        boarding_group: str,
        boarding_gate: str,
        issued_by: int | None = None,
    ) -> BoardingPass:

        if not isinstance(booking_id, int) or booking_id <= 0:
            raise ValidationError(
                "Booking ID must be a positive integer."
            )

        if not isinstance(boarding_group, str) or not boarding_group.strip():
            raise ValidationError("Boarding group is required.")

        if not isinstance(boarding_gate, str) or not boarding_gate.strip():
            raise ValidationError("Boarding gate is required.")

        try:
            booking = self.booking_repository.get_by_id(booking_id)
            if booking is None:
                raise ResourceNotFoundError("Booking was not found.")

            if booking.status != BookingStatus.CHECKED_IN:
                raise ResourceConflictError(
                    "Boarding passes can only be issued for "
                    "checked-in bookings."
                )

            existing = self.repository.get_by_booking(booking_id)
            if existing is not None:
                raise ResourceConflictError(
                    "This booking already has a boarding pass."
                )

            for _ in range(5):
                number = self._generate_number()
                if self.repository.get_by_number(number) is None:
                    break
            else:
                raise ResourceConflictError(
                    "Unable to generate a unique boarding pass number."
                )

            boarding_pass = self.repository.create(
                booking_id=booking_id,
                boarding_pass_number=number,
                boarding_group=boarding_group.strip().upper(),
                boarding_gate=boarding_gate.strip().upper(),
                issued_by=issued_by,
            )

            self.session.commit()
            return boarding_pass

        except (
            ValidationError,
            ResourceNotFoundError,
            ResourceConflictError,
        ):
            self.session.rollback()
            raise

        except IntegrityError as exc:
            self.session.rollback()
            raise ResourceConflictError(
                "Boarding pass already exists for this booking."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to issue boarding pass."
            ) from exc
