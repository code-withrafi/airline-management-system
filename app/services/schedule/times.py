# app/services/schedule/times.py
"""
Departure time templates.

Given a target frequency for a day, returns a list of departure
times (as datetime.time objects) with a small random jitter so
schedules don't look robotic.
"""

import random
from datetime import time


class TimeTemplateGenerator:
    """
    Provides departure times for each frequency level.

    Higher frequencies spread flights across the day. Jitter is
    applied to avoid every route having flights at identical times.
    """

    TEMPLATES = {
        1: [time(9, 0)],                                   # one flight, mid-morning
        2: [time(8, 0), time(18, 0)],                      # morning + evening
        3: [time(7, 0), time(13, 0), time(19, 0)],         # spread across day
    }

    # Random jitter range in minutes (± this value)
    JITTER_MINUTES = 30

    @classmethod
    def for_frequency(cls, n: int) -> list[time]:
        """
        Return a list of departure times for the given frequency.

        If n > 3, extra flights fill the gaps between existing ones.
        """
        if n <= 0:
            return []

        base = cls.TEMPLATES.get(n)
        if base is None and n > 3:
            # Fall back to 3-slot template + interpolated extras
            base = cls.TEMPLATES[3]
            # Interpolate extra times
            extras = cls._extra_times(n - 3, base)
            base = sorted(list(base) + extras)

        return [cls._jitter(t) for t in base]

    @staticmethod
    def _extra_times(count: int, base: list[time]) -> list[time]:
        """Insert `count` extra times between the base template hours."""
        extras = []
        # Between 7 and 13 → 10:00
        # Between 13 and 19 → 16:00
        candidates = [time(10, 0), time(16, 0), time(21, 0), time(5, 0)]
        for i in range(count):
            extras.append(candidates[i % len(candidates)])
        return extras

    @classmethod
    def _jitter(cls, t: time) -> time:
        """Add a random ±JITTER_MINUTES to a time."""
        total_minutes = t.hour * 60 + t.minute
        delta = random.randint(-cls.JITTER_MINUTES, cls.JITTER_MINUTES)
        total_minutes = max(0, min(23 * 60 + 59, total_minutes + delta))
        return time(total_minutes // 60, total_minutes % 60)