# app/services/pricing.py
"""
Central pricing rules for seat classes.

Base fare on a Flight represents the *economy* fare.
Business class is priced as a multiplier on top of economy.
"""

from decimal import Decimal, ROUND_HALF_UP


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

BUSINESS_MULTIPLIER = Decimal("2.5")
ECONOMY_MULTIPLIER  = Decimal("1.0")

# Map by seat_class string (as stored in DB — "ECONOMY" | "BUSINESS")
_MULTIPLIERS = {
    "ECONOMY":  ECONOMY_MULTIPLIER,
    "BUSINESS": BUSINESS_MULTIPLIER,
}


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def get_multiplier(seat_class) -> Decimal:
    """
    Accepts a SeatClass enum OR its string value ('ECONOMY'/'BUSINESS').
    Falls back to 1.0 for unknown classes so nothing ever breaks.
    """
    key = getattr(seat_class, "value", str(seat_class)).upper()
    return _MULTIPLIERS.get(key, ECONOMY_MULTIPLIER)


def calculate_fare(base_fare, seat_class) -> Decimal:
    """
    Compute the fare for a seat on a flight.

    base_fare  — the flight's economy fare (Decimal or numeric)
    seat_class — SeatClass enum or 'ECONOMY'/'BUSINESS' string

    Returns a Decimal quantized to 2 decimal places.
    """
    base = Decimal(str(base_fare))
    multiplier = get_multiplier(seat_class)
    total = base * multiplier
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def price_breakdown(base_fare, seat_class) -> dict:
    """
    Handy for the UI: returns both the base and the surcharge so the
    frontend can display "Base $35.00 + Business surcharge $52.50".
    """
    base = Decimal(str(base_fare)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    multiplier = get_multiplier(seat_class)
    total = calculate_fare(base, seat_class)
    surcharge = (total - base).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "base_fare": base,
        "multiplier": multiplier,
        "surcharge": surcharge,
        "total_fare": total,
    }