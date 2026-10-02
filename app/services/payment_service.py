from dataclasses import dataclass
from datetime import datetime
import uuid

from app.validators.payment_validator import (
    PaymentValidationError,
    validate_card_number,
    validate_expiry,
    validate_cvv,
    validate_cardholder,
)


@dataclass(frozen=True)
class PaymentResult:
    """
    Result of a mock payment attempt.

    success        : whether the payment was approved
    transaction_id : reference string when successful, else None
    message        : human-readable outcome
    paid_at        : UTC timestamp when successful, else None
    amount         : charged amount (0.0 on failure)
    """

    success: bool

    transaction_id: str | None

    message: str

    paid_at: datetime | None

    amount: float


class PaymentService:
    """
    Mock payment gateway.

    Validates card *format* only and always approves
    well-formed input. No real gateway integration —
    out of scope for this project.
    """

    @staticmethod
    def _generate_transaction_id() -> str:

        body = (
            uuid.uuid4()
            .hex[:12]
            .upper()
        )

        return f"TXN-{body}"

    def process_payment(
        self,
        *,
        booking_id: int,
        amount: float,
        card_number: str,
        expiry: str,
        cvv: str,
        cardholder_name: str,
    ) -> PaymentResult:
        """
        Attempt to process a payment for a booking.

        Returns a PaymentResult instead of raising so the
        GUI can display the failure reason inline.
        """

        if not isinstance(booking_id, int) or booking_id <= 0:

            return PaymentResult(
                success=False,
                transaction_id=None,
                message="Invalid booking ID.",
                paid_at=None,
                amount=0.0,
            )

        if amount is None or amount <= 0:

            return PaymentResult(
                success=False,
                transaction_id=None,
                message="Amount must be greater than zero.",
                paid_at=None,
                amount=0.0,
            )

        try:

            validate_card_number(
                card_number
            )

            validate_expiry(
                expiry
            )

            validate_cvv(
                cvv
            )

            validate_cardholder(
                cardholder_name
            )

        except PaymentValidationError as exc:

            return PaymentResult(
                success=False,
                transaction_id=None,
                message=str(exc),
                paid_at=None,
                amount=0.0,
            )

        return PaymentResult(
            success=True,
            transaction_id=self._generate_transaction_id(),
            message="Payment approved (mock).",
            paid_at=datetime.utcnow(),
            amount=float(amount),
        )
