# scripts/verify_fares.py
"""Show how fares vary by route and time using the ML fare model."""
from datetime import datetime

from app.config.database import SessionLocal
from app.ml.fare.service import FarePredictorService
from app.models.route import Route


def main():
    db = SessionLocal()
    try:
        svc = FarePredictorService(db)
        routes = db.query(Route).limit(5).all()

        # Dates to test
        dates = [
            ("Mon 8am",  datetime(2026, 11, 16, 8, 0)),
            ("Mon 2pm",  datetime(2026, 11, 16, 14, 0)),
            ("Sat 10am", datetime(2026, 11, 21, 10, 0)),
            ("Xmas 8am", datetime(2026, 12, 25, 8, 0)),
            ("Xmas 2pm", datetime(2026, 12, 25, 14, 0)),
        ]

        print("=" * 80)
        print("Fare variation by route and time")
        print("=" * 80)

        for r in routes:
            origin = r.origin_airport.iata_code if r.origin_airport else "?"
            destination = r.destination_airport.iata_code if r.destination_airport else "?"
            print(f"\nRoute {r.id}: {origin} → {destination}  ({r.distance_km} km)")
            print("-" * 80)

            for label, dt in dates:
                fare = svc.predict(route=r, departure_time=dt)
                mult = svc.predict_multiplier_only(route=r, departure_time=dt)
                print(f"  {label:<10}  multiplier={mult:.3f}  fare=${fare}")

    finally:
        db.close()


if __name__ == "__main__":
    main()