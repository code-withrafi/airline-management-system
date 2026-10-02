"""
PDF generation for boarding passes and baggage tags.

Uses reportlab + qrcode to produce airline-style documents.
"""

import io
import json
from pathlib import Path

import qrcode

from reportlab.lib import colors
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


# ----------------------------------------------------------------------
# Colours
# ----------------------------------------------------------------------

BRAND_BLUE = colors.HexColor("#1E40AF")
DARK_TEXT = colors.HexColor("#0F172A")
MUTED_TEXT = colors.HexColor("#64748B")
LIGHT_BG = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#E2E8F0")

# Boarding-pass-only palette. The baggage tag keeps using the colours
# above untouched; these are a richer, more "airline premium" tone
# used solely for the new boarding pass layout.
BP_NAVY = colors.HexColor("#0B2545")
BP_NAVY_DEEP = colors.HexColor("#081B33")
BP_GOLD = colors.HexColor("#C9A24B")
BP_PANEL_BG = colors.HexColor("#EEF1F6")
BP_CARD_BG = colors.white
BP_WHITE_MUTED = colors.HexColor("#C7D2E3")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _draw_label(c, x, y, text):
    """Small grey label above a field."""
    c.setFont("Helvetica", 7)
    c.setFillColor(MUTED_TEXT)
    c.drawString(x, y, text)


def _draw_value(c, x, y, text, font_size=11):
    """Value below a label."""
    c.setFont("Helvetica-Bold", font_size)
    c.setFillColor(DARK_TEXT)
    c.drawString(x, y, text)


def _draw_airplane_shape(c, cx, cy, size, angle=0.0, alpha=1.0,
                          fill_color=None, stroke_color=None):
    """
    Draw a simple top-down airplane silhouette centred at (cx, cy).

    The nose points along +y before rotation; `angle` is degrees,
    counter-clockwise (0 = nose pointing straight up).
    """
    pts = [
        (0.00, 1.00),
        (0.10, 0.55),
        (0.95, -0.25),
        (0.95, -0.42),
        (0.12, -0.05),
        (0.10, -0.55),
        (0.40, -0.80),
        (0.40, -0.94),
        (0.00, -0.78),
        (-0.40, -0.94),
        (-0.40, -0.80),
        (-0.10, -0.55),
        (-0.12, -0.05),
        (-0.95, -0.42),
        (-0.95, -0.25),
        (-0.10, 0.55),
    ]

    c.saveState()
    c.translate(cx, cy)
    c.rotate(angle)
    fc = fill_color or BP_NAVY
    c.setFillColor(fc, alpha=alpha)
    c.setStrokeColor(stroke_color or fc, alpha=alpha)

    p = c.beginPath()
    p.moveTo(pts[0][0] * size, pts[0][1] * size)
    for px, py in pts[1:]:
        p.lineTo(px * size, py * size)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    c.restoreState()


def _draw_dashed_perforation(c, x, y_bottom, y_top, notch_radius=3.2):
    """Vertical tear-off perforation line with rounded notches top/bottom."""
    c.saveState()
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.setDash(3, 3)
    c.line(x, y_bottom + notch_radius, x, y_top - notch_radius)
    c.setDash()

    c.setFillColor(colors.white)
    c.circle(x, y_bottom, notch_radius, stroke=0, fill=1)
    c.circle(x, y_top, notch_radius, stroke=0, fill=1)
    c.restoreState()


def _draw_fake_barcode(c, x, y, num_bars, bar_h, max_bar_w=2):
    """A row of pseudo-random bars used as a decorative barcode."""
    c.setFillColor(colors.black)
    bar_x = x
    for i in range(num_bars):
        w = 1 + (i % 3)
        c.rect(bar_x, y, min(w, max_bar_w), bar_h, stroke=0, fill=1)
        bar_x += w + 1.6


def _make_qr_buffer(data, box_size=4, border=1):
    """
    Generate a QR code PNG in memory.

    `data` may be a string or a dict; dicts are JSON-serialized.
    Returns a BytesIO buffer positioned at 0.
    """
    if isinstance(data, dict):
        payload = json.dumps(data, separators=(",", ":"))
    else:
        payload = str(data)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _draw_qr(c, data, x, y, size):
    """
    Draw a QR code inside a square of the given size,
    positioned with its bottom-left corner at (x, y).
    """
    buf = _make_qr_buffer(data)
    c.drawImage(
        ImageReader(buf),
        x,
        y,
        width=size,
        height=size,
        preserveAspectRatio=True,
        anchor="sw",
        mask="auto",
    )


# ----------------------------------------------------------------------
# Boarding pass
# ----------------------------------------------------------------------

def generate_boarding_pass_pdf(
    boarding_pass,
    booking,
    output_path,
):
    """
    Generate a boarding pass PDF from model objects.

    boarding_pass: BoardingPass ORM object
    booking:       Booking ORM object (with flight, seat, passenger, route loaded)
    output_path:   path to write the PDF

    Landscape layout with two coupons, like a real airline pass:
      - main coupon (left)  = passenger copy
      - stub       (right)  = boarding gate / final check-in copy
    """

    output_path = Path(output_path)

    PASS_WIDTH = 220 * mm
    PASS_HEIGHT = 108 * mm
    STUB_WIDTH = 60 * mm
    MAIN_WIDTH = PASS_WIDTH - STUB_WIDTH

    c = canvas.Canvas(
        str(output_path),
        pagesize=(PASS_WIDTH, PASS_HEIGHT),
    )

    width, height = PASS_WIDTH, PASS_HEIGHT

    passenger = booking.passenger
    flight = booking.flight
    seat = booking.seat

    route = flight.route
    origin_code = ""
    destination_code = ""

    if route is not None:
        if route.origin_airport is not None:
            origin_code = route.origin_airport.iata_code
        if route.destination_airport is not None:
            destination_code = route.destination_airport.iata_code

    # --------------------------------------------------------------
    # Card background + outer border
    # --------------------------------------------------------------

    c.setFillColor(BP_CARD_BG)
    c.rect(0, 0, width, height, stroke=0, fill=1)

    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.rect(1, 1, width - 2, height - 2, stroke=1, fill=0)

    # Stub panel gets a faint tint so the two coupons read as separate
    c.setFillColor(BP_PANEL_BG)
    c.rect(MAIN_WIDTH, 0, STUB_WIDTH, height, stroke=0, fill=1)

    # --------------------------------------------------------------
    # Watermark airplanes (drawn first, behind all text)
    # --------------------------------------------------------------

    _draw_airplane_shape(
        c, MAIN_WIDTH * 0.58, height * 0.38, 30 * mm,
        angle=-18, alpha=0.055, fill_color=BP_NAVY,
    )
    _draw_airplane_shape(
        c, MAIN_WIDTH + STUB_WIDTH / 2, height * 0.52, 14 * mm,
        angle=-18, alpha=0.07, fill_color=BP_NAVY,
    )

    # ================================================================
    # MAIN COUPON — passenger copy
    # ================================================================

    header_h = 20 * mm
    c.setFillColor(BP_NAVY)
    c.rect(0, height - header_h, MAIN_WIDTH, header_h, stroke=0, fill=1)
    c.setFillColor(BP_GOLD)
    c.rect(0, height - header_h - 1.2 * mm, MAIN_WIDTH, 1.2 * mm, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(8 * mm, height - 11 * mm, "AIRLINE")
    c.setFont("Helvetica", 8)
    c.setFillColor(BP_WHITE_MUTED)
    c.drawString(8 * mm, height - 17 * mm, "BOARDING PASS  \u2022  PASSENGER COPY")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.white)
    c.drawRightString(
        MAIN_WIDTH - 8 * mm, height - 11 * mm, boarding_pass.boarding_pass_number
    )
    c.setFont("Helvetica", 7)
    c.setFillColor(BP_WHITE_MUTED)
    c.drawRightString(MAIN_WIDTH - 8 * mm, height - 17 * mm, "PASS NO.")

    # --------------------------------------------------------------
    # QR code — top-right of main coupon, below the header
    # --------------------------------------------------------------

    qr_size = 26 * mm
    qr_x = MAIN_WIDTH - 8 * mm - qr_size
    qr_y = height - header_h - 1.2 * mm - qr_size - 3 * mm

    qr_payload = {
        "ref": booking.booking_reference,
        "pass": boarding_pass.boarding_pass_number,
        "flight": flight.flight_number,
        "from": origin_code,
        "to": destination_code,
        "seat": seat.seat_number if seat else None,
        "gate": boarding_pass.boarding_gate,
        "group": boarding_pass.boarding_group,
        "passenger": f"{passenger.first_name} {passenger.last_name}",
        "passport": passenger.passport_number,
    }

    _draw_qr(c, qr_payload, qr_x, qr_y, qr_size)

    # --------------------------------------------------------------
    # Passenger / Flight
    # --------------------------------------------------------------

    y = height - header_h - 9 * mm

    _draw_label(c, 8 * mm, y, "PASSENGER")
    _draw_value(
        c, 8 * mm, y - 5 * mm,
        f"{passenger.first_name} {passenger.last_name}",
        font_size=13,
    )

    # Right column labels shift left to leave room for the QR
    right_col_x = MAIN_WIDTH - 46 * mm - qr_size - 4 * mm

    _draw_label(c, right_col_x, y, "FLIGHT")
    _draw_value(
        c, right_col_x, y - 5 * mm,
        flight.flight_number, font_size=13,
    )

    # --------------------------------------------------------------
    # Route
    # --------------------------------------------------------------

    y -= 17 * mm

    _draw_label(c, 8 * mm, y, "FROM")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(BP_NAVY)
    c.drawString(8 * mm, y - 8 * mm, origin_code or "\u2014")

    _draw_label(c, right_col_x, y, "TO")
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(BP_NAVY)
    c.drawString(right_col_x, y - 8 * mm, destination_code or "\u2014")

    # Dashed flight-path connector with a small plane icon
    line_y = y - 4.5 * mm
    line_x1 = 34 * mm
    line_x2 = right_col_x - 4 * mm
    c.setStrokeColor(BP_GOLD)
    c.setLineWidth(1)
    c.setDash(1, 2)
    c.line(line_x1, line_y, line_x2, line_y)
    c.setDash()
    _draw_airplane_shape(
        c, (line_x1 + line_x2) / 2, line_y, 4 * mm,
        angle=-90, alpha=1, fill_color=BP_GOLD,
    )

    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED_TEXT)
    c.drawCentredString(
        (line_x1 + line_x2) / 2,
        line_y + 3.5 * mm,
        flight.departure_time.strftime("%d %b %Y  \u2022  %H:%M"),
    )

    # --------------------------------------------------------------
    # Seat / Gate / Group
    # --------------------------------------------------------------

    y -= 20 * mm
    col_w = (MAIN_WIDTH - 16 * mm) / 3
    field_xs = [8 * mm, 8 * mm + col_w, 8 * mm + 2 * col_w]

    _draw_label(c, field_xs[0], y, "SEAT")
    _draw_value(
        c, field_xs[0], y - 5 * mm,
        seat.seat_number if seat else "\u2014", font_size=14,
    )

    _draw_label(c, field_xs[1], y, "GATE")
    _draw_value(c, field_xs[1], y - 5 * mm, boarding_pass.boarding_gate, font_size=14)

    _draw_label(c, field_xs[2], y, "GROUP")
    _draw_value(c, field_xs[2], y - 5 * mm, boarding_pass.boarding_group, font_size=14)

    # --------------------------------------------------------------
    # Passport + aircraft
    # --------------------------------------------------------------

    y -= 13 * mm

    _draw_label(c, field_xs[0], y, "PASSPORT")
    _draw_value(
        c, field_xs[0], y - 4.5 * mm, passenger.passport_number, font_size=9.5
    )

    _draw_label(c, field_xs[1], y, "AIRCRAFT")
    _draw_value(
        c, field_xs[1], y - 4.5 * mm,
        flight.aircraft.model if flight.aircraft else "\u2014",
        font_size=9.5,
    )

    # --------------------------------------------------------------
    # Barcode + footer (fare intentionally omitted)
    # --------------------------------------------------------------

    barcode_y = 10 * mm
    _draw_fake_barcode(c, 8 * mm, barcode_y, 60, 8 * mm)

    c.setStrokeColor(BORDER)
    c.line(8 * mm, 7 * mm, MAIN_WIDTH - 8 * mm, 7 * mm)
    c.setFont("Helvetica", 6.5)
    c.setFillColor(MUTED_TEXT)
    c.drawString(
        8 * mm, 4.5 * mm,
        f"Issued: {boarding_pass.issued_at.strftime('%d %b %Y')}",
    )
    c.drawString(
        8 * mm, 1.5 * mm,
        "Please arrive at the gate 30 minutes before departure.",
    )

    # Perforation between main coupon and stub
    _draw_dashed_perforation(c, MAIN_WIDTH, 0, height)

    # ================================================================
    # STUB — boarding gate / final check-in copy
    # ================================================================

    stub_x0 = MAIN_WIDTH
    stub_header_h = 14 * mm

    c.setFillColor(BP_NAVY_DEEP)
    c.rect(stub_x0, height - stub_header_h, STUB_WIDTH, stub_header_h, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(stub_x0 + STUB_WIDTH / 2, height - 7 * mm, "BOARDING GATE")
    c.setFont("Helvetica", 6.5)
    c.setFillColor(BP_WHITE_MUTED)
    c.drawCentredString(
        stub_x0 + STUB_WIDTH / 2, height - 11.5 * mm, "FINAL CHECK-IN STUB"
    )

    sy = height - stub_header_h - 9 * mm
    sx = stub_x0 + 6 * mm

    _draw_label(c, sx, sy, "PASSENGER")
    c.setFont("Helvetica-Bold", 9.5)
    c.setFillColor(DARK_TEXT)
    c.drawString(sx, sy - 4.5 * mm, f"{passenger.first_name} {passenger.last_name}")

    sy -= 11 * mm
    _draw_label(c, sx, sy, "FLIGHT / ROUTE")
    _draw_value(
        c, sx, sy - 4.5 * mm,
        f"{flight.flight_number}  {origin_code}\u2192{destination_code}",
        font_size=9.5,
    )

    sy -= 11 * mm
    _draw_label(c, sx, sy, "DEPARTS")
    _draw_value(
        c, sx, sy - 4.5 * mm,
        flight.departure_time.strftime("%d %b %Y, %H:%M"),
        font_size=9.5,
    )

    sy -= 12 * mm
    stub_col_w = (STUB_WIDTH - 12 * mm) / 2
    stub_field_xs = [sx, sx + stub_col_w]

    _draw_label(c, stub_field_xs[0], sy, "SEAT")
    _draw_value(
        c, stub_field_xs[0], sy - 5 * mm,
        seat.seat_number if seat else "\u2014", font_size=13,
    )
    _draw_label(c, stub_field_xs[1], sy, "GROUP")
    _draw_value(
        c, stub_field_xs[1], sy - 5 * mm, boarding_pass.boarding_group, font_size=13
    )

    sy -= 14 * mm
    _draw_label(c, sx, sy, "GATE")
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(BP_NAVY)
    c.drawString(sx, sy - 7 * mm, boarding_pass.boarding_gate)

    # Small barcode + pass number at the bottom of the stub
    _draw_fake_barcode(c, sx, 10 * mm, 24, 8 * mm, max_bar_w=1.6)
    c.setFont("Helvetica", 6.5)
    c.setFillColor(MUTED_TEXT)
    c.drawString(sx, 6.5 * mm, boarding_pass.boarding_pass_number)

    c.showPage()
    c.save()

    return output_path


# ----------------------------------------------------------------------
# Baggage tag
# ----------------------------------------------------------------------

def generate_baggage_tag_pdf(
    baggage,
    checkin,
    booking,
    output_path,
):
    """
    Generate a baggage tag PDF with a tear-off stub.

    baggage:  Baggage ORM object
    checkin:  CheckIn ORM object (for context)
    booking:  Booking ORM object (with flight, passenger)
    output_path: path to write the PDF
    """

    output_path = Path(output_path)

    # Baggage tags are long strips: ~2in x 5in
    tag_width = 2 * 72          # 2 inches in points
    tag_height = 5 * 72         # 5 inches in points

    c = canvas.Canvas(
        str(output_path),
        pagesize=(tag_width, tag_height),
    )

    passenger = booking.passenger
    flight = booking.flight

    route = flight.route
    origin_code = ""
    destination_code = ""

    if route is not None:
        if route.origin_airport is not None:
            origin_code = route.origin_airport.iata_code
        if route.destination_airport is not None:
            destination_code = route.destination_airport.iata_code

    # --------------------------------------------------------------
    # Main tag (top 3/4 of the strip)
    # --------------------------------------------------------------

    c.setFillColor(BRAND_BLUE)
    c.rect(0, tag_height - 40, tag_width, 40, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(8, tag_height - 20, "AIRLINE")
    c.setFont("Helvetica", 8)
    c.drawString(8, tag_height - 32, "BAGGAGE TAG")

    # Tag number
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(8, tag_height - 60, baggage.bag_tag)

    y = tag_height - 85
    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED_TEXT)
    c.drawString(8, y, "PASSENGER")
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(
        8, y - 11,
        f"{passenger.first_name} {passenger.last_name}",
    )

    y -= 30
    c.setFillColor(MUTED_TEXT)
    c.setFont("Helvetica", 8)
    c.drawString(8, y, "FLIGHT")
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(
        8, y - 11,
        f"{flight.flight_number}  "
        f"{origin_code} \u2192 {destination_code}",
    )

    y -= 30
    c.setFillColor(MUTED_TEXT)
    c.setFont("Helvetica", 8)
    c.drawString(8, y, "WEIGHT")
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(8, y - 11, f"{baggage.weight_kg} kg")

    # Fake barcode strip
    y -= 30
    c.setFillColor(colors.black)
    bar_x = 8
    bar_y = y - 10
    bar_h = 20
    bar_w = 2

    for i in range(30):
        width_var = 1 + (i % 3)
        c.rect(
            bar_x,
            bar_y,
            width_var,
            bar_h,
            stroke=0,
            fill=1,
        )
        bar_x += width_var + 2

    # --------------------------------------------------------------
    # Cut line
    # --------------------------------------------------------------

    cut_y = tag_height * 0.3
    c.setStrokeColor(BORDER)
    c.setDash(4, 4)
    c.line(0, cut_y, tag_width, cut_y)
    c.setDash()

    c.setFillColor(MUTED_TEXT)
    c.setFont("Helvetica", 6)
    c.drawCentredString(tag_width / 2, cut_y + 4, "CUT HERE")

    # --------------------------------------------------------------
    # Stub (bottom 30%)
    # --------------------------------------------------------------

    c.setFillColor(BRAND_BLUE)
    c.rect(0, cut_y - 18, tag_width, 18, stroke=0, fill=1)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(8, cut_y - 12, "AIRLINE")

    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(8, cut_y - 35, baggage.bag_tag)

    c.setFont("Helvetica", 7)
    c.setFillColor(MUTED_TEXT)
    c.drawString(8, cut_y - 50, "PASSENGER")
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(
        8, cut_y - 60,
        f"{passenger.first_name} {passenger.last_name}",
    )

    c.setFillColor(MUTED_TEXT)
    c.setFont("Helvetica", 7)
    c.drawString(8, cut_y - 74, "FLIGHT")
    c.setFillColor(DARK_TEXT)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(8, cut_y - 84, flight.flight_number)

    c.showPage()
    c.save()

    return output_path

# ----------------------------------------------------------------------
# E-ticket / itinerary receipt
# ----------------------------------------------------------------------

def generate_ticket_pdf(booking, output_path):
    """
    Generate an e-ticket / itinerary receipt PDF from a Booking.

    booking:      Booking ORM object with .flight, .flight.route,
                  .flight.aircraft, .passenger, .seat loaded.
    output_path:  path to write the PDF.
    """

    output_path = Path(output_path)

    PAGE_W = 190 * mm
    PAGE_H = 260 * mm

    c = canvas.Canvas(str(output_path), pagesize=(PAGE_W, PAGE_H))

    passenger = booking.passenger
    flight = booking.flight
    seat = booking.seat
    aircraft = flight.aircraft if flight else None
    route = flight.route if flight else None

    origin_code = ""
    origin_city = ""
    destination_code = ""
    destination_city = ""

    if route is not None:
        if route.origin_airport is not None:
            origin_code = route.origin_airport.iata_code
            origin_city = route.origin_airport.city
        if route.destination_airport is not None:
            destination_code = route.destination_airport.iata_code
            destination_city = route.destination_airport.city

    # ---------------- Outer border ----------------

    c.setFillColor(colors.white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.rect(6 * mm, 6 * mm, PAGE_W - 12 * mm, PAGE_H - 12 * mm, stroke=1, fill=0)

    # ---------------- Header band ----------------

    header_h = 24 * mm
    c.setFillColor(BP_NAVY)
    c.rect(
        6 * mm,
        PAGE_H - 6 * mm - header_h,
        PAGE_W - 12 * mm,
        header_h,
        stroke=0,
        fill=1,
    )
    c.setFillColor(BP_GOLD)
    c.rect(
        6 * mm,
        PAGE_H - 6 * mm - header_h - 1.2 * mm,
        PAGE_W - 12 * mm,
        1.2 * mm,
        stroke=0,
        fill=1,
    )

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(12 * mm, PAGE_H - 22 * mm, "AIRLINE")

    c.setFont("Helvetica", 9)
    c.setFillColor(BP_WHITE_MUTED)
    c.drawString(12 * mm, PAGE_H - 28 * mm, "E-TICKET  \u2022  ITINERARY RECEIPT")

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.white)
    c.drawRightString(
        PAGE_W - 12 * mm,
        PAGE_H - 20 * mm,
        booking.booking_reference,
    )
    c.setFont("Helvetica", 8)
    c.setFillColor(BP_WHITE_MUTED)
    c.drawRightString(
        PAGE_W - 12 * mm,
        PAGE_H - 26 * mm,
        "BOOKING REFERENCE",
    )

    # ---------------- Status / meta line ----------------

    y = PAGE_H - 6 * mm - header_h - 1.2 * mm - 8 * mm

    status_value = (
        booking.status.value
        if hasattr(booking.status, "value")
        else str(booking.status)
    )

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(BP_NAVY)
    c.drawString(12 * mm, y, f"STATUS: {status_value}")

    issued_at = (
        booking.booked_at.strftime("%d %b %Y, %H:%M")
        if booking.booked_at
        else "-"
    )
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED_TEXT)
    c.drawRightString(PAGE_W - 12 * mm, y, f"Issued: {issued_at}")

    # ---------------- QR code ----------------

    qr_size = 30 * mm
    qr_x = PAGE_W - 12 * mm - qr_size
    qr_y = y - qr_size - 4 * mm

    qr_payload = {
        "ref": booking.booking_reference,
        "passenger": (
            f"{passenger.first_name} {passenger.last_name}"
            if passenger
            else None
        ),
        "flight": flight.flight_number if flight else None,
        "from": origin_code,
        "to": destination_code,
        "seat": seat.seat_number if seat else None,
        "fare": str(booking.fare_amount),
    }

    _draw_qr(c, qr_payload, qr_x, qr_y, qr_size)

    # ---------------- Section helper ----------------

    def section(title, y_top):
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(BP_NAVY)
        c.drawString(12 * mm, y_top, title.upper())
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.line(
            12 * mm,
            y_top - 2 * mm,
            PAGE_W - 12 * mm,
            y_top - 2 * mm,
        )

    def kv(key, value, x, y_pos, value_size=10):
        c.setFont("Helvetica", 7)
        c.setFillColor(MUTED_TEXT)
        c.drawString(x, y_pos, key.upper())
        c.setFont("Helvetica-Bold", value_size)
        c.setFillColor(DARK_TEXT)
        c.drawString(x, y_pos - 4.5 * mm, str(value) if value else "\u2014")

    # ---------------- Passenger section ----------------

    y = qr_y - 6 * mm

    section("Passenger", y)
    y -= 8 * mm

    passenger_name = (
        f"{passenger.first_name} {passenger.last_name}"
        if passenger
        else "-"
    )

    left_x = 12 * mm
    right_x = PAGE_W / 2 + 4 * mm

    kv("Name", passenger_name, left_x, y)
    kv(
        "Passport",
        passenger.passport_number if passenger else "-",
        right_x,
        y,
    )

    y -= 13 * mm

    kv(
        "Phone",
        passenger.phone if passenger else "-",
        left_x,
        y,
    )
    kv(
        "Email",
        passenger.user.email
        if passenger and passenger.user
        else "-",
        right_x,
        y,
    )

    # ---------------- Flight section ----------------

    y -= 16 * mm
    section("Flight", y)
    y -= 8 * mm

    flight_number = flight.flight_number if flight else "-"
    dep_date = (
        flight.departure_time.strftime("%d %b %Y")
        if flight
        else "-"
    )
    dep_time = (
        flight.departure_time.strftime("%H:%M")
        if flight
        else "-"
    )
    arr_time = (
        flight.arrival_time.strftime("%H:%M")
        if flight
        else "-"
    )

    kv("Flight No.", flight_number, left_x, y)
    kv("Date", dep_date, right_x, y)

    y -= 13 * mm

    kv("Departure", dep_time, left_x, y)
    kv("Arrival", arr_time, right_x, y)

    y -= 13 * mm

    kv(
        "From",
        f"{origin_code} - {origin_city}" if origin_code else "-",
        left_x,
        y,
    )
    kv(
        "To",
        f"{destination_code} - {destination_city}"
        if destination_code
        else "-",
        right_x,
        y,
    )

    y -= 13 * mm

    kv(
        "Aircraft",
        getattr(aircraft, "model", "-") if aircraft else "-",
        left_x,
        y,
    )
    kv(
        "Registration",
        getattr(aircraft, "registration_number", "-")
        if aircraft
        else "-",
        right_x,
        y,
    )

    # ---------------- Seat section ----------------

    y -= 16 * mm
    section("Seat", y)
    y -= 8 * mm

    seat_number = seat.seat_number if seat else "-"
    seat_class = (
        seat.seat_class.value
        if seat and hasattr(seat.seat_class, "value")
        else "-"
    )
    seat_position = (
        seat.position.value
        if seat and hasattr(seat.position, "value")
        else "-"
    )

    kv("Seat", seat_number, left_x, y)
    kv("Class", seat_class, right_x, y)

    y -= 13 * mm

    kv("Position", seat_position, left_x, y)

    # ---------------- Fare section ----------------

    y -= 16 * mm
    section("Fare", y)
    y -= 8 * mm

    kv("Total Paid", f"${booking.fare_amount}", left_x, y)

    if booking.refund_amount is not None:
        kv(
            "Refund Amount",
            f"${booking.refund_amount}",
            right_x,
            y,
        )

    # ---------------- Footer ----------------

    c.setStrokeColor(BORDER)
    c.line(
        12 * mm,
        20 * mm,
        PAGE_W - 12 * mm,
        20 * mm,
    )

    c.setFont("Helvetica", 7.5)
    c.setFillColor(MUTED_TEXT)
    c.drawString(
        12 * mm,
        15 * mm,
        "Present this e-ticket at the check-in counter.",
    )
    c.drawString(
        12 * mm,
        11 * mm,
        "Please arrive at the airport at least 2 hours before departure.",
    )
    c.setFont("Helvetica-Oblique", 6.5)
    c.drawString(
        12 * mm,
        7 * mm,
        "This document is a booking confirmation, not a boarding pass.",
    )

    c.showPage()
    c.save()

    return output_path
