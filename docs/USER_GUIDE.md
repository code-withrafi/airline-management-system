#  User Guide

> **Airline Management System**
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

### 1.3 Booking a Flight

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

### 1.4 Completing Payment

The demo uses a **mock payment gateway**. Any card number passing the Luhn check will be approved.

**Test card:**

- Number: `4242 4242 4242 4242`
- Name: your name
- Expiry: `12/28` (any future date)
- CVC: `123`

Click **Pay $X.XX**. You'll be redirected to a **green confirmation screen**.

### 1.5 Downloading Your Ticket

**From the confirmation screen:** Click **Download ticket**.

**From My Bookings:** Click the **Ticket** button on any confirmed booking.

You'll get a PDF e-ticket with:

- Passenger details
- Flight info
- Seat assignment
- Fare

### 1.6 Managing Bookings

Go to **My Bookings** from the navbar. Each booking shows:

- Reference number
- Status badge
- Total paid
- Actions: **Details / Ticket / Refund / Cancel**

Click **Details** for the full booking page with timeline.

### 1.7 Requesting a Refund

1. On a **CONFIRMED** booking, click **Refund**.
2. A modal opens showing:
   - **Refund policy** (25%–100% depending on timing)
   - **Your refund amount**
3. Click **Request $X.XX**.
4. Status changes to **REFUND_REQUESTED** (pending admin review).
5. Once an admin approves, status becomes **REFUNDED**.

### 1.8 Profile Management

Click your **avatar** (top-right) → **Profile**:

- **Personal information:** edit name, phone, DOB, passport, address
- **Account & security:** change your password

Changes are saved immediately.

### 1.9 Signing Out

Click **Sign out** in the top-right. Your JWT is cleared. You can sign back in anytime.

---

## 2. Administrator Guide

**Access:** PySide desktop app (`python -m app.main` → log in as admin)

### 2.1 Dashboard

Shows:

- Total flights today
- Active aircraft
- Bookings count
- Revenue

### 2.2 Aircraft Management

- **Add aircraft:** Registration, manufacturer, model, capacity → seats auto-generate
- **Edit aircraft:** Update details (capacity changes require care with existing bookings)
- **View seats:** Inspect the layout generated for each aircraft

### 2.3 Route Management

- **Add route:** Origin, destination, distance, duration
- **Toggle active / inactive**

### 2.4 Flight Management

- **Add flight:** Number, route, aircraft, times, base fare
- **Update status:** `SCHEDULED` → `BOARDING` → `DEPARTED` → `ARRIVED`
- **Cancel flight:** All bookings auto-refund eligible
- **Assign aircraft:** Swap aircraft on an existing flight

### 2.5 Staff Management

- **Add staff account:** Creates a `User` + `Staff` row
- **Assign to flights:** Pilots, cabin crew, check-in officers

### 2.6 Refund Approvals

For each booking in `REFUND_REQUESTED`:

- **Approve** → status flips to `REFUNDED`, `refund_amount` is set
- **Reject** → status reverts to `CONFIRMED`

### 2.7 Reports

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

---

## 8. Support

- Check the API docs at <http://127.0.0.1:8000/docs>
- Inspect browser DevTools → Network tab for API calls
- Check backend logs in the uvicorn terminal