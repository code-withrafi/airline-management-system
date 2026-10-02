from datetime import datetime
import random
import string

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from sqlalchemy.orm import Session

from app.models import (
    Booking,
    BookingStatus,
)

from app.repositories import (
    BookingRepository,
    FlightRepository,
    PassengerRepository,
    SeatRepository,
)

from app.services.booking_availability_service import (
    BookingAvailabilityService,
)

from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)

from app.services.refund_policy_service import (
    RefundPolicyService,
)

from app.validators.booking_status_validator import (
    BookingStatusValidator,
)


class BookingService:
    """
    Business service responsible for booking management.
    """

    def __init__(
        self,
        session: Session,
    ):

        self.session = session

        self.booking_repository = (
            BookingRepository(
                session
            )
        )

        self.passenger_repository = (
            PassengerRepository(
                session
            )
        )

        self.flight_repository = (
            FlightRepository(
                session
            )
        )

        self.seat_repository = (
            SeatRepository(
                session
            )
        )

        self.availability_service = (
            BookingAvailabilityService(
                session
            )
        )

    @staticmethod
    def _validate_id(
        value: int,
        name: str,
    ) -> None:

        if isinstance(value, bool):

            raise ValidationError(
                f"{name} must be a positive integer."
            )

        if not isinstance(value, int):

            raise ValidationError(
                f"{name} must be a positive integer."
            )

        if value <= 0:

            raise ValidationError(
                f"{name} must be a positive integer."
            )

    @staticmethod
    def _generate_reference() -> str:

        prefix = "BK"

        random_part = "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=8,
            )
        )

        return f"{prefix}{random_part}"

    @staticmethod
    def _validate_fare(
        fare_amount,
    ):

        if fare_amount is None:

            raise ValidationError(
                "Fare amount is required."
            )

        if fare_amount < 0:

            raise ValidationError(
                "Fare amount cannot be negative."
            )

        return fare_amount

    def get_all_bookings(
        self,
    ) -> list[Booking]:

        try:

            return (
                self.booking_repository
                .get_all()
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve bookings."
            ) from exc

    def get_booking_by_id(
        self,
        booking_id: int,
    ) -> Booking:

        self._validate_id(
            booking_id,
            "Booking ID"
        )

        try:

            booking = (
                self.booking_repository
                .get_by_id(
                    booking_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve booking."
            ) from exc

        if booking is None:

            raise ResourceNotFoundError(
                "Booking was not found."
            )

        return booking

    def get_booking_by_reference(
        self,
        reference: str,
    ) -> Booking | None:
        """Return a booking by its reference, or None."""

        if not isinstance(reference, str) or not reference.strip():
            raise ValidationError("Booking reference is required.")

        try:
            return self.booking_repository.get_by_reference(reference)
        except SQLAlchemyError as exc:
            raise DatabaseOperationError(
                "Unable to retrieve booking."
            ) from exc

    def get_passenger_bookings(
        self,
        passenger_id: int,
    ) -> list[Booking]:

        self._validate_id(
            passenger_id,
            "Passenger ID"
        )

        try:

            return (
                self.booking_repository
                .get_by_passenger(
                    passenger_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve passenger bookings."
            ) from exc

    def get_flight_bookings(
        self,
        flight_id: int,
    ) -> list[Booking]:

        self._validate_id(
            flight_id,
            "Flight ID"
        )

        try:

            return (
                self.booking_repository
                .get_active_bookings(
                    flight_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve flight bookings."
            ) from exc

    def create_booking(
        self,
        *,
        passenger_id: int,
        flight_id: int,
        seat_id: int,
        fare_amount,
    ) -> Booking:

        self._validate_id(
            passenger_id,
            "Passenger ID"
        )

        self._validate_id(
            flight_id,
            "Flight ID"
        )

        self._validate_id(
            seat_id,
            "Seat ID"
        )

        fare_amount = (
            self._validate_fare(
                fare_amount
            )
        )

        try:

            passenger = (
                self.passenger_repository
                .get_by_id(
                    passenger_id
                )
            )

            if passenger is None:

                raise ResourceNotFoundError(
                    "Passenger was not found."
                )

            flight = (
                self.flight_repository
                .get_by_id(
                    flight_id
                )
            )

            if flight is None:

                raise ResourceNotFoundError(
                    "Flight was not found."
                )

            seat = (
                self.seat_repository
                .get_by_id(
                    seat_id
                )
            )

            if seat is None:

                raise ResourceNotFoundError(
                    "Seat was not found."
                )

            self.availability_service.validate_seat_available(
                flight_id=flight_id,
                seat_id=seat_id,
            )

            booking_reference = (
                self._generate_reference()
            )

            booking = (
                self.booking_repository
                .create(
                    booking_reference=booking_reference,
                    passenger_id=passenger_id,
                    flight_id=flight_id,
                    seat_id=seat_id,
                    fare_amount=fare_amount,
                    status=BookingStatus.UNPAID,
                )
            )

            self.session.commit()

            return booking

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            self.session.rollback()

            raise

        except IntegrityError as exc:

            self.session.rollback()

            raise ResourceConflictError(
                "Unable to create booking because the seat is already reserved."
            ) from exc

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to create booking."
            ) from exc

    def _transition_booking(
        self,
        booking_id: int,
        new_status,
    ) -> Booking:
        """
        Internal helper: validate and apply a status transition.
        """

        self._validate_id(
            booking_id,
            "Booking ID"
        )

        try:

            booking = (
                self.booking_repository
                .get_by_id(
                    booking_id
                )
            )

            if booking is None:

                raise ResourceNotFoundError(
                    "Booking was not found."
                )

            if booking.status == new_status:

                return booking

            BookingStatusValidator.validate_transition(
                booking.status,
                new_status,
            )

            booking.status = new_status

            if new_status in (
                BookingStatus.CANCELLED,
                BookingStatus.REFUNDED,
            ):

                booking.cancelled_at = (
                    datetime.utcnow()
                )

            self.session.commit()

            return booking

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            self.session.rollback()

            raise

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to update booking status."
            ) from exc

    def mark_as_paid(
        self,
        booking_id: int,
    ) -> Booking:
        """UNPAID -> CONFIRMED."""

        return self._transition_booking(
            booking_id,
            BookingStatus.CONFIRMED,
        )

    def cancel_booking(
        self,
        booking_id: int,
    ) -> Booking:
        """UNPAID or CONFIRMED -> CANCELLED."""

        return self._transition_booking(
            booking_id,
            BookingStatus.CANCELLED,
        )

    def expire_unpaid_bookings(
        self,
        now: datetime | None = None,
    ) -> int:
        """Cancel every UNPAID booking that is past its payment window.

        Idempotent: safe to call as often as you like. Returns
        the number of bookings transitioned to CANCELLED.
        """

        if now is None:
            now = datetime.utcnow()

        from app.config.booking_policy import EXPIRY_THRESHOLD

        cutoff = now - EXPIRY_THRESHOLD

        try:
            expired = self.booking_repository.get_expired_unpaid(
                cutoff
            )

            if not expired:
                return 0

            for booking in expired:
                booking.status = BookingStatus.CANCELLED
                booking.cancelled_at = now

            self.session.commit()

            return len(expired)

        except SQLAlchemyError as exc:
            self.session.rollback()
            raise DatabaseOperationError(
                "Unable to expire unpaid bookings."
            ) from exc

    def check_in(
        self,
        booking_id: int,
    ) -> Booking:
        """CONFIRMED -> CHECKED_IN."""

        return self._transition_booking(
            booking_id,
            BookingStatus.CHECKED_IN,
        )

    def complete_booking(
        self,
        booking_id: int,
    ) -> Booking:
        """CHECKED_IN -> COMPLETED."""

        return self._transition_booking(
            booking_id,
            BookingStatus.COMPLETED,
        )

    def request_refund(
        self,
        booking_id: int,
    ) -> Booking:
        """
        CONFIRMED -> REFUND_REQUESTED.

        Only allowed if:
        - the booking is currently CONFIRMED
        - the flight has not yet departed
        """

        self._validate_id(
            booking_id,
            "Booking ID"
        )

        try:

            booking = (
                self.booking_repository
                .get_by_id(
                    booking_id
                )
            )

            if booking is None:

                raise ResourceNotFoundError(
                    "Booking was not found."
                )

            if booking.status != BookingStatus.CONFIRMED:

                raise ResourceConflictError(
                    "Only confirmed bookings can be refunded."
                )

            # Refuse if the flight has already departed
            RefundPolicyService.get_refund_percentage(
                departure_time=booking.flight.departure_time,
            )

            BookingStatusValidator.validate_transition(
                booking.status,
                BookingStatus.REFUND_REQUESTED,
            )

            booking.status = (
                BookingStatus.REFUND_REQUESTED
            )

            self.session.commit()

            return booking

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            self.session.rollback()

            raise

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to request refund."
            ) from exc

    def approve_refund(
        self,
        booking_id: int,
    ) -> Booking:
        """
        REFUND_REQUESTED -> REFUNDED.

        Computes the refund amount from the fare and the
        flight's departure time, stores it on the booking,
        and transitions to REFUNDED.
        """

        self._validate_id(
            booking_id,
            "Booking ID"
        )

        try:

            booking = (
                self.booking_repository
                .get_by_id(
                    booking_id
                )
            )

            if booking is None:

                raise ResourceNotFoundError(
                    "Booking was not found."
                )

            if booking.status != BookingStatus.REFUND_REQUESTED:

                raise ResourceConflictError(
                    "Only refund-requested bookings can be approved."
                )

            refund_amount = (
                RefundPolicyService
                .calculate_refund_amount(
                    fare_amount=booking.fare_amount,
                    departure_time=booking.flight.departure_time,
                )
            )

            BookingStatusValidator.validate_transition(
                booking.status,
                BookingStatus.REFUNDED,
            )

            booking.status = BookingStatus.REFUNDED
            booking.cancelled_at = datetime.utcnow()

            self.booking_repository.set_refund_amount(
                booking,
                refund_amount,
            )

            self.session.commit()

            return booking

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            self.session.rollback()

            raise

        except SQLAlchemyError as exc:

            self.session.rollback()

            raise DatabaseOperationError(
                "Unable to approve refund."
            ) from exc

    def reject_refund(
        self,
        booking_id: int,
    ) -> Booking:
        """REFUND_REQUESTED -> CONFIRMED."""

        return self._transition_booking(
            booking_id,
            BookingStatus.CONFIRMED,
        )

    def preview_refund(
        self,
        booking_id: int,
    ) -> dict:
        """
        Return a preview of the refund amount without
        making any changes. Used by the UI to show the
        passenger/admin how much they'll get back.
        """

        self._validate_id(
            booking_id,
            "Booking ID"
        )

        booking = self.booking_repository.get_by_id(
            booking_id
        )

        if booking is None:

            raise ResourceNotFoundError(
                "Booking was not found."
            )

        percentage = (
            RefundPolicyService
            .get_refund_percentage(
                departure_time=booking.flight.departure_time,
            )
        )

        amount = (
            RefundPolicyService
            .calculate_refund_amount(
                fare_amount=booking.fare_amount,
                departure_time=booking.flight.departure_time,
            )
        )

        return {
            "percentage": percentage,
            "amount": amount,
        }

    def update_booking_status(
        self,
        booking_id: int,
        status,
    ) -> Booking:
        """
        Generic status update — validates the transition.
        Kept for backwards compatibility.
        """

        if not isinstance(
            status,
            BookingStatus
        ):

            try:

                status = BookingStatus(
                    status
                )

            except (
                ValueError,
                TypeError,
            ) as exc:

                raise ValidationError(
                    "Invalid booking status."
                ) from exc

        return self._transition_booking(
            booking_id,
            status,
        )