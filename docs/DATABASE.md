# 🗄️ Database Design

> **Airline Management System**
> PostgreSQL 14+ · SQLAlchemy 2.x · 17 tables · 6 enums · full referential integrity.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Entity-Relationship Diagram (ERD)](#2-entity-relationship-diagram-erd)
3. [Table Reference](#3-table-reference)
4. [Booking Status State Machine](#4-booking-status-state-machine)
5. [Indexes](#5-indexes)
6. [Data Seeding](#6-data-seeding)
7. [Migration Scripts](#7-migration-scripts)

---

## 1. Overview

The system uses **PostgreSQL 14+** with **SQLAlchemy 2.x** as the ORM.

Every entity follows a consistent pattern:

- `id` — integer primary key (auto-increment)
- `created_at` / `updated_at` — UTC timestamps
- Foreign-key relationships with explicit `ondelete` behavior where needed

---

## 2. Entity-Relationship Diagram (ERD)

**Diagram — Entity-Relationship Diagram**

```mermaid
erDiagram
    USER ||--o| PASSENGER : "has profile"
    USER ||--o| STAFF : "has profile"
    USER {
        int id PK
        string email UK
        string password_hash
        enum role "ADMIN | STAFF | PASSENGER"
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    PASSENGER ||--o{ BOOKING : "makes"
    PASSENGER {
        int id PK
        int user_id FK "UK, nullable for companions"
        string first_name
        string last_name
        string phone
        date date_of_birth
        string passport_number
        string address
        datetime created_at
        datetime updated_at
    }

    STAFF ||--o| USER : "linked to"
    STAFF {
        int id PK
        int user_id FK "UK"
        string staff_number UK
        string first_name
        string last_name
        string phone
        enum role "CHECK_IN_OFFICER | ..."
        boolean is_active
        datetime created_at
    }

    AIRPORT ||--o{ ROUTE : "origin"
    AIRPORT ||--o{ ROUTE : "destination"
    AIRPORT {
        int id PK
        string iata_code UK
        string icao_code UK
        string name
        string city
        string country
        string timezone
        boolean is_active
    }

    ROUTE ||--o{ FLIGHT : "operates"
    ROUTE {
        int id PK
        int origin_airport_id FK
        int destination_airport_id FK
        int distance_km
        int estimated_duration_minutes
        boolean is_active
    }

    AIRCRAFT ||--o{ FLIGHT : "flies"
    AIRCRAFT ||--o{ SEAT : "contains"
    AIRCRAFT {
        int id PK
        string registration_number UK
        string manufacturer
        string model
        int seat_capacity
        enum status "ACTIVE | MAINTENANCE | RETIRED"
    }

    SEAT ||--o{ BOOKING : "reserved for"
    SEAT {
        int id PK
        int aircraft_id FK
        string seat_number
        enum seat_class "ECONOMY | BUSINESS"
        int row_number
        enum position "WINDOW | MIDDLE | AISLE"
    }

    FLIGHT ||--o{ BOOKING : "booked on"
    FLIGHT ||--o{ FLIGHT_STAFF : "assigned"
    FLIGHT {
        int id PK
        string flight_number UK
        int route_id FK
        int aircraft_id FK
        datetime departure_time
        datetime arrival_time
        numeric base_fare "economy fare"
        enum status "SCHEDULED | BOARDING | ..."
        string boarding_gate
    }

    BOOKING ||--o| BOARDING_PASS : "generates"
    BOOKING ||--o| CHECKIN : "has"
    BOOKING ||--o{ BAGGAGE : "carries"
    BOOKING {
        int id PK
        string booking_reference UK
        int passenger_id FK
        int flight_id FK
        int seat_id FK
        numeric fare_amount
        numeric refund_amount
        enum status "UNPAID | CONFIRMED | ..."
        datetime booked_at
        datetime cancelled_at
    }

    STAFF ||--o{ FLIGHT_STAFF : "assigned to"
    FLIGHT_STAFF {
        int id PK
        int flight_id FK
        int staff_id FK
        enum role "PILOT | CABIN_CREW | ..."
    }

    CHECKIN ||--o| BOARDING_PASS : "issues"
    CHECKIN {
        int id PK
        int booking_id FK "UK"
        datetime checked_in_at
        int checked_in_by_staff_id FK
    }

    BOARDING_PASS {
        int id PK
        int booking_id FK "UK"
        int checkin_id FK "UK"
        string boarding_pass_number UK
        string boarding_gate
        string boarding_group
        datetime issued_at
    }

    BAGGAGE {
        int id PK
        int booking_id FK
        string bag_tag UK
        numeric weight_kg
        datetime created_at
    }
```

---

## 3. Table Reference

### 3.1 `users`

Primary authentication table for all roles.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK | Auto-increment |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | Lowercased on insert |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash |
| `role` | ENUM | NOT NULL | `ADMIN` · `STAFF` · `PASSENGER` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Soft-disable accounts |
| `created_at` | DATETIME | NOT NULL | UTC |
| `updated_at` | DATETIME | NOT NULL, ON UPDATE | UTC |

**Relationships**

- 1:1 with `passengers` (nullable)
- 1:1 with `staff` (nullable)

---

### 3.2 `passengers`

Profile for passenger users (also used for companions without accounts).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | INTEGER | PK | |
| `user_id` | INTEGER | FK → `users.id`, UNIQUE, NULLABLE | `NULL` for companions |
| `first_name` | VARCHAR(100) | NOT NULL | |
| `last_name` | VARCHAR(100) | NOT NULL | |
| `phone` | VARCHAR(30) | NOT NULL | |
| `date_of_birth` | DATE | NULLABLE | |
| `passport_number` | VARCHAR(50) | NOT NULL | |
| `address` | VARCHAR(500) | NULLABLE | |

**Relationships**

- 1:N with `bookings`

---

### 3.3 `aircraft`

Fleet inventory; each aircraft contains a fixed number of seats.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK |
| `registration_number` | VARCHAR(50) | UNIQUE, NOT NULL |
| `manufacturer` | VARCHAR(100) | NOT NULL |
| `model` | VARCHAR(100) | NOT NULL |
| `seat_capacity` | INTEGER | NOT NULL, > 0 |
| `status` | ENUM | `ACTIVE` · `MAINTENANCE` · `RETIRED` |

---

### 3.4 `seats`

Individual seat inventory per aircraft.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK |
| `aircraft_id` | INTEGER | FK → `aircraft.id`, NOT NULL |
| `seat_number` | VARCHAR(10) | NOT NULL |
| `seat_class` | VARCHAR(8) | `ECONOMY` · `BUSINESS` |
| `row_number` | INTEGER | NOT NULL |
| `position` | VARCHAR(6) | `WINDOW` · `MIDDLE` · `AISLE` |

> **Note:** Seats are auto-generated via `SeatGenerator.generate(capacity)` when an aircraft is created.

---

### 3.5 `flights`

Scheduled operations of a route by an aircraft.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK |
| `flight_number` | VARCHAR(20) | UNIQUE, NOT NULL, INDEXED |
| `route_id` | INTEGER | FK → `routes.id` |
| `aircraft_id` | INTEGER | FK → `aircraft.id` |
| `departure_time` | DATETIME | NOT NULL, INDEXED |
| `arrival_time` | DATETIME | NOT NULL |
| `base_fare` | NUMERIC(10,2) | NOT NULL — **economy fare** |
| `status` | ENUM | `SCHEDULED` · `BOARDING` · `DEPARTED` · `ARRIVED` · `DELAYED` · `CANCELLED` |
| `boarding_gate` | VARCHAR(20) | NULLABLE |

**Check constraint:** `departure_time < arrival_time`

---

### 3.6 `bookings`

The core transactional table.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PK |
| `booking_reference` | VARCHAR(20) | UNIQUE, NOT NULL |
| `passenger_id` | INTEGER | FK → `passengers.id` |
| `flight_id` | INTEGER | FK → `flights.id` |
| `seat_id` | INTEGER | FK → `seats.id` |
| `fare_amount` | NUMERIC(10,2) | NOT NULL |
| `refund_amount` | NUMERIC(10,2) | NULLABLE |
| `status` | ENUM | `UNPAID` · `CONFIRMED` · `CHECKED_IN` · `COMPLETED` · `CANCELLED` · `REFUND_REQUESTED` · `REFUNDED` |
| `booked_at` | DATETIME | NOT NULL |
| `cancelled_at` | DATETIME | NULLABLE |

**Unique constraint:** `(flight_id, seat_id)` — prevents double-booking a seat on the same flight.

---

## 4. Booking Status State Machine

**Diagram 7 — Booking Status State Machine**

![Booking Status State Machine](./diagrams/7.Booking%20Status%20State%20Machine.png)

---

## 5. Indexes

| Table | Index | Purpose |
|---|---|---|
| `users` | `email` | Login lookup |
| `passengers` | `user_id` | Join from user |
| `passengers` | `passport_number` | Passport uniqueness check |
| `aircraft` | `registration_number` | Fast aircraft lookup |
| `seats` | `aircraft_id` | Fetch seat map |
| `flights` | `flight_number` | Search |
| `flights` | `departure_time` | Date-range queries |
| `bookings` | `booking_reference` | Reference lookup |
| `bookings` | `(flight_id, seat_id)` UNIQUE | Prevent double-booking |

---

## 6. Data Seeding

The database is seeded by `app/config/seed_database.py` with:

- **Airports:** Dhaka (DAC), Cox's Bazar (CXB), Bangkok (BKK), Guangzhou (CAN), Chittagong (CGP), Jashore (JSR)
- **Aircraft:** 4 real aircraft + test variants
- **Routes:** DAC ↔ CXB, DAC ↔ BKK, CGP ↔ DAC, and others
- **Users:** 1 admin, 1 staff, 1 passenger
- **Flights:** Several scheduled flights per route

---

## 7. Migration Scripts

When the schema changes, run the appropriate migration:

```bash
python migrate_multi_passenger.py   # Example migration
python backfill_seats.py            # Fix any missing seats
```

**Always back up the database first:**

```bash
pg_dump -U postgres airline_management > backup.sql
```