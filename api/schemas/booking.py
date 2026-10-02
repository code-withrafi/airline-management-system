# api/schemas/booking.py
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------- Seat ----------

class SeatResponse(BaseModel):
    id: int
    seat_number: str
    seat_class: str          # "ECONOMY" | "BUSINESS"
    row_number: int
    position: str            # "WINDOW" | "MIDDLE" | "AISLE" etc.
    is_available: bool
    price: Decimal           # ← NEW: computed fare for this seat's class


# ---------- Booking create ----------

class BookingCreateRequest(BaseModel):
    flight_id: int = Field(gt=0)
    seat_id: int = Field(gt=0)


# ---------- Booking response ----------

class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    booking_reference: str
    flight_id: int
    seat_id: int
    passenger_id: int
    fare_amount: Decimal
    refund_amount: Optional[Decimal] = None
    status: str
    booked_at: datetime
    cancelled_at: Optional[datetime] = None

    # Payment-window fields. Populated only when status == UNPAID.
    # expires_at  : booked_at + PAYMENT_WINDOW (absolute UTC time)
    # seconds_remaining : max(0, (expires_at - now).total_seconds())
    expires_at: Optional[datetime] = None
    seconds_remaining: Optional[int] = None


# ---------- Payment ----------

class PaymentRequest(BaseModel):
    booking_id: int = Field(gt=0)
    amount: float = Field(gt=0)
    card_number: str = Field(min_length=12, max_length=19)
    expiry: str = Field(min_length=3, max_length=7)
    cvv: str = Field(min_length=3, max_length=4)
    cardholder_name: str = Field(min_length=2, max_length=100)


class PaymentResponse(BaseModel):
    success: bool
    message: str
    booking_id: int
    transaction_id: Optional[str] = None
    amount: Optional[float] = None


# ---------- Refunds ----------

class RefundPreviewResponse(BaseModel):
    booking_id: int
    booking_reference: str
    eligible: bool
    reason: Optional[str] = None

    refund_amount: Decimal
    refund_percentage: int            # 0–100

    paid_amount: Decimal
    departure_time: datetime
    hours_until_departure: Optional[float] = None


class RefundRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    booking_reference: str
    status: str
    refund_amount: Optional[Decimal] = None
    message: str = "Refund requested. Pending admin review."