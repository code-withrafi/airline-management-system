# api/routers/seats.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.booking import BookingStatus
from app.repositories.booking_repository import BookingRepository
from app.repositories.flight_repository import FlightRepository
from app.services.pricing import calculate_fare          # ← NEW
from app.services.seat_service import SeatService
from api.deps import get_db
from api.schemas.booking import SeatResponse

router = APIRouter()


@router.get(
    "/flights/{flight_id}/seats",
    response_model=list[SeatResponse],
)
def get_flight_seats(
    flight_id: int,
    db: Session = Depends(get_db),
):
    """
    Public seat map for a flight.
    Each seat knows:
      - whether it's still available (no active booking)
      - its computed price (base_fare × class multiplier)
    """
    flight = FlightRepository(db).get_by_id(flight_id)
    if flight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found.",
        )

    seats = SeatService(db).get_aircraft_seats(flight.aircraft_id) or []

    taken_booking_rows = BookingRepository(db).get_by_flight(flight_id)
    taken_seat_ids = {
        b.seat_id
        for b in taken_booking_rows
        if b.status not in (BookingStatus.CANCELLED, BookingStatus.REFUNDED)
    }

    return [
        SeatResponse(
            id=s.id,
            seat_number=s.seat_number,
            seat_class=(
                s.seat_class.value
                if hasattr(s.seat_class, "value")
                else str(s.seat_class)
            ),
            row_number=s.row_number,
            position=s.position,
            is_available=(s.id not in taken_seat_ids),
            price=calculate_fare(flight.base_fare, s.seat_class),   # ← NEW
        )
        for s in seats
    ]