# app/services/schedule/frequency.py
"""
Frequency rules for the flight schedule generator.

Encodes business logic for how many flights per day each route
should have, based on route type (domestic vs. international)
and day of week.
"""

from datetime import datetime


class FrequencyPredictor:
    """
    Predicts flights-per-day for a route.

    Rules (confirmed with product owner):
      - Domestic routes: 3 flights per day, every day
      - International routes: 1 flight per day
        → 2 flights on weekends (Saturday / Sunday)
    """

    DOMESTIC_BASE = 3
    INTERNATIONAL_BASE = 1
    INTERNATIONAL_WEEKEND = 2

    @staticmethod
    def is_weekend(date) -> bool:
        return date.weekday() >= 5   # Sat=5, Sun=6

    @staticmethod
    def is_domestic(route) -> bool:
        """A route is domestic if origin and destination are in the same country."""
        if route is None:
            return True
        origin = route.origin_airport
        destination = route.destination_airport
        if origin is None or destination is None:
            return True
        return origin.country == destination.country

    @classmethod
    def flights_per_day(cls, route, date) -> int:
        """Return the number of flights to schedule for this route on this date."""
        if cls.is_domestic(route):
            return cls.DOMESTIC_BASE

        # International
        if cls.is_weekend(date):
            return cls.INTERNATIONAL_WEEKEND
        return cls.INTERNATIONAL_BASE