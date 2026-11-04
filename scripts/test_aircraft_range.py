# scripts/test_aircraft_range.py
"""Unit test for the aircraft range rule."""
from app.services.schedule.aircraft_range import (
    aircraft_can_serve_route,
    can_operate_long_haul,
    is_route_long_haul,
)


class _Fake:
    def __init__(self, manufacturer, model=""):
        self.manufacturer = manufacturer
        self.model = model


def main():
    print("=" * 70)
    print("Aircraft Range Rule — Unit Test")
    print("=" * 70)

    cases = [
        # (aircraft, distance_km, expected)
        (_Fake("ATR", "ATR 72-600"),       300, True),
        (_Fake("ATR", "ATR 72-600"),       600, True),
        (_Fake("ATR", "ATR 72-600"),       601, False),
        (_Fake("ATR", "ATR 72-600"),       700, False),
        (_Fake("ATR", "ATR 72-600"),      2885, False),
        (_Fake("ATR", "ATR 42-600"),      2442, False),
        (_Fake("Boeing", "737-800"),      2885, True),
        (_Fake("Boeing", "Boeing 737-800"), 5000, True),
        (_Fake("Airbus", "A320"),          147, True),
        (_Fake("Airbus", "A350-900"),     2885, True),
        (_Fake("Airbus", "A330-300"),     5000, True),
        (_Fake("Unknown", "Test"),        3000, True),  # permissive default
    ]

    print(f"\n{'Manufacturer':<12} {'Model':<18} {'Distance':<10} "
          f"{'Allowed':<8} {'Expected':<8} Result")
    print("-" * 70)

    all_ok = True
    for aircraft, distance, expected in cases:
        actual = aircraft_can_serve_route(aircraft, distance)
        ok = actual == expected
        all_ok = all_ok and ok
        icon = "✅" if ok else "❌"
        print(f"{aircraft.manufacturer:<12} {aircraft.model:<18} "
              f"{distance:<10} {str(actual):<8} {str(expected):<8} {icon}")

    print()
    print("=" * 70)
    if all_ok:
        print("🎉 All tests passed!")
    else:
        print("⚠️ Some tests failed.")
    print("=" * 70)


if __name__ == "__main__":
    main()