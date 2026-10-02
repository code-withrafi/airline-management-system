from app.models.booking import BookingStatus
from app.exceptions import ValidationError


class BookingStatusValidator:
    """Validates BookingStatus transitions."""

    ALLOWED_TRANSITIONS = {
        BookingStatus.UNPAID: {
            BookingStatus.CONFIRMED,
            BookingStatus.CANCELLED,
        },
        BookingStatus.CONFIRMED: {
            BookingStatus.CHECKED_IN,
            BookingStatus.CANCELLED,
            BookingStatus.REFUND_REQUESTED,
        },
        BookingStatus.CHECKED_IN: {
            BookingStatus.COMPLETED,
        },
        BookingStatus.REFUND_REQUESTED: {
            BookingStatus.REFUNDED,
            BookingStatus.CONFIRMED,
        },
        BookingStatus.REFUNDED: set(),
        BookingStatus.CANCELLED: set(),
        BookingStatus.COMPLETED: set(),
    }

    @classmethod
    def validate_transition(
        cls,
        current_status,
        new_status,
    ) -> None:

        if current_status == new_status:
            return

        allowed = cls.ALLOWED_TRANSITIONS.get(
            current_status,
            set(),
        )

        if new_status not in allowed:
            raise ValidationError(
                f"Invalid booking status change: "
                f"{current_status.value} -> {new_status.value}"
            )
