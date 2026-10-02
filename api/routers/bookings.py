# api/routers/bookings.py
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.passenger import Passenger
from app.repositories.flight_repository import FlightRepository
from app.repositories.seat_repository import SeatRepository
from app.services.booking_service import BookingService
from app.services.exceptions import (
    AuthorizationError,
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.pricing import calculate_fare          # ← NEW
from api.deps import get_db, require_passenger_profile
from api.schemas.booking import (
    BookingCreateRequest,
    BookingResponse,
    RefundPreviewResponse,
    RefundRequestResponse,
)
from app.config.booking_policy import (
    PAYMENT_WINDOW,
    EXPIRY_THRESHOLD,
)

import tempfile
import os
from fastapi.responses import FileResponse

router = APIRouter()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _status_str(booking) -> str:
    return (
        booking.status.value
        if hasattr(booking.status, "value")
        else str(booking.status)
    )


def _to_response(booking) -> BookingResponse:
    """Build the public response model.

    For UNPAID bookings, also computes the payment-window fields
    so the frontend can render a countdown. For any other status
    those fields stay None.
    """
    status_value = _status_str(booking).upper()

    expires_at = None
    seconds_remaining = None

    if status_value == "UNPAID" and booking.booked_at is not None:
        expires_at = booking.booked_at + PAYMENT_WINDOW
        remaining = (expires_at - datetime.utcnow()).total_seconds()
        seconds_remaining = max(0, int(remaining))

    return BookingResponse(
        id=booking.id,
        booking_reference=booking.booking_reference,
        flight_id=booking.flight_id,
        seat_id=booking.seat_id,
        passenger_id=booking.passenger_id,
        fare_amount=booking.fare_amount,
        refund_amount=booking.refund_amount,
        status=status_value,
        booked_at=booking.booked_at,
        cancelled_at=booking.cancelled_at,
        expires_at=expires_at,
        seconds_remaining=seconds_remaining,
    )


def _maybe_expire(booking, db) -> None:
    """Lazily cancel a booking whose payment window has passed.

    Belt-and-braces for the background sweeper: if the sweeper
    hasn't run yet but a passenger (or their tab's setInterval)
    hits this endpoint, we expire the booking on the spot so the
    response is always truthful.

    Mutates ooking in place and commits. Safe to call on
    non-UNPAID bookings: it becomes a no-op.
    """
    if _status_str(booking).upper() != "UNPAID" or booking.booked_at is None:
        return

    cutoff = datetime.utcnow() - EXPIRY_THRESHOLD
    if booking.booked_at > cutoff:
        return

    booking.status = booking.status.__class__.CANCELLED
    booking.cancelled_at = datetime.utcnow()
    db.commit()
    db.refresh(booking)


# ------------------------------------------------------------------
# Create
# ------------------------------------------------------------------

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreateRequest,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """Create a booking (status: UNPAID). Only the owner can pay it."""
    flight = FlightRepository(db).get_by_id(payload.flight_id)
    if flight is None:
        raise HTTPException(404, "Flight not found.")

    seat = SeatRepository(db).get_by_id(payload.seat_id)
    if seat is None:
        raise HTTPException(404, "Seat not found.")
    if seat.aircraft_id != flight.aircraft_id:
        raise HTTPException(400, "Seat does not belong to this flight's aircraft.")

    # ✅ Compute the fare based on the seat's class (economy vs business)
    fare = calculate_fare(flight.base_fare, seat.seat_class)

    try:
        booking = BookingService(db).create_booking(
            passenger_id=passenger.id,
            flight_id=flight.id,
            seat_id=seat.id,
            fare_amount=fare,
        )
    except ResourceConflictError as exc:
        raise HTTPException(409, str(exc))
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    except AuthorizationError as exc:
        raise HTTPException(403, str(exc))
    except DatabaseOperationError as exc:
        raise HTTPException(500, str(exc))

    return _to_response(booking)


# ------------------------------------------------------------------
# Read
# ------------------------------------------------------------------

@router.get("/my", response_model=list[BookingResponse])
def my_bookings(
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """List the logged-in passenger's bookings."""
    try:
        bookings = BookingService(db).get_passenger_bookings(passenger.id)
    except DatabaseOperationError as exc:
        raise HTTPException(500, str(exc))

    return [_to_response(b) for b in bookings]


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """Get one of my bookings. 403 if it's not mine."""
    try:
        booking = BookingService(db).get_booking_by_id(booking_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))

    if booking.passenger_id != passenger.id:
        raise HTTPException(403, "Not your booking.")

    # Lazy expiry: if the payment window has passed while this
    # booking was UNPAID, cancel it now so the response is current.
    _maybe_expire(booking, db)

    return _to_response(booking)


# ------------------------------------------------------------------
# Cancel
# ------------------------------------------------------------------

@router.delete("/{booking_id}", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """Cancel my booking."""
    try:
        booking = BookingService(db).get_booking_by_id(booking_id)
        if booking.passenger_id != passenger.id:
            raise HTTPException(403, "Not your booking.")

        cancelled = BookingService(db).cancel_booking(booking_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ResourceConflictError as exc:
        raise HTTPException(409, str(exc))
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    except DatabaseOperationError as exc:
        raise HTTPException(500, str(exc))

    return _to_response(cancelled)


# ------------------------------------------------------------------
# Refunds
# ------------------------------------------------------------------

@router.get("/{booking_id}/refund-preview", response_model=RefundPreviewResponse)
def refund_preview(
    booking_id: int,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """
    Show the passenger how much they'd get back if they requested a refund now.
    Does NOT change any state.
    """
    try:
        booking = BookingService(db).get_booking_by_id(booking_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))

    if booking.passenger_id != passenger.id:
        raise HTTPException(403, "Not your booking.")

    # Only CONFIRMED bookings can be refunded (mirrors request_refund's rule).
    current = _status_str(booking).upper()
    if current != "CONFIRMED":
        return RefundPreviewResponse(
            booking_id=booking.id,
            booking_reference=booking.booking_reference,
            eligible=False,
            reason=(
                f"Only confirmed bookings can be refunded "
                f"(current status: {current})."
            ),
            refund_amount=Decimal("0.00"),
            refund_percentage=0,
            paid_amount=booking.fare_amount,
            departure_time=booking.flight.departure_time,
        )

    # Ask the service — keys are "amount" and "percentage"
    try:
        info = BookingService(db).preview_refund(booking_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except (ResourceConflictError, ValidationError) as exc:
        return RefundPreviewResponse(
            booking_id=booking.id,
            booking_reference=booking.booking_reference,
            eligible=False,
            reason=str(exc),
            refund_amount=Decimal("0.00"),
            refund_percentage=0,
            paid_amount=booking.fare_amount,
            departure_time=booking.flight.departure_time,
        )

    refund_amount = Decimal(str(info.get("amount", 0) or 0))
    refund_percentage = int(info.get("percentage", 0) or 0)

    now = datetime.utcnow()
    dep = booking.flight.departure_time
    hours_until = (dep - now).total_seconds() / 3600.0

    return RefundPreviewResponse(
        booking_id=booking.id,
        booking_reference=booking.booking_reference,
        eligible=True,
        refund_amount=refund_amount,
        refund_percentage=refund_percentage,
        paid_amount=booking.fare_amount,
        departure_time=dep,
        hours_until_departure=round(hours_until, 1),
    )


@router.post("/{booking_id}/refund", response_model=RefundRequestResponse)
def request_refund(
    booking_id: int,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """
    Submit a refund request.
    Flips booking status CONFIRMED → REFUND_REQUESTED.
    Admin reviews it later (via the desktop app).
    """
    try:
        booking = BookingService(db).get_booking_by_id(booking_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))

    if booking.passenger_id != passenger.id:
        raise HTTPException(403, "Not your booking.")

    try:
        updated = BookingService(db).request_refund(booking_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))
    except ResourceConflictError as exc:
        raise HTTPException(409, str(exc))
    except ValidationError as exc:
        raise HTTPException(422, str(exc))
    except DatabaseOperationError as exc:
        raise HTTPException(500, str(exc))

    return RefundRequestResponse(
        id=updated.id,
        booking_reference=updated.booking_reference,
        status=_status_str(updated),
        refund_amount=updated.refund_amount,
    )


# ------------------------------------------------------------------
# Ticket PDF
# ------------------------------------------------------------------

@router.get("/{booking_id}/ticket")
def download_ticket(
    booking_id: int,
    passenger: Passenger = Depends(require_passenger_profile),
    db: Session = Depends(get_db),
):
    """
    Generate and stream the e-ticket PDF for a booking.
    Only the owner can download it.
    """
    # Ownership check
    try:
        booking = BookingService(db).get_booking_by_id(booking_id)
    except ResourceNotFoundError as exc:
        raise HTTPException(404, str(exc))

    if booking.passenger_id != passenger.id:
        raise HTTPException(403, "Not your booking.")

    status_value = (
        booking.status.value
        if hasattr(booking.status, "value")
        else str(booking.status)
    ).upper()

    if status_value in ("UNPAID", "CANCELLED"):
        raise HTTPException(
            status_code=409,
            detail=f"Ticket is not available for a {status_value.lower()} booking.",
        )

    # Generate PDF to a temp file
    try:
        from app.utils.pdf_generator import generate_ticket_pdf

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pdf",
            prefix=f"ticket-{booking.booking_reference}-"
        ) as tmp:
            tmp_path = tmp.name

        generate_ticket_pdf(booking, tmp_path)

    except Exception as exc:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except OSError: pass
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate ticket PDF: {exc}",
        )

    filename = f"ticket-{booking.booking_reference}.pdf"

    return FileResponse(
        path=tmp_path,
        media_type="application/pdf",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
        background=_CleanupFile(tmp_path),
    )


class _CleanupFile:
    """Starlette BackgroundTask to delete a temp file after the response is sent."""
    def __init__(self, path: str):
        self.path = path

    async def __call__(self):
        try:
            os.remove(self.path)
        except OSError:
            pass