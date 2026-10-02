# ✈️ Airline Management System

> **Final Year Project · Zhengzhou University · 2023–2027**
> A modern airline booking and management system built on a **hybrid desktop + web architecture**.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Architecture](#3-architecture)
4. [Tech Stack](#4-tech-stack)
5. [Quick Start](#5-quick-start)
6. [Documentation Index](#6-documentation-index)
7. [Project Structure](#7-project-structure)
8. [Testing](#8-testing)
9. [Roles & Access](#9-roles--access)
10. [Screenshots](#10-screenshots)
11. [License](#11-license)
12. [Acknowledgments](#12-acknowledgments)

---

## 1. Overview

A modern airline booking and management system built as a Final Year Project.

The system consists of **two complementary user interfaces** sharing a common PostgreSQL database and business-logic layer:

- 🖥️ **Desktop client** (Python + PySide6) — used by **administrators and staff** for operations
- 🌐 **Web application** (React + FastAPI) — used by **passengers** for self-service booking

---

## 2. Features

### 2.1 Passenger Web App — `localhost:5173`

- 🎬 Animated landing page with hero section
- 🔍 Public flight search (no login required to browse)
- 💺 Interactive seat map with class-based pricing
- 💳 Booking + mock payment gateway
- 🎫 PDF e-ticket download
- 💸 Refund requests with policy tiers
- 👤 Profile management (view/edit + password change)
- 📋 My Bookings dashboard with full booking timeline

### 2.2 Admin / Staff Desktop App

- 📊 Admin dashboard with live metrics
- ✈️ Aircraft, flight, route, and airport management
- 👥 Staff management and assignment
- ✅ Passenger check-in and boarding pass issuance
- 💰 Refund approval / rejection
- 📈 Reports and analytics

### 2.3 Backend (shared)

- 🔐 JWT authentication with role-based access
- 📐 Role-gated API (passenger-only web endpoints)
- 🎯 Class-based pricing engine (Economy 1× / Business 2.5×)
- 🪑 Automatic seat generation for any aircraft capacity
- 📄 PDF generation (tickets, boarding passes, baggage tags)
- 🔄 Full booking lifecycle state machine

---

## 3. Architecture

```
┌──────────────────────┐              ┌──────────────────────┐
│   PySide Desktop     │              │   React Web App      │
│   (Admin + Staff)    │              │   (Passengers)       │
└──────────┬───────────┘              └──────────┬───────────┘
           │ SQLAlchemy                          │ REST / JWT
           │                                     │
           ▼                                     ▼
    ┌────────────────────────────────────────────────────┐
    │         Shared Services & Repositories             │
    │  (single source of truth for business logic)       │
    └────────────────┬───────────────────────────────────┘
                     │
                     ▼
              ┌──────────────┐
              │  PostgreSQL  │
              └──────────────┘

                     ▲
                     │ REST / JWT
                     │
              ┌──────┴───────┐
              │   FastAPI    │
              └──────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for full diagrams.

---

## 4. Tech Stack

| Layer | Technology |
|---|---|
| **Desktop client** | Python 3.12 + PySide6 (Qt6) |
| **Web client** | React 18 + Vite + Framer Motion + Axios |
| **API** | FastAPI + Pydantic v2 + Uvicorn |
| **ORM** | SQLAlchemy 2.x |
| **Database** | PostgreSQL 14+ |
| **Auth** | JWT (HS256) + bcrypt |
| **PDFs** | ReportLab |
| **Icons** | react-icons |

---

## 5. Quick Start

**Prerequisites:** Python 3.12+, Node.js 18+, PostgreSQL 14+ running locally.

```bash
# 1. Clone and set up the backend
git clone <your-repo-url>
cd Airline-Management-System
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt

# 2. Configure the database
# Edit .env and set DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# 3. Initialize the database (creates tables + seed data)
python -c "from app.models.init_database import init_database; init_database()"

# 4. Start the FastAPI backend
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

# 5. Set up and start the React frontend (in a new terminal)
cd frontend
npm install
npm run dev

# 6. Launch the desktop app (in a third terminal)
python -m app.main
```

**URLs**

| Service | URL |
|---|---|
| Web app | <http://localhost:5173> |
| API docs (Swagger) | <http://127.0.0.1:8000/docs> |
| ReDoc | <http://127.0.0.1:8000/redoc> |

Full setup guide: [docs/SETUP.md](docs/SETUP.md)

---

## 6. Documentation Index

| Document | Description |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, component diagrams, data flow |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | Complete REST API documentation |
| [DATABASE.md](docs/DATABASE.md) | Schema, ERD, relationships |
| [USER_GUIDE.md](docs/USER_GUIDE.md) | Step-by-step guides for all user roles |
| [TESTING.md](docs/TESTING.md) | Test strategy, test cases, results |
| [SETUP.md](docs/SETUP.md) | Installation, configuration, deployment |
| [SUMMARY.md](docs/SUMMARY.md) | One-page executive summary |

---

## 7. Project Structure

```
Airline-Management-System/
├── app/                    # Python backend + desktop GUI
│   ├── config/             # Database, settings
│   ├── gui/                # PySide6 desktop client
│   │   ├── admin/          # Admin dashboard
│   │   ├── staff/          # Staff dashboard
│   │   ├── login/          # Shared login window
│   │   ├── common/         # Styles, shared widgets
│   │   └── components/     # Reusable PySide widgets
│   ├── models/             # SQLAlchemy models
│   ├── repositories/       # Data access layer
│   ├── services/           # Business logic
│   ├── utils/              # PDF generator, security helpers
│   └── validators/         # Domain validators
├── api/                    # FastAPI passenger API
│   ├── main.py             # App entry point
│   ├── deps.py             # Dependencies (auth, db)
│   ├── security_jwt.py     # JWT encode/decode
│   ├── routers/            # HTTP endpoints
│   └── schemas/            # Pydantic models
├── frontend/               # React passenger web app
│   ├── src/
│   │   ├── api/            # API client
│   │   ├── components/     # Reusable components
│   │   ├── context/        # Auth context
│   │   ├── pages/          # Route pages
│   │   └── App.jsx
│   └── package.json
├── docs/                   # Documentation (this folder)
├── tests/                  # Automated tests
├── requirements.txt
└── README.md
```

---

## 8. Testing

```bash
# Backend
pytest

# Frontend (add vitest for unit tests)
cd frontend
npm test
```

See [docs/TESTING.md](docs/TESTING.md) for the full test plan.

---

## 9. Roles & Access

| Role | Surface | Capabilities |
|---|---|---|
| **Admin** | Desktop | Full CRUD on aircraft, flights, routes, staff, airports; reports; refund approvals |
| **Staff** | Desktop | Passenger check-in, boarding pass issuance, baggage handling |
| **Passenger** | Web | Search, book, pay, download tickets, request refunds, manage profile |

> Passenger desktop login redirects to the web app.

---

## 10. Screenshots

A complete visual walkthrough of the system, organized by user journey.

---

### 10.1 Passenger Web Application

####  Landing & Public Pages

| # | Screenshot | Description |
|---|---|---|
| 1 | ![Landing Page](./snaps/landing.png) | **Landing page** — Animated hero section with the flight search widget |
| 10 | ![Popular Destinations](./snaps/10populardestinationsection.png) | **Popular destinations** — Featured routes section on the landing page |

####  Flight Search & Discovery

| # | Screenshot | Description |
|---|---|---|
| 2 | ![Flight Results](./snaps/2Flightresult.png) | **Search results** — Flight cards with economy and business class fares |
| 3 | ![Flight Details](./snaps/3flightdetails.png) | **Flight details** — Full flight information with route visualization |

#### 💺 Booking Flow

| # | Screenshot | Description |
|---|---|---|
| 4 | ![Seat Selection](./snaps/4seatselection.png) | **Seat selection** — Interactive seat map with class-based pricing |
| 5 | ![Mock Payment](./snaps/5mockpayment.png) | **Mock payment** — Secure card form with live order summary |
| 6 | ![Confirmation](./snaps/6confirmation.png) | **Confirmation** — Animated success screen with booking reference |

####  Booking Management

| # | Screenshot | Description |
|---|---|---|
| 7 | ![Booking Details](./snaps/7bookingdetails.png) | **Booking details** — E-ticket view with full timeline and actions |
| 8 | ![E-Ticket](./snaps/8eticket.png) | **E-ticket PDF** — Generated ticket with passenger and flight details |

####  Account Management

| # | Screenshot | Description |
|---|---|---|
| 9 | ![Profile](./snaps/9profile.png) | **Profile page** — Personal information and password management |
| 1.1 | ![Register](./snaps/1.1Register.png) | **Register** — Account creation form with validation |
| 1.1 | ![Login](./snaps/1.1Login.png) | **Login** — Sign-in form with error handling |

---

### 10.2 Admin Desktop Application

####  Dashboard

| # | Screenshot | Description |
|---|---|---|
| stafflogin | ![Staff Login](./snaps/stafflogin.png) | **Login** — Shared login window for admin and staff |
| 11 | ![Admin Dashboard](./snaps/11admindashboard.png) | **Admin dashboard** — Live metrics for flights, aircraft, and bookings |

####  Management Screens

| # | Screenshot | Description |
|---|---|---|
| 12 | ![Add Airport](./snaps/12admindashairportsadd.png) | **Add airport** — Airport registration with IATA/ICAO codes |
| 13 | ![Add Aircraft](./snaps/13admindashaircraftsadd.png) | **Add aircraft** — Aircraft registration with auto seat generation |
| 14 | ![Add Flight](./snaps/14admindashflightadd.png) | **Add flight** — Flight scheduling with route and aircraft selection |

####  Operations & Reports

| # | Screenshot | Description |
|---|---|---|
| 15 | ![Booking View](./snaps/15adminbookingview.png) | **Booking management** — View, filter, and manage all bookings |
| 16 | ![Report View](./snaps/16adminreportview.png) | **Reports** — Revenue, load factor, and analytics dashboards |

---

### 10.3 Staff Desktop Application

####  Check-In Operations

| # | Screenshot | Description |
|---|---|---|
| 17 | ![Staff Dashboard](./snaps/17checkinstaffdashboard.png) | **Staff dashboard** — Passenger check-in and boarding pass issuance |
| 18 | ![Baggage Tag](./snaps/18buggagetag.png) | **Baggage tag** — Auto-generated PDF baggage tag with tear-off stub |
| 19 | ![Boarding Pass](./snaps/19boardingpass.png) | **Boarding pass** — PDF boarding pass with QR code and stub |

---

## 11. License

Academic use only. **Not licensed for commercial distribution.**

---

## 12. Acknowledgments

Built as part of a personal Project.

- **Institution:** Zhengzhou University
- **Academic Year:** 2023–2027

> This project is intended for educational and academic purposes only. Do not use for commercial purposes.