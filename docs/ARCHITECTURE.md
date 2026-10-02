#  System Architecture

> **Airline Management System**
> A hybrid desktop + web architecture with a shared service layer.

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Architectural Goals](#2-architectural-goals)
3. [Component Diagram](#3-component-diagram)
4. [Layered Architecture](#4-layered-architecture)
5. [Data Flow — Passenger Booking](#5-data-flow--passenger-booking)
6. [Authentication Flow](#6-authentication-flow)
7. [Refund Workflow](#7-refund-workflow)
8. [Design Decisions](#8-design-decisions)
9. [Deployment View (Future)](#9-deployment-view-future)

---

## 1. High-Level Overview

The system follows a **hybrid client-server architecture**: two independent client applications — a **desktop client** and a **web client** — share a common backend consisting of a Python service layer, an ORM, and a PostgreSQL database.

The **FastAPI** application is a thin HTTP adapter over the same service layer used by the desktop client. **No business logic is duplicated.**

---

## 2. Architectural Goals

| # | Goal | Description |
|---|------|-------------|
| 1 | **Single source of truth** | One database, one service layer, no logic duplication |
| 2 | **Role separation** | Admins & staff → desktop client; passengers → web client |
| 3 | **Loose coupling** | Clients interact through well-defined interfaces |
| 4 | **Backwards compatibility** | The desktop app continues to work unchanged |
| 5 | **Extensibility** | New clients can be added without modifying the services |

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

## 8. Design Decisions

### 8.1 Why a hybrid architecture?

Real airlines operate this way. Internal operations need rich desktop tooling (keyboard shortcuts, printing, multi-monitor support), while customers expect web and mobile access. Sharing a single backend delivers:

- **Consistency** — one business layer, one source of truth
- **Speed** — the passenger app ships faster without touching admin code
- **Safety** — bugs in the web app cannot corrupt admin workflows

### 8.2 Why FastAPI?

- **Pydantic v2** — automatic validation and OpenAPI documentation
- **Async-ready** — scales later without a rewrite
- **Python-native** — zero impedance with the existing services
- **Swagger out of the box** — free interactive API documentation

### 8.3 Why not rewrite the whole thing in React?

- The desktop admin/staff app works, is rich, and would take months to reimplement
- Admins do not need web access
- *Don't fix what isn't broken* — **strangler pattern**: migrate one piece at a time

### 8.4 Why JWT over sessions?

- **Stateless** — no server-side session store required
- Works cleanly across both the desktop and web clients
- Easy to expire (8-hour expiry currently)
- The standard approach for REST APIs

### 8.5 Why a role-gated API?

Even though the web app is *intended* for passengers, we enforce `require_passenger` at the API boundary. Admin tokens hitting `/api/bookings/*` receive **403**. This is defense-in-depth: even if a staff token is extracted, it cannot be misused against the passenger API.

### 8.6 Why atomic seat generation?

Creating an aircraft without seats leaves the database in an inconsistent state. By wrapping seat generation in the same transaction as aircraft creation, we guarantee: **every aircraft has exactly `seat_capacity` seats, always.**

### 8.7 Why a single pricing module?

Class-based pricing logic must be consistent across five surfaces:

1. Search results
2. Seat map display
3. Booking summary
4. Payment amount
5. PDF ticket

By centralizing this logic in `app/services/pricing.py`, changing the business multiplier updates **all five places at once**.

---

## 9. Deployment View (Future)

**Diagram 6 — Deployment View (Future)**

![Deployment View (Future)](./diagrams/6.Deployment%20View%20(Future).png)

> For the current version, everything runs locally.