# app/services/seat_generator.py
from app.models import (
    SeatClass,
    SeatPosition,
)


class SeatGenerator:
    """
    Generates a realistic seat layout for a given aircraft capacity.

    Layout rules
    ------------
    - Business cabin: first 2 rows, 6 seats per row (A B C | D E F)
    - Economy cabin : all remaining rows, 6 seats per row
    - The last economy row may be partial if capacity isn't a multiple of 6

    Example — a 162-seat Boeing 737-800:
        2 business rows × 6 = 12 business seats
        25 economy rows × 6 = 150 economy seats
        Total = 162 ✅

    Aircraft with capacity ≤ 12 get all-business cabins (no economy).
    """

    BUSINESS_ROWS = 2

    LAYOUT = [
        ("A", SeatPosition.WINDOW),
        ("B", SeatPosition.MIDDLE),
        ("C", SeatPosition.AISLE),
        ("D", SeatPosition.AISLE),
        ("E", SeatPosition.MIDDLE),
        ("F", SeatPosition.WINDOW),
    ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def generate(capacity: int):
        """
        Return a list of seat dicts for an aircraft of the given capacity.

        Each dict has:
            seat_number  str           e.g. "1A", "27F"
            row_number   int
            position     SeatPosition  enum
            seat_class   SeatClass     enum
        """
        if not isinstance(capacity, int) or capacity <= 0:
            return []

        seats: list[dict] = []
        created = 0

        seats_per_row = len(SeatGenerator.LAYOUT)
        biz_max = SeatGenerator.BUSINESS_ROWS * seats_per_row

        # Tiny aircraft: fold everything into business
        biz_target = min(capacity, biz_max)

        # ---- Business cabin ----
        row = 1
        while created < biz_target:
            for letter, position in SeatGenerator.LAYOUT:
                if created >= biz_target:
                    break
                seats.append({
                    "seat_number": f"{row}{letter}",
                    "row_number": row,
                    "position": position,
                    "seat_class": SeatClass.BUSINESS,
                })
                created += 1
            row += 1

        # ---- Economy cabin ----
        while created < capacity:
            for letter, position in SeatGenerator.LAYOUT:
                if created >= capacity:
                    break
                seats.append({
                    "seat_number": f"{row}{letter}",
                    "row_number": row,
                    "position": position,
                    "seat_class": SeatClass.ECONOMY,
                })
                created += 1
            row += 1

        return seats