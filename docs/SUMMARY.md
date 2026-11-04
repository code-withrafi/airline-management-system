# 📄 One-Page Project Summary

> **Airline Management System — A Hybrid Desktop and Web Architecture**

| | |
|---|---|
| **Title** | Airline Management System — A Hybrid Desktop and Web Architecture |
| **Author** | Iftekhar Ibne Masud Rafi |
| **Institution** | Zhengzhou University (2023–2027) |
| **Academic Year** | 2023–2027 |
| **Project Type** | Final Year Project |

---

## Problem

Traditional airline management systems typically fall into one of two categories:

- **Desktop-only** — rich admin tooling, but a poor passenger experience
- **Web-only** — modern passenger UX, but a loss of rich internal tooling

Neither approach serves both audiences well. A third failure mode is even more common: **rewriting everything from scratch**, which is expensive, risky, and slow.

---

## Solution

A **hybrid architecture** in which:

- **Administrators and staff** use a rich **Python / PySide6** desktop client
- **Passengers** use a modern **React** web application
- Both surfaces share a **single PostgreSQL database** and a **common Python business-logic layer**
- A **FastAPI** backend exposes REST endpoints for the web client
- Three **machine learning models** augment the system with predictive capability

The desktop app was **augmented — not replaced —** following the **strangler fig pattern**. The passenger surface was migrated to the web first, while admin and staff operations kept working unchanged.

---

## Key Features

### Passenger Web App
- Animated React landing page with hero and live recommendations
- Public flight search with no login required
- Interactive seat map with class-based pricing (Economy 1× / Business 2.5×)
- JWT-authenticated booking flow with mock payment gateway
- PDF e-ticket download
- Full refund lifecycle (passenger requests → admin approves)
- Personal profile and password management

### Admin & Staff Desktop App
- Admin dashboard with live operational metrics
- Aircraft, flight, route, airport, and staff management
- **Automated flight schedule generator** — bulk-generate 6+ months of flights in seconds
- **Aircraft range-aware scheduling** — ATR turboprops blocked from routes > 600 km
- Passenger check-in and PDF boarding pass issuance
- Baggage tag generation with tear-off stubs
- Refund approvals and operational reports

### Machine Learning Subsystem
- **No-Show Prediction** — XGBoost classifier powering an Overbooking Advisor (ROC-AUC 0.81)
- **Route Recommendations** — item-item collaborative filtering for personalized landing-page suggestions
- **Dynamic Fare Prediction** — XGBoost regressor pricing each flight by demand patterns (R² 0.98)

---

## Technology Stack

**Backend & Desktop:** Python 3.12 · PySide6 · FastAPI · SQLAlchemy 2.x · Pydantic v2 · PostgreSQL 14+

**Web Frontend:** React 18 · Vite · Framer Motion · Axios · react-icons

**Machine Learning:** XGBoost · scikit-learn · pandas · numpy · joblib

**Auth & Security:** JWT (HS256) · bcrypt

**Document Generation:** ReportLab

---

## Results

- **47 automated backend tests** passing
- All **26 aircraft** in the system have correct seat counts
- **3 trained ML models** with documented metrics (ROC-AUC 0.81, R² 0.98)
- **Automated schedule generator** produces ~600 flights per month at ~1,140 flights/second
- Full end-to-end booking flow verified from landing page to PDF ticket
- **Zero regressions** in the legacy desktop client throughout the migration
- **Zero ATR turboprops** assigned to routes exceeding 600 km

---

## Conclusion

The system demonstrates that **legacy desktop applications can be augmented — not replaced — by modern web frontends**, provided they share a well-designed backend. The **strangler fig pattern** applied here (migrate the passenger surface, keep the admin surface) enabled incremental delivery with zero downtime and no data loss.

Beyond the hybrid architecture, the project demonstrates that a traditional booking system can be meaningfully enhanced with **machine learning** — predictive pricing, no-show forecasting, and route recommendations — without redesigning the underlying architecture or disrupting existing workflows.