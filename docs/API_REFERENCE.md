#  API Reference

> **Airline Management System**
> REST API for the passenger web application. Built with FastAPI + Pydantic v2.

---

## Table of Contents

1. [Base URL & Docs](#1-base-url--docs)
2. [Authentication](#2-authentication)
3. [Endpoints](#3-endpoints)
   - [Auth](#31-auth)
   - [Flights (Public)](#32-flights-public)
   - [Seats (Public)](#33-seats-public)
   - [Bookings (Protected)](#34-bookings-protected)
   - [Refunds (Protected)](#35-refunds-protected)
   - [Payments (Protected)](#36-payments-protected)
   - [Ticket PDF (Protected)](#37-ticket-pdf-protected)
   - [Passenger Profile (Protected)](#38-passenger-profile-protected)
   - [Health](#39-health)
4. [Status Codes Summary](#4-status-codes-summary)

---

## 1. Base URL & Docs

| | |
|---|---|
| **Base URL** | `http://127.0.0.1:8000` |
| **Swagger UI** | [`/docs`](http://127.0.0.1:8000/docs) |
| **ReDoc** | [`/redoc`](http://127.0.0.1:8000/redoc) |

---

## 2. Authentication

All passenger endpoints require a **JWT** obtained from `/api/auth/login` or `/api/auth/register`.

Send it in the request header:

```
Authorization: Bearer <token>
```

Tokens expire after **8 hours**.

---

## 3. Endpoints

### 3.1 Auth

#### `POST /api/auth/login`

Login and receive a JWT.

**Request body**

```json
{
  "email": "rafsan@passenger.com",
  "password": "test123"
}
```

**Response — 200**

```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "rafsan@passenger.com",
    "role": "PASSENGER"
  }
}
```

**Errors**

| Code | Meaning |
|---|---|
| `401` | Invalid credentials |
| `403` | Non-passenger role (admins/staff must use the desktop app) |

---

#### `POST /api/auth/register`

Create a passenger account. Returns a JWT immediately.

**Request body**

```json
{
  "email": "newuser@test.com",
  "password": "secret123",
  "first_name": "New",
  "last_name": "User",
  "phone": "+8801700000000",
  "date_of_birth": "1995-05-20",
  "passport_number": "XX9999999",
  "address": "Dhaka, Bangladesh"
}
```

**Response — 201:** Same shape as login.

**Errors**

| Code | Meaning |
|---|---|
| `409` | Email or passport already exists |
| `422` | Invalid input |

---

#### `GET /api/auth/me`

Get the current user's info.

**Response — 200**

```json
{
  "id": 1,
  "email": "rafsan@passenger.com",
  "role": "PASSENGER"
}
```

---

### 3.2 Flights (Public)

#### `GET /api/flights/search`

Search for flights. **No authentication required.**

**Query parameters**

| Name | Type | Required | Description |
|---|---|---|---|
| `origin` | string (3) | yes | Origin IATA code (e.g., `DAC`) |
| `destination` | string (3) | yes | Destination IATA code |
| `date` | date | yes | Departure date (`YYYY-MM-DD`) |

**Example**

```
GET /api/flights/search?origin=DAC&destination=CXB&date=2026-09-15
```

**Response — 200**

```json
{
  "count": 1,
  "results": [
    {
      "id": 844,
      "flight_number": "SN301",
      "departure_time": "2026-09-15T19:00:42.535000",
      "arrival_time": "2026-09-15T19:45:42.535000",
      "base_fare": "35.00",
      "economy_fare": "35.00",
      "business_fare": "87.50",
      "status": "SCHEDULED",
      "boarding_gate": "TBD",
      "route": {
        "id": 3,
        "distance_km": 312,
        "estimated_duration_minutes": 65,
        "origin_airport": { "...": "..." },
        "destination_airport": { "...": "..." }
      },
      "aircraft": {
        "id": 2,
        "registration_number": "BD-B02",
        "manufacturer": "Boeing",
        "model": "737-800",
        "seat_capacity": 162,
        "status": "ACTIVE"
      }
    }
  ]
}
```

**Errors**

| Code | Meaning |
|---|---|
| `400` | Same origin and destination |
| `404` | Airport not found |

---

#### `GET /api/flights/{flight_id}`

Get one flight's full details. **Public.**

**Response — 200:** A single `FlightResponse` object (same shape as one item from search).

---

### 3.3 Seats (Public)

#### `GET /api/flights/{flight_id}/seats`

Get the seat map for a flight. **Public.**

**Response — 200**

```json
[
  {
    "id": 1001,
    "seat_number": "1A",
    "seat_class": "BUSINESS",
    "row_number": 1,
    "position": "WINDOW",
    "is_available": true,
    "price": "87.50"
  },
  {
    "id": 1002,
    "seat_number": "1B",
    "seat_class": "BUSINESS",
    "row_number": 1,
    "position": "MIDDLE",
    "is_available": false,
    "price": "87.50"
  }
]
```

> `is_available` is `false` when the seat has an active booking (non-cancelled, non-refunded).

---

### 3.4 Bookings (Protected)

All endpoints require a passenger JWT.

#### `POST /api/bookings`

Create a booking (status: `UNPAID`).

**Request body**

```json
{ "flight_id": 844, "seat_id": 1001 }
```

**Response — 201**

```json
{
  "id": 147,
  "booking_reference": "SN7X4K2A",
  "flight_id": 844,
  "seat_id": 1001,
  "passenger_id": 1,
  "fare_amount": "87.50",
  "refund_amount": null,
  "status": "UNPAID",
  "booked_at": "2026-09-15T18:32:00",
  "cancelled_at": null
}
```

> **Note:** Fare is computed automatically via the pricing module (business class = 2.5× economy).

**Errors**

| Code | Meaning |
|---|---|
| `400` | Seat doesn't belong to flight's aircraft |
| `403` | Not your account |
| `409` | Seat already booked |

---

#### `GET /api/bookings/my`

List the logged-in passenger's bookings.

**Response — 200:** Array of `BookingResponse`.

---

#### `GET /api/bookings/{booking_id}`

Get one booking. `403` if it's not yours.

**Response — 200:** `BookingResponse`.

---

#### `DELETE /api/bookings/{booking_id}`

Cancel a booking.

**Response — 200:** Updated `BookingResponse` with `status: CANCELLED`.

**Errors**

| Code | Meaning |
|---|---|
| `409` | Booking can't be cancelled in its current state |

---

### 3.5 Refunds (Protected)

#### `GET /api/bookings/{booking_id}/refund-preview`

Preview how much you'd get back. Does **not** change anything.

**Response — 200**

```json
{
  "booking_id": 147,
  "booking_reference": "SN7X4K2A",
  "eligible": true,
  "reason": null,
  "refund_amount": "28.00",
  "refund_percentage": 80,
  "paid_amount": "35.00",
  "departure_time": "2026-09-15T19:00:42",
  "hours_until_departure": 1.4
}
```

**Refund tiers**

| Days before departure | Refund % |
|---|---|
| 7+ | 100% |
| 5+ | 80% |
| 3+ | 70% |
| 2+ | 60% |
| 1+ | 40% |
| Same day | 25% |

---

#### `POST /api/bookings/{booking_id}/refund`

Submit a refund request. Flips status `CONFIRMED → REFUND_REQUESTED`.

**Response — 200**

```json
{
  "id": 147,
  "booking_reference": "SN7X4K2A",
  "status": "REFUND_REQUESTED",
  "refund_amount": null,
  "message": "Refund requested. Pending admin review."
}
```

**Errors**

| Code | Meaning |
|---|---|
| `409` | Booking not in `CONFIRMED` state |

---

### 3.6 Payments (Protected)

#### `POST /api/payments`

Process a mock payment for a booking. Marks it `CONFIRMED` on success.

**Request body**

```json
{
  "booking_id": 147,
  "amount": 87.50,
  "card_number": "4242424242424242",
  "expiry": "12/28",
  "cvv": "123",
  "cardholder_name": "Rafsan Ahmed"
}
```

**Response — 200**

```json
{
  "success": true,
  "message": "Payment approved (mock).",
  "booking_id": 147,
  "transaction_id": "TXN-A1B2C3D4E5F6",
  "amount": 87.50
}
```

**Errors**

| Code | Meaning |
|---|---|
| `403` | Not your booking |
| `409` | Already paid / cancelled |
| `422` | Card format rejected |

---

### 3.7 Ticket PDF (Protected)

#### `GET /api/bookings/{booking_id}/ticket`

Download the e-ticket as a PDF.

**Response:** `application/pdf` stream.

**Errors**

| Code | Meaning |
|---|---|
| `409` | Booking is `UNPAID` or `CANCELLED` |

---

### 3.8 Passenger Profile (Protected)

#### `GET /api/passengers/me`

Get the current passenger's profile.

**Response — 200**

```json
{
  "id": 1,
  "user_id": 1,
  "email": "rafsan@passenger.com",
  "first_name": "Rafsan",
  "last_name": "Ahmed",
  "phone": "+8801700000000",
  "date_of_birth": "1995-05-20",
  "passport_number": "XX9999999",
  "address": "Dhaka, Bangladesh",
  "created_at": "2026-01-15T10:00:00",
  "updated_at": "2026-09-15T18:00:00"
}
```

---

#### `PUT /api/passengers/me`

Update profile.

**Request body**

```json
{
  "first_name": "Rafsan",
  "last_name": "Ahmed",
  "phone": "+8801700000000",
  "date_of_birth": "1995-05-20",
  "passport_number": "XX9999999",
  "address": "Dhaka, Bangladesh"
}
```

**Response — 200:** Updated profile.

---

#### `POST /api/passengers/me/password`

Change password.

**Request body**

```json
{
  "old_password": "test123",
  "new_password": "newsecret123"
}
```

**Response — 200**

```json
{ "message": "Password updated successfully." }
```

**Errors**

| Code | Meaning |
|---|---|
| `400` | Wrong current password |
| `422` | New password too short |

---

### 3.9 Health

#### `GET /health`

Liveness check.

**Response — 200**

```json
{ "status": "ok" }
```

---

## 4. Status Codes Summary

| Code | Meaning |
|---|---|
| `200` | OK |
| `201` | Created |
| `400` | Bad request (validation or logic error) |
| `401` | Not authenticated |
| `403` | Authenticated but not authorized |
| `404` | Resource not found |
| `409` | Conflict (double-booking, wrong state) |
| `422` | Unprocessable entity (Pydantic validation) |
| `500` | Internal server error |