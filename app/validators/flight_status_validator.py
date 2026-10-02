from app.models.flight import FlightStatus
from app.exceptions import ValidationError


class FlightStatusValidator:
    """Validates FlightStatus transitions."""

    ALLOWED_TRANSITIONS = {
        FlightStatus.SCHEDULED: {
            FlightStatus.BOARDING,
            FlightStatus.DELAYED,
            FlightStatus.CANCELLED,
        },
        FlightStatus.BOARDING: {
            FlightStatus.DEPARTED,
            FlightStatus.DELAYED,
            FlightStatus.CANCELLED,
        },
        FlightStatus.DELAYED: {
            FlightStatus.BOARDING,
            FlightStatus.DEPARTED,
            FlightStatus.CANCELLED,
        },
        FlightStatus.DEPARTED: {
            FlightStatus.ARRIVED,
        },
        FlightStatus.ARRIVED: set(),
        FlightStatus.CANCELLED: set(),
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
                f"Invalid flight status change: "
                f"{current_status.value} â†’ {new_status.value}"
            )
