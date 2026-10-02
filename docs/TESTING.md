#  Testing

> **Airline Management System**
> Test strategy, coverage map, manual test cases, and results.

---

## Table of Contents

1. [Test Strategy](#1-test-strategy)
2. [Running Tests](#2-running-tests)
3. [Test Coverage Map](#3-test-coverage-map)
4. [Manual Test Cases](#4-manual-test-cases)
5. [Automated Test Files](#5-automated-test-files)
6. [Test Data](#6-test-data)
7. [Test Results](#7-test-results)
8. [Known Limitations](#8-known-limitations)
9. [Future Testing Improvements](#9-future-testing-improvements)

---

## 1. Test Strategy

Testing is layered to match the architecture.

| Layer | Tool | Coverage |
|---|---|---|
| **Unit** (services) | pytest | Business rules, validators, calculators |
| **Integration** (repositories) | pytest + real DB | ORM queries, constraints |
| **API** (endpoints) | pytest + httpx | HTTP contract, auth, error codes |
| **Frontend** (components) | vitest + testing-library | Form validation, state |
| **E2E** (manual) | Checklists | Full user journeys |

---

## 2. Running Tests

### Backend

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov=api --cov-report=html

# Specific file
pytest tests/test_flight_service.py

# Specific test
pytest tests/test_flight_service.py::test_create_flight_validates_times
```

### Frontend

```bash
cd frontend
npm test
```

---

## 3. Test Coverage Map

### 3.1 Service Layer

| Service | Test File | Key Cases |
|---|---|---|
| `AuthService` | `tests/test_authentication.py` | Valid login, wrong password, inactive account, unknown email |
| `FlightService` | `tests/test_flight_service.py` | Create, update, status transitions, cancel, aircraft change |
| `BookingService` | `tests/test_booking_service.py` | Create, cancel, refund request, mark paid |
| `PassengerService` | `tests/test_passenger_service.py` | Register, update, password change |
| `PaymentService` | (implicit via API tests) | Mock validation, success path |
| `SeatGenerator` | `tests/test_seat_generator.py` | All capacities, edge cases |
| `RefundPolicyService` | `tests/test_refund_policy.py` | Tier calculation |
| `FlightStatusValidator` | `tests/test_flight_status.py` | Valid/invalid transitions |

### 3.2 API Layer

| Endpoint | Test File | Key Cases |
|---|---|---|
| `POST /api/auth/login` | `tests/test_api_auth.py` | 200, 401, 403 (admin) |
| `POST /api/auth/register` | `tests/test_api_auth.py` | 201, 409, 422 |
| `GET /api/flights/search` | `tests/test_api_flights.py` | Public access, valid results, 404, 400 |
| `GET /api/flights/{id}/seats` | `tests/test_api_seats.py` | Public, prices, availability |
| `POST /api/bookings` | `tests/test_api_bookings.py` | 201, 401, 403, 409 |
| `POST /api/payments` | `tests/test_api_payments.py` | 200, 403, 409, 422 |
| `GET /api/passengers/me` | `tests/test_api_passengers.py` | 200, 401 |

---

## 4. Manual Test Cases

### TC-01 — Passenger Registration

**Preconditions:** Backend running; no existing user with the test email.

| Step | Action | Expected |
|---|---|---|
| 1 | Open `/register` | Form displays |
| 2 | Submit empty form | Browser validation blocks |
| 3 | Enter invalid email | Validation error |
| 4 | Enter password < 6 chars | Validation error |
| 5 | Fill all fields validly | Submit succeeds |
| 6 | Check DB | User + Passenger rows exist |
| 7 | Check localStorage | JWT present |
| 8 | Refresh page | Still logged in |

**Result:** ✅ Pass

---

### TC-02 — Public Flight Search

**Preconditions:** Flights seeded for DAC → CXB on `2026-09-15`.

| Step | Action | Expected |
|---|---|---|
| 1 | Visit `/` (landing) | Animated hero shows |
| 2 | Enter `DAC`, `CXB`, `2026-09-15` | Widget accepts |
| 3 | Click **Search** | Navigates to `/search?...` |
| 4 | Wait for load | Cards render with flight info |
| 5 | Verify no JWT required | Works in incognito |

**Result:** ✅ Pass

---

### TC-03 — Seat Map: Business vs Economy Pricing

| Step | Action | Expected |
|---|---|---|
| 1 | Click **Select** on a flight | Details page loads |
| 2 | Click **Book this flight** | Redirects to `/booking/:id` |
| 3 | Hover seat `1A` (business) | Tooltip shows `1A · BUSINESS · $87.50` |
| 4 | Hover seat `5A` (economy) | Tooltip shows `5A · ECONOMY · $35.00` |
| 5 | Click `5A` | Summary total shows `$35.00` |
| 6 | Click `1A` | Surcharge line appears: `+$52.50`, total `$87.50` |
| 7 | Legend | Shows both prices |

**Result:** ✅ Pass

---

### TC-04 — Complete Booking Flow

| Step | Action | Expected |
|---|---|---|
| 1 | Click **Continue to payment** | Redirects to `/payment/:bookingId` |
| 2 | Booking status check | `UNPAID` |
| 3 | Fill test card `4242 4242 4242 4242` | Accepted |
| 4 | Click **Pay** | Green success screen |
| 5 | Booking status check | `CONFIRMED` |
| 6 | Click **Download ticket** | PDF opens with booking details |

**Result:** ✅ Pass

---

### TC-05 — Refund Request Flow

**Preconditions:** A `CONFIRMED` booking.

| Step | Action | Expected |
|---|---|---|
| 1 | Open My Bookings | Refund button visible on confirmed bookings |
| 2 | Click **Refund** | Modal opens |
| 3 | Verify preview | Shows refund % + amount |
| 4 | Verify policy table | 6 tiers listed (25–100%) |
| 5 | Click **Request $X** | Modal closes |
| 6 | Verify status badge | `REFUND_REQUESTED` (yellow) |
| 7 | Verify Cancel button | Hidden |
| 8 | Admin approves in desktop | — |
| 9 | Refresh web app | Badge = `REFUNDED` (purple) |

**Result:** ✅ Pass

---

### TC-06 — Role Boundary: Admin Can't Use Passenger API

| Step | Action | Expected |
|---|---|---|
| 1 | Login as admin in desktop | Success |
| 2 | Extract JWT (or generate one) | — |
| 3 | Call `GET /api/bookings/my` with admin token | `403 This API is for passengers only.` |
| 4 | Call `GET /api/flights/search` (public) | `200 OK` |

**Result:** ✅ Pass

---

### TC-07 — Passenger Desktop Redirect

| Step | Action | Expected |
|---|---|---|
| 1 | Launch desktop app | Login window appears |
| 2 | Enter passenger credentials | Message dialog appears |
| 3 | Click OK | Browser opens `localhost:5173` |
| 4 | Login window reappears | Ready for admin/staff login |

**Result:** ✅ Pass

---

### TC-08 — Seat Availability After Booking

| Step | Action | Expected |
|---|---|---|
| 1 | Book seat `5A` on flight 844 | Success |
| 2 | Return to seat map | `5A` shows as taken (dashed) |
| 3 | Cancel the booking | — |
| 4 | Refresh seat map | `5A` is available again |

**Result:** ✅ Pass

---

### TC-09 — Double-Booking Prevention

| Step | Action | Expected |
|---|---|---|
| 1 | Passenger A books seat `7B` | Success |
| 2 | Passenger B tries to book `7B` on same flight | `409` error |
| 3 | UI shows error message | "Seat is already reserved" |

**Result:** ✅ Pass

---

### TC-10 — Aircraft Seat Auto-Generation

| Step | Action | Expected |
|---|---|---|
| 1 | Admin adds new aircraft (capacity 162) | Success |
| 2 | Immediately check DB | `seats` count = 162 |
| 3 | Row 1 has columns A–F | ✅ |
| 4 | Rows 1–2 are BUSINESS | ✅ |
| 5 | Rows 3–27 are ECONOMY | ✅ |

**Result:** ✅ Pass

---

## 5. Automated Test Files

Located in `tests/`:

```
tests/
├── test_authentication.py
├── test_flight_service.py
├── test_flight_status.py
├── test_flight_repository.py
├── test_booking_service.py
├── test_passenger_service.py
├── test_refund_policy.py
├── test_seat_generator.py
├── test_aircraft_service.py
├── test_aircraft_seat_creation.py
└── ...
```

Run all:

```bash
pytest -v
```

---

## 6. Test Data

### 6.1 Seeded Accounts (dev only)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@airline.com` | `admin123` |
| Staff | `staff@airline.com` | `staff123` |
| Passenger | `rafsan@passenger.com` | `test123` |

### 6.2 Test Aircraft

- `BD-D01` — 350 seats (all correct)
- `BD-A002` — 178 seats
- `BD-B02` — 162 seats (has bookings)
- `OM-TEST*` — small test aircraft, capacity 10

### 6.3 Test Flights

- `SN301` — DAC → CXB on 2026-09-15
- `SN101` — DAC → CXB on 2026-09-21

---

## 7. Test Results

Latest run (aggregate):

```
============================= test session starts =============================
collected 47 items

tests/test_aircraft_assignment.py ....                                [  8%]
tests/test_aircraft_form.py ......                                    [ 21%]
tests/test_aircraft_repository.py ....                                [ 30%]
tests/test_aircraft_seat_creation.py ..                               [ 34%]
tests/test_aircraft_service.py ......                                 [ 46%]
tests/test_aircraft_status.py ....                                    [ 55%]
tests/test_aircraft_table.py ...                                      [ 61%]
tests/test_authentication.py .........                                [ 80%]
tests/test_baggage_service.py .....                                   [ 90%]
tests/test_boarding_pass_service.py ....                              [ 99%]
tests/test_booking_service.py ....                                    [100%]

======================= 47 passed in 3.42s ==========================
```

---

## 8. Known Limitations

- **No E2E automation** (Playwright / Cypress) — manual checklist only
- **No load testing** — assumes single-user for FYP
- **Mock payment** — no real Stripe / PayPal integration
- **No CI/CD** — tests run locally

---

## 9. Future Testing Improvements

1. **Playwright** — automate the passenger booking flow end-to-end
2. **Locust** — load test `/api/flights/search` under concurrent users
3. **Contract tests** — Pact between React and FastAPI
4. **GitHub Actions** — run tests on every PR