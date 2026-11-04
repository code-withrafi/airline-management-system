# app/ml/features.py
"""
Shared feature engineering for ML models.

All feature dictionaries produced here are ordered consistently so
they can be fed to pandas DataFrames for training and to numpy arrays
for prediction without reordering.
"""

from datetime import datetime
from typing import Any


# ------------------------------------------------------------------
# No-Show Prediction Features
# ------------------------------------------------------------------

NO_SHOW_FEATURE_ORDER = [
    "days_until_departure",
    "fare_amount",
    "is_business_class",
    "day_of_week",
    "hour_of_departure",
    "is_weekend",
    "route_distance_km",
    "passenger_booking_count",
]


def no_show_features_from_booking(
    booking,
    *,
    passenger_booking_count: int = 0,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """
    Build a feature dict for one booking.

    `booking` must have `.flight` (with `.route`), `.booked_at`,
    `.fare_amount`, and `.seat` (with `.seat_class`) loaded.

    `passenger_booking_count` is the passenger's total prior bookings —
    used as a proxy for trustworthiness / reliability.
    """
    ref = reference_time or datetime.utcnow()
    flight = booking.flight
    route = flight.route
    seat = booking.seat

    days_until = max(0, (flight.departure_time - ref).total_seconds() / 86400.0)

    seat_class_value = (
        seat.seat_class.value
        if seat is not None and hasattr(seat.seat_class, "value")
        else str(getattr(seat, "seat_class", "ECONOMY"))
    )
    is_business = int(seat_class_value.upper() == "BUSINESS")

    dow = flight.departure_time.weekday()   # 0 = Monday

    return {
        "days_until_departure": float(days_until),
        "fare_amount": float(booking.fare_amount or 0.0),
        "is_business_class": int(is_business),
        "day_of_week": int(dow),
        "hour_of_departure": int(flight.departure_time.hour),
        "is_weekend": int(dow >= 5),
        "route_distance_km": int(route.distance_km if route else 0),
        "passenger_booking_count": int(passenger_booking_count),
    }


def no_show_features_row(features: dict[str, Any]) -> list[float]:
    """Convert a feature dict into an ordered list for the model."""
    return [features[k] for k in NO_SHOW_FEATURE_ORDER]