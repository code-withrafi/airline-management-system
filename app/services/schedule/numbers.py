# app/services/schedule/numbers.py
"""
Flight number generation.

Uses a per-generation counter that starts after the highest
existing flight number so we never collide with admin-created
flights.
"""

import re

from app.models.flight import Flight


FLIGHT_NUMBER_PREFIX = "SN"


class FlightNumberGenerator:
    """
    Produces sequential, unique flight numbers like SN1001, SN1002, ...
    """

    def __init__(self, session, prefix: str = FLIGHT_NUMBER_PREFIX):
        self.session = session
        self.prefix = prefix
        self._counter = self._find_next_counter()

    def _find_next_counter(self) -> int:
        """Return a safe starting number (highest existing + 1)."""
        rows = (
            self.session.query(Flight.flight_number)
            .filter(Flight.flight_number.like(f"{self.prefix}%"))
            .all()
        )
        max_n = 1000   # default start
        pattern = re.compile(rf"^{re.escape(self.prefix)}(\d+)$")

        for (number,) in rows:
            m = pattern.match(number)
            if m:
                max_n = max(max_n, int(m.group(1)))

        return max_n + 1

    def next(self) -> str:
        """Return the next unique flight number."""
        value = f"{self.prefix}{self._counter}"
        self._counter += 1
        return value