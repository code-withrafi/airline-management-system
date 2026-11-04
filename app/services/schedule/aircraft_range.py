# app/services/schedule/aircraft_range.py
"""
Aircraft range rules for the schedule generator.

Airline business rule:
  - Short-haul routes (≤ 600 km) can be served by ANY aircraft,
    including ATR turboprops.
  - Long-haul routes (> 600 km) require a jet (Boeing or Airbus).
    ATR turboprops MUST NOT be assigned.
"""


# Manufacturers that CAN fly long-haul.
# Matched case-insensitively against Aircraft.manufacturer.
LONG_HAUL_MANUFACTURERS = {
    "boeing",
    "airbus",
    "embraer",
    "bombardier",
    "comac",
}

# Manufacturers that MUST NOT fly long-haul.
SHORT_HAUL_MANUFACTURERS = {
    "atr",
    "de havilland",
    "dhc",
    "cessna",
    "beechcraft",
    "pilatus",
}

# Distance threshold (km) above which short-haul-only aircraft are forbidden
LONG_HAUL_THRESHOLD_KM = 600


def can_operate_long_haul(aircraft) -> bool:
    """
    Return True if the aircraft can fly a route longer than
    LONG_HAUL_THRESHOLD_KM.

    Uses the manufacturer string. If the manufacturer is unknown,
    defaults to True (permissive) so unknown/new aircraft aren't
    silently excluded.
    """
    manufacturer = (getattr(aircraft, "manufacturer", "") or "").strip().lower()

    if manufacturer in LONG_HAUL_MANUFACTURERS:
        return True
    if manufacturer in SHORT_HAUL_MANUFACTURERS:
        return False

    # Fallback: inspect the model name for hints
    model = (getattr(aircraft, "model", "") or "").strip().lower()
    if "atr" in model or "dash" in model or "dhc" in model:
        return False

    return True    # permissive default


def is_route_long_haul(distance_km: int) -> bool:
    """Return True if the route distance exceeds the long-haul threshold."""
    return int(distance_km or 0) > LONG_HAUL_THRESHOLD_KM


def aircraft_can_serve_route(aircraft, distance_km: int) -> bool:
    """
    Return True if the aircraft is suitable for a route of the
    given distance.

    - Short route (≤ 600 km): any aircraft ✓
    - Long route (> 600 km): must be long-haul capable
    """
    if not is_route_long_haul(distance_km):
        return True
    return can_operate_long_haul(aircraft)