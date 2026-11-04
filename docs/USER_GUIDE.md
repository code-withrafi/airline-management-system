# 👥 User Guide

> **Airline Management System — Final Year Project**
> Complete guide for Passengers, Administrators, and Staff.

---

## Table of Contents

1. [Passenger Guide](#1-passenger-guide)
2. [Administrator Guide](#2-administrator-guide)
3. [Staff Guide](#3-staff-guide)
4. [Common Passenger Scenarios](#4-common-passenger-scenarios)
5. [Keyboard Shortcuts](#5-keyboard-shortcuts)
6. [Browser Support](#6-browser-support)
7. [Troubleshooting](#7-troubleshooting)
8. [Support](#8-support)

---

## 1. Passenger Guide

**Access:** Web app at <http://localhost:5173>

### 1.1 Creating an Account

1. Open the web app.
2. Click **Get started** in the top-right corner.
3. Fill in:
   - First name, last name
   - Email, password (min 6 chars)
   - Phone, date of birth
   - Passport number
   - Address (optional)
4. Click **Create account**.
5. You're logged in automatically ✅

### 1.2 Searching for Flights (No Login Needed)

1. From the landing page, use the search widget:
   - **From:** 3-letter airport code (e.g., `DAC`)
   - **To:** 3-letter airport code (e.g., `CXB`)
   - **Date:** departure date
2. Click **Search**.
3. Browse results — each card shows:
   - Flight number, aircraft
   - Departure / arrival times
   - **Economy from $X · Business from $Y**
4. Click **Select** on a flight to see full details.

### 1.3 Exploring Recommendations (Automatic)

Below the popular-destinations section, the landing page shows a **live recommendation carousel**:

- **Anonymous visitors** see the 3 most popular routes across the network.
- **Logged-in passengers** see **personalized** recommendations based on their booking history.
  - The section header changes to *"Picked for your next trip"*
  - A subtitle shows which of your past routes the recommendations are based on.
- Click any recommended route to jump straight to the search results for that route.

### 1.4 Booking a Flight

1. On the flight detail page, click **Book this flight**.
2. *(If not logged in, you'll be redirected to login; after signing in, you'll return to booking automatically.)*
3. **Choose your seat** from the interactive seat map:
   - **Amber seats** = Business class (higher price)
   - **White seats** = Economy class
   - **Dashed gray** = already taken
   - Click a seat to select it.
4. Review the summary on the right:
   - Base fare
   - Business surcharge (if applicable)
   - Total
5. Click **Continue to payment**.

> **Dynamic pricing note:** Fares are computed per flight by the ML fare model. Same route, different days/hours have different prices. Peak hours, weekends, and holiday seasons cost more.

### 1.5 Completing Payment

The demo uses a **mock payment gateway**. Any card number passing the Luhn check will be approved.

**Test card:**

- Number: `4242 4242 4242 4242`
- Name: your name
- Expiry: `12/28` (any future date)
- CVC: `123`

Click **Pay $X.XX**. You'll be redirected to a **green confirmation screen**.

### 1.6 Downloading Your Ticket

**From the confirmation screen:** Click **Download ticket**.

**From My Bookings:** Click the **Ticket** button on any confirmed booking.

You'll get a PDF e-ticket with:

- Passenger details
- Flight info
- Seat assignment
- Fare

### 1.7 Managing Bookings

Go to **My Bookings** from the navbar. Each booking shows:

- Reference number
- Status badge
- Total paid
- Actions: **Details / Ticket / Refund / Cancel**

Click **Details** for the full booking page with timeline.

### 1.8 Requesting a Refund

1. On a **CONFIRMED** booking, click **Refund**.
2. A modal opens showing:
   - **Refund policy** (25%–100% depending on timing)
   - **Your refund amount**
3. Click **Request $X.XX**.
4. Status changes to **REFUND_REQUESTED** (pending admin review).
5. Once an admin approves, status becomes **REFUNDED**.

### 1.9 Profile Management

Click your **avatar** (top-right) → **Profile**:

- **Personal information:** edit name, phone, DOB, passport, address
- **Account & security:** change your password

Changes are saved immediately.

### 1.10 Signing Out

Click **Sign out** in the top-right. Your JWT is cleared. You can sign back in anytime.

---

## 2. Administrator Guide

**Access:** PySide desktop app (`python -m app.main` → log in as admin)

### 2.1 Dashboard

Shows:

- Total airports, aircraft, routes, and flights
- Scheduled vs. cancelled flights
- Bookings and registered passengers
- Recent / upcoming flights list

### 2.2 Aircraft Management

- **Add aircraft:** Registration, manufacturer, model, capacity → seats **auto-generate** to match
- **Edit aircraft:** Update details (capacity changes require care with existing bookings)
- **View seats:** Inspect the layout generated for each aircraft
- **Status:** Set aircraft to ACTIVE / MAINTENANCE / INACTIVE

> **Aircraft range rule:** ATR turboprops cannot be assigned to routes longer than 600 km. Only Boeing and Airbus (and other long-haul manufacturers) can operate on long routes. This rule is enforced automatically by the schedule generator.

### 2.3 Route Management

- **Add route:** Origin, destination, distance, duration
- **Toggle active / inactive**

### 2.4 Flight Management

- **Add flight:** Number, route, aircraft, times, base fare
- **Update status:** `SCHEDULED` → `BOARDING` → `DEPARTED` → `ARRIVED`
- **Cancel flight:** All bookings auto-refund eligible
- **Assign aircraft:** Swap aircraft on an existing flight

#### Filtering Flights (Large Fleets)

Because the schedule generator can produce **hundreds or thousands of flights**, the flight management page includes powerful filters:

| Filter | Purpose |
|---|---|
| **Search** | Match by flight number (`SN1042`), route (`DAC-CXB`, `DAC->CXB`, `DAC`), or boarding gate |
| **Status** | Show only flights matching one status (Scheduled, Boarding, Departed, etc.) |
| **From date** | Only flights departing on or after this date |
| **To date** | Only flights departing on or before this date |
| **Reset** | Clear all filters and restore the default date range |

The status bar at the bottom shows `Showing X of Y flight(s).` when filters are active.

### 2.5 Schedule Generator (Automated Flight Creation)

**Access:** Click **🤖 Schedule** in the sidebar.

This is the flagship automation feature. It bulk-generates flights for an entire date range in seconds.

#### How to Use

1. **Pick a date range:**
   - **Start date** — when the schedule begins
   - **End date** — when it ends (up to 6+ months is fine)
   - Use the **preset buttons** for quick ranges: *1 month · 3 months · 6 months · 1 year*
2. **Choose options:**
   - ☐ **Overwrite existing flights in range** — deletes SCHEDULED flights before regenerating. Flights with **active bookings** are always preserved.
3. **Click Generate Flights.**
4. Watch the **progress bar** and **live log** as flights are created.
5. When done, a summary dialog shows **created**, **skipped**, and **duration**.

#### What Gets Generated

| Rule | Value |
|---|---|
| **Domestic routes** | 3 flights per day |
| **International routes** | 1 flight per day, 2 on weekends |
| **Aircraft assignment** | Round-trip aware, range-aware |
| **Turnaround time** | 45 min domestic / 90 min international |
| **Fares** | Dynamically computed per flight via ML |
| **Flight numbers** | Auto-generated unique sequential numbers |

#### Performance

- **~1,140 flights per second** on this hardware
- A 30-day schedule for ~12 routes completes in **under 1 second**
- Progress bar updates live; UI stays responsive during generation

#### Post-Generation

After completion, the flights page and dashboard refresh automatically. Use the **flight filters** (§2.4) to inspect specific days or routes.

### 2.6 Staff Management

- **Add staff account:** Creates a `User` + `Staff` row
- **Assign to flights:** Pilots, cabin crew, check-in officers

### 2.7 Refund Approvals

For each booking in `REFUND_REQUESTED`:

- **Approve** → status flips to `REFUNDED`, `refund_amount` is set
- **Reject** → status reverts to `CONFIRMED`

### 2.8 Overbooking Advisor (ML)

When a flight is selected on the **Flights** page, a panel below the table shows:

- **Confirmed bookings** on the flight
- **Expected no-shows** (ML prediction)
- **Expected no-show rate**
- **Safe overbooking** count
- **Confidence** (low / medium / high)
- A **recommendation message**

This uses the trained no-show prediction model. Values refresh when you click **Refresh** or select a different flight.

### 2.9 Reports

- Bookings by route
- Revenue by aircraft
- Load factor (% seats sold)
- Refund rate

---

## 3. Staff Guide

**Access:** PySide desktop app (log in as staff)

Staff accounts must be marked as **check-in officers** to access the dashboard.

### 3.1 Check-In

For each passenger:

1. Look up by **booking reference** (e.g., `SN7X4K2A`) or **passport number**
2. Confirm identity (name, passport)
3. Click **Check in**
4. Status flips from `CONFIRMED` to `CHECKED_IN`

### 3.2 Boarding Pass Issuance

After check-in, click **Issue boarding pass**. This generates:

- Boarding pass number
- Boarding gate
- Boarding group (based on seat class — business boards first)

The passenger can then download their PDF from the web app.

### 3.3 Baggage Handling

- Weigh each bag
- Tag it (`bag_tag` auto-generated)
- Attach PDF tag (printed by staff)

### 3.4 Passenger Search

Quick search bar: find any passenger by:

- Booking reference
- Passport number
- Name

---

## 4. Common Passenger Scenarios

### 4.1 Family Trip (Multiple Bookings)

Currently the system handles **one passenger per booking**. For family travel:

1. Each passenger creates their own account, OR
2. One account books multiple separate bookings

> *Multi-passenger booking is a future enhancement.*

### 4.2 Flight Cancelled by Admin

- Passengers see the flight status as `CANCELLED`
- Bookings in `CONFIRMED` state are auto-eligible for full refund
- Passengers can log in → **My Bookings** → **Request refund**

### 4.3 Passenger Can't Log In

- Check email format (must be valid)
- Check password (min 6 chars, case-sensitive)
- Try **Forgot password** (coming soon — currently contact admin)

### 4.4 Lost Booking Reference

- Log in → **My Bookings** → reference shown on each row
- Or check confirmation email (demo — not really sent)

### 4.5 Same Route, Different Price

You may notice that two flights on the **same route** on **different days** have **different prices**. This is expected:

- Peak hours (7–9 AM, 5–7 PM) cost more
- Weekends cost more
- Holiday seasons (Dec, Jan, Jun, Jul) cost more
- Last-minute bookings cost more than long-lead bookings

The ML fare model prices each flight individually. This is how real airlines operate.

### 4.6 Passenger Logs Into the Desktop App

If you log in via the **PySide desktop app** with a passenger account:

- A friendly message appears explaining that passengers should use the web app.
- The web app URL opens automatically in your browser.
- The desktop login window returns so admins or staff can still sign in.

---

## 5. Keyboard Shortcuts

**Web app:**

- `Esc` — close any modal
- `Enter` — submit focused form

**Desktop app:**

- `Ctrl+Q` — quit (if configured)
- `Tab` — navigate fields

---

## 6. Browser Support

The web app works on:

- Chrome / Edge (latest)
- Firefox (latest)
- Safari 15+

**Not supported:** IE11, very old Android browsers.

---

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| Can't log in | Check credentials; ensure backend is running on `127.0.0.1:8000` |
| "Not authenticated" | Log out and log back in (JWT expired) |
| Seat map doesn't load | Refresh; check backend logs |
| Payment fails | Check card number (Luhn valid), expiry is future |
| PDF doesn't download | Check popup blocker; try a different browser |
| Refund request fails | Booking must be `CONFIRMED`, not yet departed |
| Recommendations don't load | Ensure the recommender model is trained: `python -m app.ml.recommender.train` |
| Overbooking Advisor shows "model not trained" | Run `python -m app.ml.no_show.train` |
| Same fares on all flights | ML fare model missing — run `python -m app.ml.fare.generate_data` then `python -m app.ml.fare.train`, then regenerate flights |
| Flight page too slow | Use the filter toolbar (search / status / date range) to narrow the result set |
| ATR aircraft on long routes (legacy) | Run `python -m scripts.purge_future_flights` then regenerate |

---

## 8. Support

- Check the API docs at <http://127.0.0.1:8000/docs>
- Inspect browser DevTools → Network tab for API calls
- Check backend logs in the uvicorn terminal
- Read the ML documentation at `docs/ML_FEATURES.md`
- Read the setup guide at `docs/SETUP.md` for installation issues