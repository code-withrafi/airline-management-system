from datetime import datetime, timezone
from decimal import Decimal

from app.services.exceptions import ValidationError


class RefundPolicyService:
    """
    Computes refund percentages and amounts based on
    how many days before departure a refund is requested.

    Refund tiers (days before departure):
        7+      -> 100%
        5 or 6  ->  80%
        3 or 4  ->  70%
        2       ->  60%
        1       ->  40%
        0       ->  25%  (same day)
        past    -> invalid (no refund)
    """

    TIERS = [
        (7, Decimal("1.00")),
        (5, Decimal("0.80")),
        (3, Decimal("0.70")),
        (2, Decimal("0.60")),
        (1, Decimal("0.40")),
        (0, Decimal("0.25")),
    ]

    @classmethod
    def get_refund_percentage(
        cls,
        departure_time: datetime,
        now: datetime | None = None,
    ) -> Decimal:
        """
        Return the refund percentage (0.0 to 1.0) for a
        refund requested at `now` for a flight departing
        at `departure_time`.

        Raises ValidationError if the flight has already departed.
        """

        if now is None:
            now = datetime.now(timezone.utc).replace(tzinfo=None)

        if departure_time <= now:
            raise ValidationError(
                "Refunds are not available after the flight has departed."
            )

        days_before = (departure_time - now).days

        for threshold, percentage in cls.TIERS:
            if days_before >= threshold:
                return percentage

        # Should never reach here since days_before >= 0 and
        # the last tier threshold is 0
        return Decimal("0.25")

    @classmethod
    def calculate_refund_amount(
        cls,
        fare_amount,
        departure_time: datetime,
        now: datetime | None = None,
    ) -> Decimal:
        """
        Return the refund amount in currency units.
        """

        if fare_amount is None:
            raise ValidationError("Booking has no fare amount.")

        fare = Decimal(str(fare_amount))

        if fare < 0:
            raise ValidationError("Fare amount cannot be negative.")

        percentage = cls.get_refund_percentage(
            departure_time=departure_time,
            now=now,
        )

        return (fare * percentage).quantize(Decimal("0.01"))