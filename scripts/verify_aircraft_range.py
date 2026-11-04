# scripts/verify_aircraft_range.py
"""
Verify no ATR aircraft is assigned to routes > 600 km in the DB.

Also shows which aircraft operate long-haul routes.
"""
from datetime import datetime

from app.config.database import SessionLocal
from app.models.aircraft import Aircraft
from app.models.flight import Flight


THRESHOLD_KM = 600
SHORT_HAUL_ONLY = {"atr", "de havilland", "dhc", "cessna", "beechcraft"}


def main():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        flights = db.query(Flight).filter(Flight.departure_time >= now).all()

        violations = []
        for f in flights:
            if not f.route or not f.route.distance_km:
                continue
            aircraft = db.query(Aircraft).filter(Aircraft.id == f.aircraft_id).first()
            if not aircraft:
                continue
            manufacturer = (aircraft.manufacturer or "").lower()
            if f.route.distance_km > THRESHOLD_KM and manufacturer in SHORT_HAUL_ONLY:
                violations.append((f, aircraft))

        print("=" * 70)
        print("Aircraft Range Verification")
        print("=" * 70)
        print(f"Total future flights:      {len(flights)}")
        print(f"ATR violations (>600 km):  {len(violations)}")
        print()

        if violations:
            print("⚠️  VIOLATIONS FOUND:")
            for f, a in violations[:20]:
                print(f"  {f.flight_number}  {a.manufacturer} {a.model}  "
                      f"on {f.route.distance_km} km route")
        else:
            print("✅ No ATR turboprops assigned to long-haul routes.")

        # Which aircraft fly long-haul routes?
        print()
        print("Aircraft operating long-haul routes (>600 km):")
        seen = {}
        for f in flights:
            if not f.route or f.route.distance_km <= THRESHOLD_KM:
                continue
            aircraft = db.query(Aircraft).filter(Aircraft.id == f.aircraft_id).first()
            if not aircraft:
                continue
            if aircraft.id not in seen:
                seen[aircraft.id] = (aircraft, f.route.distance_km)
            else:
                # Track max distance seen per aircraft
                _, prev_max = seen[aircraft.id]
                seen[aircraft.id] = (aircraft, max(prev_max, f.route.distance_km))

        for aircraft_id, (aircraft, max_km) in seen.items():
            print(f"  {aircraft.manufacturer:<12} {aircraft.model:<20} "
                  f"max {max_km} km")

        print()
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    main()