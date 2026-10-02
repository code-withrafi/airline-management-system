# api/routers/payments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.passenger import Passenger
from app.services.booking_service import BookingService
from app.services.exceptions import (
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.payment_service import PaymentService
from api.deps import get_db, require_passenger_profile
from api.schemas.booking import PaymentRequest, PaymentResponse
from app.config.booking_policy import EXPIRY_THRESHOLD
from datetime import datetime

router = APIRouter()


# Statuses that mean the booking is already settled — cannot be paid again.
_ALREADY_PAID_STATUSES = {
    "CONFIRMED",
    "CHECKED_IN",
    "COMPLETED",
}

# Statuses that mean the booking is dead — cannot be paid.
_DEAD_STATUSES = {
    "CANCELLED",
    "REFUNDED",
    "REFUND_REQUESTED",
}


def _status_value(status) -> str:
    """Normalize a BookingStatus enum (or string) to its uppercase string."""
    return getattr(status, "value", str(status)).upper()


@router.post("", response_model=PaymentResponse)
def pay(
    payload: PaymentRequest,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """Process payment for a booking and mark it as paid on success."""

    # ---------- 1. Fetch booking + ownership check ----------
    try:
        booking = BookingService(db).get_booking_by_id(payload.booking_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if booking.passenger_id != passenger.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your booking.",
        )

    # ---------- 2a. Expiry guard ----------
    # Even if the background sweeper hasn't run yet, refuse payment
    # for a booking whose payment window has already closed, and
    # cancel it so the seat is released immediately.
    current_status = _status_value(booking.status)

    if current_status == "UNPAID" and booking.booked_at is not None:
        cutoff = datetime.utcnow() - EXPIRY_THRESHOLD
        if booking.booked_at <= cutoff:
            try:
                booking.status = booking.status.__class__.CANCELLED
                booking.cancelled_at = datetime.utcnow()
                db.commit()
            except Exception:
                db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Payment window expired. The booking was "
                    "cancelled and the seat has been released."
                ),
            )

    # ---------- 2b. Status guard: can we pay? ----------

    if current_status in _ALREADY_PAID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Booking is already {current_status.lower()}.",
        )

    if current_status in _DEAD_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Booking cannot be paid (status: {current_status}).",
        )

    if current_status != "UNPAID":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Booking is not payable (status: {current_status}).",
        )

    # ---------- 3. Amount sanity check ----------
    try:
        amount = float(payload.amount)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid payment amount.",
        )

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Amount must be greater than zero.",
        )

    # Optional: enforce that the client pays exactly the booking's fare.
    expected_amount = float(booking.fare_amount)
    if abs(amount - expected_amount) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Amount mismatch. Expected {expected_amount:.2f}, "
                f"got {amount:.2f}."
            ),
        )

    # ---------- 4. Run the mock payment gateway ----------
    # PaymentService takes NO constructor arguments — it's a pure validator
    # that returns a PaymentResult. It does NOT touch the database.
    result = PaymentService().process_payment(
        booking_id=payload.booking_id,
        amount=amount,
        card_number=payload.card_number,
        expiry=payload.expiry,
        cvv=payload.cvv,
        cardholder_name=payload.cardholder_name,
    )

    if not result.success:
        # Mock gateway rejected the card format — surface the reason.
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result.message or "Payment declined.",
        )

    # ---------- 5. Persist: mark booking as paid/confirmed ----------
    # Since PaymentService is a mock and does not write to the DB,
    # the router performs the state transition.
    try:
        BookingService(db).mark_as_paid(booking.id)
    except ResourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ResourceConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except DatabaseOperationError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    # ---------- 6. Return success ----------
    return PaymentResponse(
        success=True,
        message=result.message or "Payment approved.",
        booking_id=booking.id,
        transaction_id=result.transaction_id,
        amount=result.amount if result.amount is not None else amount,
    )