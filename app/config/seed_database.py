from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.config.database import SessionLocal
from app.models import (
    User,
    UserRole,
    Staff,
    Airport,
    Route,
    Aircraft,
    AircraftStatus,
    Seat,
    SeatClass,
    SeatPosition,
)
from app.utils.security import hash_password


# ============================================================
# ADMIN CONFIGURATION
# ============================================================

ADMIN_EMAIL = "admin@airline.local"
ADMIN_PASSWORD = "Admin@12345"

# All seeded staff share this password. Keep it in one place
# so the seed script and any tests that log in as staff stay
# in sync.
STAFF_PASSWORD = "StaffPass123!"


# ============================================================
# AIRPORT DATA
# ============================================================

AIRPORT_DATA = [
    {
        "iata_code": "DAC",
        "icao_code": "VGHS",
        "name": "Hazrat Shahjalal International Airport",
        "city": "Dhaka",
        "country": "Bangladesh",
        "timezone": "Asia/Dhaka",
    },
    {
        "iata_code": "CGP",
        "icao_code": "VGEG",
        "name": "Shah Amanat International Airport",
        "city": "Chattogram",
        "country": "Bangladesh",
        "timezone": "Asia/Dhaka",
    },
    {
        "iata_code": "CXB",
        "icao_code": "VGCB",
        "name": "Cox's Bazar Airport",
        "city": "Cox's Bazar",
        "country": "Bangladesh",
        "timezone": "Asia/Dhaka",
    },
    {
        "iata_code": "JSR",
        "icao_code": "VGJR",
        "name": "Jashore Airport",
        "city": "Jashore",
        "country": "Bangladesh",
        "timezone": "Asia/Dhaka",
    },
]


# ============================================================
# AIRCRAFT DATA
# ============================================================

AIRCRAFT_DATA = [
    {
        "registration_number": "OM-A01",
        "manufacturer": "Airbus",
        "model": "A320-200",
        "seat_capacity": 30,
    },
    {
        "registration_number": "OM-B02",
        "manufacturer": "Boeing",
        "model": "737-800",
        "seat_capacity": 40,
    },
]


# ============================================================
# ROUTE DATA
# ============================================================

ROUTE_DATA = [
    {
        "origin": "DAC",
        "destination": "CGP",
        "distance_km": 214,
        "duration": 55,
    },
    {
        "origin": "CGP",
        "destination": "DAC",
        "distance_km": 214,
        "duration": 55,
    },
    {
        "origin": "DAC",
        "destination": "CXB",
        "distance_km": 312,
        "duration": 65,
    },
    {
        "origin": "DAC",
        "destination": "JSR",
        "distance_km": 147,
        "duration": 45,
    },
]


# ============================================================
# STAFF DATA
# ============================================================

STAFF_DATA = [
    {
        "email": "staff1@airline.local",
        "password": STAFF_PASSWORD,
        "employee_id": "EMP001",
        "first_name": "Rahim",
        "last_name": "Ahmed",
        "phone": "+8801700000001",
        "position": "Check-in Officer",
    },
    {
        "email": "staff2@airline.local",
        "password": STAFF_PASSWORD,
        "employee_id": "EMP002",
        "first_name": "Karim",
        "last_name": "Hasan",
        "phone": "+8801700000002",
        "position": "Ground Staff",
    },
    {
        "email": "staff3@airline.local",
        "password": STAFF_PASSWORD,
        "employee_id": "EMP003",
        "first_name": "Nusrat",
        "last_name": "Jahan",
        "phone": "+8801700000003",
        "position": "Supervisor",
    },
    {
        "email": "sam@staff.local",
        "password": STAFF_PASSWORD,
        "employee_id": "EMP004",
        "first_name": "Sam",
        "last_name": "Staff",
        "phone": "+8801700000004",
        "position": "Ground Staff",
    },
    {
        "email": "peggy@airline.local",
        "password": STAFF_PASSWORD,
        "employee_id": "EMP005",
        "first_name": "Peggy",
        "last_name": "Carter",
        "phone": "+8801700000005",
        "position": "Supervisor",
    },
]


# ============================================================
# SEAT GENERATION
# ============================================================

def generate_seats(
    session,
    aircraft: Aircraft,
) -> int:
    """
    Generate seats automatically for an aircraft.

    Layout:
        A B C D E F

    Rows 1-2:
        Business

    Remaining rows:
        Economy
    """

    existing_count = session.scalar(
        select(Seat)
        .where(Seat.aircraft_id == aircraft.id)
        .limit(1)
    )

    if existing_count is not None:
        return 0

    seats_per_row = 6

    total_rows = (
        aircraft.seat_capacity // seats_per_row
    )

    seat_letters = ["A", "B", "C", "D", "E", "F"]

    position_map = {
        "A": SeatPosition.WINDOW,
        "B": SeatPosition.MIDDLE,
        "C": SeatPosition.AISLE,
        "D": SeatPosition.AISLE,
        "E": SeatPosition.MIDDLE,
        "F": SeatPosition.WINDOW,
    }

    business_rows = 2

    created = 0

    for row in range(1, total_rows + 1):

        if row <= business_rows:
            seat_class = SeatClass.BUSINESS
        else:
            seat_class = SeatClass.ECONOMY

        for letter in seat_letters:

            seat = Seat(
                aircraft_id=aircraft.id,
                seat_number=f"{row}{letter}",
                seat_class=seat_class,
                row_number=row,
                position=position_map[letter],
            )

            session.add(seat)
            created += 1

    return created


# ============================================================
# SEED AIRPORTS
# ============================================================

def seed_airports(session):
    print("\n[1/5] Seeding airports...")

    airports = {}

    for data in AIRPORT_DATA:

        airport = session.scalar(
            select(Airport)
            .where(
                Airport.iata_code == data["iata_code"]
            )
        )

        if airport is None:

            airport = Airport(
                iata_code=data["iata_code"],
                icao_code=data["icao_code"],
                name=data["name"],
                city=data["city"],
                country=data["country"],
                timezone=data["timezone"],
                is_active=True,
            )

            session.add(airport)

            print(
                f"  + Created airport: "
                f"{data['iata_code']} - {data['city']}"
            )

        else:

            print(
                f"  = Airport already exists: "
                f"{data['iata_code']}"
            )

        airports[data["iata_code"]] = airport

    session.flush()

    return airports


# ============================================================
# SEED AIRCRAFT
# ============================================================

def seed_aircraft(session):
    print("\n[2/5] Seeding aircraft...")

    aircraft_list = []

    for data in AIRCRAFT_DATA:

        aircraft = session.scalar(
            select(Aircraft)
            .where(
                Aircraft.registration_number
                == data["registration_number"]
            )
        )

        if aircraft is None:

            aircraft = Aircraft(
                registration_number=data["registration_number"],
                manufacturer=data["manufacturer"],
                model=data["model"],
                seat_capacity=data["seat_capacity"],
                status=AircraftStatus.ACTIVE,
            )

            session.add(aircraft)

            session.flush()

            created_seats = generate_seats(
                session,
                aircraft
            )

            print(
                f"  + Created aircraft: "
                f"{aircraft.registration_number} "
                f"({aircraft.model})"
            )

            print(
                f"    + Generated {created_seats} seats"
            )

        else:

            print(
                f"  = Aircraft already exists: "
                f"{aircraft.registration_number}"
            )

        aircraft_list.append(aircraft)

    session.flush()

    return aircraft_list


# ============================================================
# SEED ROUTES
# ============================================================

def seed_routes(session, airports):
    print("\n[3/5] Seeding routes...")

    routes = []

    for data in ROUTE_DATA:

        origin = airports[data["origin"]]
        destination = airports[data["destination"]]

        route = session.scalar(
            select(Route)
            .where(
                Route.origin_airport_id == origin.id,
                Route.destination_airport_id
                == destination.id,
            )
        )

        if route is None:

            route = Route(
                origin_airport_id=origin.id,
                destination_airport_id=destination.id,
                distance_km=data["distance_km"],
                estimated_duration_minutes=data["duration"],
                is_active=True,
            )

            session.add(route)

            print(
                f"  + Created route: "
                f"{data['origin']} -> "
                f"{data['destination']}"
            )

        else:

            print(
                f"  = Route already exists: "
                f"{data['origin']} -> "
                f"{data['destination']}"
            )

        routes.append(route)

    session.flush()

    return routes


# ============================================================
# SEED ADMIN + STAFF
# ============================================================

def seed_users_and_staff(session):
    print("\n[4/5] Seeding users and staff...")

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    admin = session.scalar(
        select(User)
        .where(User.email == ADMIN_EMAIL)
    )

    if admin is None:

        admin = User(
            email=ADMIN_EMAIL,
            password_hash=hash_password(
                ADMIN_PASSWORD
            ),
            role=UserRole.ADMIN,
            is_active=True,
        )

        session.add(admin)

        print(
            f"  + Created admin: {ADMIN_EMAIL}"
        )

    else:

        print(
            f"  = Admin already exists: "
            f"{ADMIN_EMAIL}"
        )

    # --------------------------------------------------------
    # STAFF
    # --------------------------------------------------------

    staff_list = []

    for data in STAFF_DATA:

        user = session.scalar(
            select(User)
            .where(User.email == data["email"])
        )

        if user is None:

            user = User(
                email=data["email"],
                password_hash=hash_password(
                    data["password"]
                ),
                role=UserRole.STAFF,
                is_active=True,
            )

            session.add(user)
            session.flush()

            print(
                f"  + Created staff user: "
                f"{data['email']}"
            )

        else:

            print(
                f"  = Staff user already exists: "
                f"{data['email']}"
            )

        staff = session.scalar(
            select(Staff)
            .where(
                Staff.employee_id
                == data["employee_id"]
            )
        )

        if staff is None:

            staff = Staff(
                user_id=user.id,
                employee_id=data["employee_id"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                phone=data["phone"],
                position=data["position"],
            )

            session.add(staff)

            print(
                f"    + Created employee: "
                f"{data['employee_id']}"
            )

        else:

            print(
                f"    = Employee already exists: "
                f"{data['employee_id']}"
            )

        staff_list.append(staff)

    session.flush()

    return admin, staff_list


# ============================================================
# DISPLAY SUMMARY
# ============================================================

def print_summary(session):
    print("\n[5/5] Database seed summary")
    print("=" * 60)

    airport_count = session.query(Airport).count()
    aircraft_count = session.query(Aircraft).count()
    seat_count = session.query(Seat).count()
    route_count = session.query(Route).count()
    user_count = session.query(User).count()
    staff_count = session.query(Staff).count()

    print(f"Airports : {airport_count}")
    print(f"Aircraft : {aircraft_count}")
    print(f"Seats    : {seat_count}")
    print(f"Routes   : {route_count}")
    print(f"Users    : {user_count}")
    print(f"Staff    : {staff_count}")

    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def seed_database():

    print("=" * 60)
    print("AIRLINE MANAGEMENT SYSTEM")
    print("DATABASE SEED")
    print("=" * 60)

    session = SessionLocal()

    try:

        airports = seed_airports(session)

        seed_aircraft(session)

        seed_routes(
            session,
            airports
        )

        seed_users_and_staff(session)

        session.commit()

        print_summary(session)

        print("\nDatabase seeding completed successfully.")

        print("\nAdmin login:")
        print(f"Email    : {ADMIN_EMAIL}")
        print(f"Password : {ADMIN_PASSWORD}")

        print("\nStaff logins (all share one password):")
        print(f"Password : {STAFF_PASSWORD}")
        print(
            "Emails   : "
            + ", ".join(d["email"] for d in STAFF_DATA)
        )

        print("\nIMPORTANT:")
        print(
            "Change the default admin password "
            "before production deployment."
        )

    except Exception as error:

        session.rollback()

        print(
            "\nERROR: Database seeding failed."
        )

        print(
            f"Reason: {error}"
        )

        raise

    finally:

        session.close()


if __name__ == "__main__":
    seed_database()