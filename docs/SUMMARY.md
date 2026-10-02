#  One-Page Project Summary

> **Airline Management System**

| | |
|---|---|
| **Title** | Airline Management System — A Hybrid Desktop and Web Architecture |
| **Author** | [Iftekhar Ibne Masud Rafi] |
| **Institution** | [Zhengzhou University (2023-2027)] |


---

## Problem

Traditional airline management systems typically fall into one of two categories:

- **Desktop-only** — rich admin tooling, but a poor passenger experience
- **Web-only** — modern passenger UX, but a loss of rich internal tooling

Neither approach serves both audiences well.

---

## Solution

A **hybrid architecture** in which:

- **Administrators and staff** use a rich **Python / PySide6** desktop client
- **Passengers** use a modern **React** web application
- Both surfaces share a **single PostgreSQL database** and a **common Python business-logic layer**
- A **FastAPI** backend exposes REST endpoints for the web client

---

## Key Features

- Animated React landing page with public flight search
- Interactive seat map with class-based pricing (Economy 1× / Business 2.5×)
- JWT-authenticated booking flow with mock payment gateway
- PDF ticket and boarding pass generation
- Full refund lifecycle (passenger requests → admin approves)
- Automated seat generation for any aircraft capacity
- Admin dashboard with aircraft, flight, route, and staff management

---

## Technology Stack

**Python · PySide6 · FastAPI · SQLAlchemy · PostgreSQL · React · Vite · Framer Motion · Axios · JWT · bcrypt · ReportLab**

---

## Results

- 47 automated backend tests passing
- All 26 aircraft in the system have correct seat counts
- Full end-to-end booking flow verified from landing page to PDF ticket
- Zero regressions in the legacy desktop client

---

## Conclusion

The system demonstrates that legacy desktop applications can be **augmented — not replaced —** by modern web frontends, provided they share a well-designed backend. The **strangler fig pattern** applied here (migrate the passenger surface, keep the admin surface) enabled incremental delivery with zero downtime and no data loss.