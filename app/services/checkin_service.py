from datetime import datetime

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    Booking,
    BookingStatus,
    CheckIn,
    CheckInMethod,
    CheckInStatus,
)
from app.repositories import (
    BoardingPassRepository,
    BookingRepository,
    CheckInRepository,
    StaffRepository,
)
from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class CheckInService:

    def __init__(self, session: Session):
        self.session = session
        self.repository = CheckInRepository(session)
        self.booking_repository = BookingRepository(session)
        self.staff_repository = StaffRepository(session)
        self.boarding_pass_repository = BoardingPassRepository(session)

    def get_checkin_by_booking(self, booking_id: int) -> CheckIn:
        checkin = self.repository.get_by_booking(booking_id)
        if checkin is None:
            raise ResourceNotFoundError(
                "This booking has not been checked in."
            )
        return checkin

    def get_checkin(self, checkin_id: int) -> CheckIn:
        checkin = self.repository.get_by_id(checkin_id)
        if checkin is None:
            raise ResourceNotFoundError("Check-in was not found.")
        return checkin

    def check_in_booking(
        self,
        *,
        booking_id: int,
        staff_id: int | None = None,
        method=CheckInMethod.STAFF,
    ) -> CheckIn:

        if not isinstance(booking_id, int) or booking_id <= 0:
            raise ValidationError(
                "Booking ID must be a positive integer."
            )

        try:
            booking = self.booking_repository.get_by_id(booking_id)
            if booking is None:
                raise ResourceNotFoundError("Booking was not found.")

            if booking.status == BookingStatus.CHECKED_IN:
                raise ResourceConflictError(
                    "This booking is already checked in."
                )

            if booking.status == BookingStatus.CANCELLED:
                raise ResourceConflictError(
                    "Cancelled bookings cannot be checked in."
                )

            if booking.status == BookingStatus.REFUNDED:
                raise ResourceConflictError(
                    "Refunded bookings cannot be checked in."
                )

            if booking.status != BookingStatus.CONFIRMED:
                raise ResourceConflictError(
                    f"Only CONFIRMED bookings can be checked in "
                    f"(current: {booking.status.value})."
                )

            if staff_id is not None:
                staff = self.staff_repository.get_by_id(staff_id)
                if staff is None:
                    raise ResourceNotFoundError(
                        "Staff member was not found."
                    )

            if booking.flight.departure_time < datetime.utcnow():
                raise ResourceConflictError(
                    "Cannot check in a booking for a flight "
                    "that has already departed."
                )

            # Defensive: if a stale CheckIn row exists from a
            # previous check-in that was not fully cleaned up,
            # delete it before creating a new one.
            stale = self.repository.get_by_booking(booking_id)
            if stale is not None:
                self.repository.delete(stale)
                self.session.flush()

            checkin = self.repository.create(
                booking_id=booking_id,
                checked_in_by=staff_id,
                method=method,
                status=CheckInStatus.CHECKED_IN,
            )

            booking.status = BookingStatus.CHECKED_IN

            self.session.commit()
            return checkin

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
                "This booking is already checked in."
            ) from exc

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to check in booking."
            ) from exc

    def cancel_checkin(self, checkin_id: int) -> None:
        """
        Undo a check-in.

        Deletes the CheckIn row and any BoardingPass row linked
        to the same booking, then resets the booking status to
        CONFIRMED. Baggage rows cascade-delete via the CheckIn
        relationship (cascade='all, delete-orphan').
        """

        checkin = self.get_checkin(checkin_id)
        booking = self.booking_repository.get_by_id(
            checkin.booking_id
        )

        if booking is None:
            raise ResourceNotFoundError("Booking was not found.")

        if booking.flight.departure_time < datetime.utcnow():
            raise ResourceConflictError(
                "Cannot undo check-in after the flight has departed."
            )

        try:
            # 1. Delete any boarding pass issued for this booking
            #    (unique constraint on booking_id would block
            #    re-issuance after a later re-check-in).
            boarding_pass = (
                self.boarding_pass_repository
                .get_by_booking(checkin.booking_id)
            )
            if boarding_pass is not None:
                self.boarding_pass_repository.delete(boarding_pass)

            # 2. Delete the check-in row. Baggage cascades via
            #    the relationship on CheckIn.
            self.repository.delete(checkin)

            # 3. Flip the booking back to CONFIRMED so it can
            #    be checked in again.
            booking.status = BookingStatus.CONFIRMED

            self.session.commit()

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to cancel check-in."
            ) from exc
