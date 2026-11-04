# 🏗️ System Architecture

> **Airline Management System — Final Year Project**
> A hybrid desktop + web architecture with a shared service layer and ML enhancements.

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Architectural Goals](#2-architectural-goals)
3. [Component Diagram](#3-component-diagram)
4. [Layered Architecture](#4-layered-architecture)
5. [Data Flow — Passenger Booking](#5-data-flow--passenger-booking)
6. [Authentication Flow](#6-authentication-flow)
7. [Refund Workflow](#7-refund-workflow)
8. [Machine Learning Subsystem](#8-machine-learning-subsystem)
9. [Flight Schedule Generator](#9-flight-schedule-generator)
10. [Design Decisions](#10-design-decisions)
11. [Deployment View (Future)](#11-deployment-view-future)

---

## 1. High-Level Overview

The system follows a **hybrid client-server architecture**: two independent client applications — a **desktop client** and a **web client** — share a common backend consisting of a Python service layer, an ORM, a PostgreSQL database, and an ML subsystem.

The **FastAPI** application is a thin HTTP adapter over the same service layer used by the desktop client. **No business logic is duplicated.**

---

## 2. Architectural Goals

| # | Goal | Description |
|---|------|-------------|
| 1 | **Single source of truth** | One database, one service layer, no logic duplication |
| 2 | **Role separation** | Admins & staff → desktop client; passengers → web client |
| 3 | **Loose coupling** | Clients interact through well-defined interfaces |
| 4 | **Backwards compatibility** | The desktop app continues to work unchanged |
| 5 | **Extensibility** | New clients and ML features can be added without modifying the services |
| 6 | **Automation** | Scheduling and pricing decisions are data-driven, not manual |
| 7 | **Defense in depth** | Role-gated API + JWT + bcrypt + per-endpoint authorization |

---

## 3. Component Diagram

**Diagram 1 — Component Diagram**

![Component Diagram](./diagrams/1.Component%20Diagram.png)

---

## 4. Layered Architecture

The backend follows a strict **layered architecture**.

**Diagram 2 — Layered Architecture**

![Layered Architecture](./diagrams/2.Layered%20Architecture.png)

### Layer Responsibilities

| Layer | Responsibility | Location |
|---|---|---|
| **Presentation** | Render UI, capture input, call services | `app/gui/*`, `api/routers/*` |
| **Application** | Business rules, validation, orchestration | `app/services/*`, `app/validators/*` |
| **ML Subsystem** | Predictions and recommendations | `app/ml/*` |
| **Data Access** | Query / insert / update DB, no business rules | `app/repositories/*` |
| **Domain** | Entity definitions | `app/models/*` |
| **Storage** | Persistent data | PostgreSQL |

---

## 5. Data Flow — Passenger Booking

A complete booking flow from the web app.

**Diagram 3 — Data Flow: Passenger Booking**

![Data Flow Passenger Booking](./diagrams/3.Data%20Flow%20Passenger%20Booking.png)

---

## 6. Authentication Flow

JWT-based stateless authentication.

**Diagram 4 — Authentication Flow**

![Authentication Flow](./diagrams/4.Authentication%20Flow.png)

---

## 7. Refund Workflow

Refunds require a two-party flow: **passenger requests**, **admin approves**.

**Diagram 5 — Refund Workflow**

![Refund Workflow](./diagrams/5.Refund%20Workflow.png)

---

## 8. Machine Learning Subsystem

Three ML models augment the core booking system. Each is trained offline, saved as a `.pkl` artifact, and served through a dedicated Python service inside `app/ml/`.

### 8.1 Model Overview

| Model | Type | Purpose | Metric |
|---|---|---|---|
| **No-Show Predictor** | XGBoost classifier | Predict expected no-shows per flight for overbooking advice | ROC-AUC 0.81 |
| **Route Recommender** | Item-item collaborative filtering | Personalize route suggestions on the landing page | Precision@3 ≥ 0.60 |
| **Fare Predictor** | XGBoost regressor | Dynamically price each scheduled flight | R² 0.98 |

### 8.2 ML Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Training Pipeline (offline)                  │
│                                                                │
│  generate_data.py → train.py → joblib.dump() → *.pkl artifact │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────────┐
│                    Inference (runtime)                         │
│                                                                │
│  PySide Desktop       ←──────┐                                 │
│  (direct Python)             │                                 │
│                              │                                 │
│                              ▼                                 │
│                    app/ml/*  Services                          │
│                              ▲                                 │
│                              │                                 │
│  React Web App  ──HTTP──►  FastAPI /api/ml/* endpoints         │
└────────────────────────────────────────────────────────────────┘
```

### 8.3 Why ML lives in `app/ml/` — not in `app/services/`

- **Separation of concerns** — model training, feature engineering, and prediction are distinct from core business rules
- **Optional dependency** — if a model is missing, the app still runs, just with a fallback path
- **Reproducibility** — training scripts and data generators are colocated with the model
- **Discoverability** — a reviewer knows exactly where to look for ML code

### 8.4 Integration Pattern

| Consumer | How it calls ML |
|---|---|
| **PySide Desktop** | Direct Python import — `NoShowService(session).forecast_flight(id)` |
| **React Web App** | HTTP — `GET /api/ml/recommendations` |
| **Schedule Generator** | Direct Python import — `FarePredictorService(session).predict(route, time)` |

The desktop app uses direct imports because it is Python and already calls services directly — no HTTP overhead needed. The web app uses HTTP because it is JavaScript.

Both consume the same underlying service classes.

---

## 9. Flight Schedule Generator

The schedule generator is a compound service that automates bulk flight creation.

### 9.1 Purpose

Generate 6+ months of flights in a single operation, with:
- Realistic frequency per route (domestic 3/day, international 1–2/day)
- Round-trip aircraft pairing (same aircraft returns on return leg)
- Aircraft range validation (ATR blocked from routes > 600 km)
- ML-driven per-flight fares
- Safe overwrite mode (only deletes scheduled flights with no bookings)

### 9.2 Component Composition

```
FlightScheduleGenerator
    │
    ├── FrequencyPredictor       → flights per day per route
    ├── TimeTemplateGenerator    → departure time slots with jitter
    ├── AircraftScheduler        → round-trip + range-valid assignment
    │       └── aircraft_range   → manufacturer range rules
    ├── FlightNumberGenerator    → unique sequential flight numbers
    └── FarePredictorService     → ML-based per-flight fare
```

### 9.3 Constraints Enforced

| Constraint | Rule | Enforcement |
|---|---|---|
| **Round-trip** | Same aircraft on return leg | `AircraftScheduler._can_operate()` |
| **Turnaround** | 45 min domestic / 90 min international between flights | Turnaround delta per route type |
| **Aircraft range** | ATR forbidden above 600 km | `aircraft_range.aircraft_can_serve_route()` |
| **Route uniqueness** | No duplicate `(flight_id, seat_id)` | DB unique constraint |
| **Overwrite safety** | Never delete flights with active bookings | `_delete_flights_in_range()` |

### 9.4 Performance

- **~1,140 flights/second** in benchmarks (593 flights in 0.52 s)
- Batch commits every 100 flights
- O(N) time on routes × days; negligible memory footprint

---

## 10. Design Decisions

### 10.1 Why a hybrid architecture?

Real airlines operate this way. Internal operations need rich desktop tooling (keyboard shortcuts, printing, multi-monitor support), while customers expect web and mobile access. Sharing a single backend delivers:

- **Consistency** — one business layer, one source of truth
- **Speed** — the passenger app ships faster without touching admin code
- **Safety** — bugs in the web app cannot corrupt admin workflows

### 10.2 Why FastAPI?

- **Pydantic v2** — automatic validation and OpenAPI documentation
- **Async-ready** — scales later without a rewrite
- **Python-native** — zero impedance with the existing services
- **Swagger out of the box** — free interactive API documentation

### 10.3 Why not rewrite the whole thing in React?

- The desktop admin/staff app works, is rich, and would take months to reimplement
- Admins do not need web access
- *Don't fix what isn't broken* — **strangler pattern**: migrate one piece at a time

### 10.4 Why JWT over sessions?

- **Stateless** — no server-side session store required
- Works cleanly across both the desktop and web clients
- Easy to expire (8-hour expiry currently)
- The standard approach for REST APIs

### 10.5 Why a role-gated API?

Even though the web app is *intended* for passengers, we enforce `require_passenger` at the API boundary. Admin tokens hitting `/api/bookings/*` receive **403**. This is defense-in-depth: even if a staff token is extracted, it cannot be misused against the passenger API.

### 10.6 Why atomic seat generation?

Creating an aircraft without seats leaves the database in an inconsistent state. By wrapping seat generation in the same transaction as aircraft creation, we guarantee: **every aircraft has exactly `seat_capacity` seats, always.**

### 10.7 Why a single pricing module?

Class-based pricing logic must be consistent across five surfaces:

1. Search results
2. Seat map display
3. Booking summary
4. Payment amount
5. PDF ticket

By centralizing this logic in `app/services/pricing.py`, changing the business multiplier updates **all five places at once.**

### 10.8 Why hybrid rule-based + ML scheduling?

Pure rules are predictable but rigid. Pure ML needs historical data we don't have. The hybrid approach:

- **Rule-based** for deterministic operations (frequency, times, flight numbers) — auditable and easy to reason about
- **ML-based** for the decision that benefits most from data (fares) — captures demand patterns rules can't

This lets the system ship immediately with sensible behavior, then improve fares as more data accumulates.

### 10.9 Why are ML models advisory, not blocking?

Every ML output is **advisory**. Nothing in the system refuses an operation because a model said so. The Overbooking Advisor *suggests* overbooking; it doesn't force it. The recommendations are shown but never required.

**Why?** ML models are probabilistic. Locking the user into a prediction makes the system fragile to drift, edge cases, and model errors. Advisory-only keeps the human in control.

### 10.10 Why does the desktop app call ML directly instead of HTTP?

The desktop app is written in Python and already imports `app/services/*` directly. Wrapping ML behind HTTP would:

- Add latency for zero benefit
- Require the FastAPI server to be running for admin features
- Duplicate the JWT flow inside a trusted local process

**Direct import is the right call for local desktop clients.** HTTP is only used when crossing the language boundary (React → FastAPI).

---

## 11. Deployment View (Future)

**Diagram 6 — Deployment View (Future)**

![Deployment View (Future)](./diagrams/6.Deployment%20View%20(Future).png)

> For the current academic version, everything runs locally.