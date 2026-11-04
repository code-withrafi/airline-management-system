# scripts/list_active_passengers.py
"""List passengers who have at least one booking."""
from app.config.database import SessionLocal
from app.models.booking import Booking
from app.models.passenger import Passenger


def main():
    db = SessionLocal()
    try:
        print(f"{'ID':<5} {'Email':<35} {'Bookings':<10}")
        print("-" * 55)

        found = False
        for p in db.query(Passenger).all():
            n = db.query(Booking).filter(Booking.passenger_id == p.id).count()
            if n == 0:
                continue
            found = True
            email = p.user.email if p.user else "(companion)"
            print(f"{p.id:<5} {email:<35} {n:<10}")

        if not found:
            print("(no passengers have bookings yet)")
    finally:
        db.close()


if __name__ == "__main__":
    main()