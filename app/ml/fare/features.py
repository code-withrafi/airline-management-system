# app/ml/fare/features.py
"""
Feature engineering for the fare prediction model.

The model predicts a *multiplier* on the route's distance-based base
fare. All features must be derivable at schedule-generation time.
"""

from datetime import datetime
from typing import Any


FARE_FEATURE_ORDER = [
    "route_distance_km",
    "days_until_departure",
    "day_of_week",
    "hour_of_departure",
    "is_weekend",
    "is_peak_hour",
    "is_holiday_season",
    "month",
]


PEAK_HOURS = {7, 8, 9, 17, 18, 19}
HOLIDAY_MONTHS = {12, 1, 6, 7}   # winter break + summer season


def fare_features(
    *,
    route_distance_km: int,
    departure_time: datetime,
    reference_time: datetime | None = None,
) -> dict[str, Any]:
    """Build the feature dict for one flight."""
    ref = reference_time or datetime.utcnow()

    days_until = max(0.0, (departure_time - ref).total_seconds() / 86400.0)
    dow = departure_time.weekday()          # 0 = Monday
    hour = departure_time.hour
    month = departure_time.month

    return {
        "route_distance_km": int(route_distance_km),
        "days_until_departure": float(days_until),
        "day_of_week": int(dow),
        "hour_of_departure": int(hour),
        "is_weekend": int(dow >= 5),
        "is_peak_hour": int(hour in PEAK_HOURS),
        "is_holiday_season": int(month in HOLIDAY_MONTHS),
        "month": int(month),
    }


def fare_features_row(features: dict[str, Any]) -> list[float]:
    """Convert the feature dict to an ordered list for the model."""
    return [features[k] for k in FARE_FEATURE_ORDER]


def base_fare_for_route(distance_km: int) -> float:
    """
    Distance-based economy base fare (in USD).

    Uses a piecewise formula calibrated to realistic airline pricing:
      - Very short (< 500 km):     ~$28 – $50
      - Short (500–1,500 km):      ~$45 – $95
      - Medium (1,500–3,000 km):   ~$88 – $155
      - Long-haul (3,000+ km):     ~$140 – $450

    Formula: fixed_cost + variable_cost_per_km * distance
    where the per-km rate decreases with distance (economies of scale).
    """
    if distance_km <= 0:
        return 25.0

    # Fixed cost — every flight has the same base cost (fuel, crew, gate)
    fixed = 20.0

    # Variable cost — decreases as distance grows
    if distance_km <= 500:
        per_km = 0.06
    elif distance_km <= 1500:
        per_km = 0.05
    elif distance_km <= 3000:
        per_km = 0.045
    else:
        per_km = 0.040

    base = fixed + distance_km * per_km
    return round(base, 2)