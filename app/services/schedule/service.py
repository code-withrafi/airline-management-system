# app/services/schedule/service.py
"""
Flight schedule generator — main orchestrator.

Takes a date range and generates flights across all active routes,
using:
  - FrequencyPredictor    → how many flights per day per route
  - TimeTemplateGenerator → which departure times
  - AircraftScheduler     → which aircraft (round-trip + range rules)
  - FlightNumberGenerator → unique flight numbers

Fares are computed dynamically using the ML fare predictor when
available, with a distance-based fallback.
"""

from datetime import date, datetime, time as time_of_day, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.aircraft import Aircraft
from app.models.flight import Flight, FlightStatus
from app.models.route import Route
from app.services.schedule.aircraft import AircraftScheduler
from app.services.schedule.frequency import FrequencyPredictor
from app.services.schedule.numbers import FlightNumberGenerator
from app.services.schedule.times import TimeTemplateGenerator


class ScheduleGenerationError(Exception):
    """Raised when the schedule generation cannot proceed."""


class FlightScheduleGenerator:
    """
    Generates flights for a date range across all routes.
    """

    def __init__(self, session):
        self.session = session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        *,
        start_date: date,
        end_date: date,
        overwrite_existing: bool = False,
        on_progress=None,
    ) -> dict:
        """Generate flights between start_date and end_date (inclusive)."""
        if start_date > end_date:
            raise ScheduleGenerationError(
                "start_date must be before or equal to end_date."
            )

        t0 = datetime.utcnow()

        routes = (
            self.session.query(Route)
            .filter(Route.is_active == True)  # noqa: E712
            .all()
        )
        if not routes:
            raise ScheduleGenerationError("No active routes to schedule.")

        # -------- Overwrite mode --------
        deleted = 0
        if overwrite_existing:
            deleted = self._delete_flights_in_range(start_date, end_date)

        # -------- Precompute schedule slots --------
        slots = self._build_slots(routes, start_date, end_date)
        total = len(slots)

        # -------- Initialize helpers --------
        aircraft_scheduler = AircraftScheduler(self.session)
        number_gen = FlightNumberGenerator(self.session)

        created = 0
        skipped_no_aircraft = 0
        skipped_duplicate = 0
        errors = []
        by_route = {}

        # -------- Iterate --------
        for i, slot in enumerate(slots):
            flight_number = "?"

            try:
                flight_number = number_gen.next()

                # Assign aircraft (with range constraint)
                aircraft_state = aircraft_scheduler.assign(
                    origin_airport_id=slot["origin_airport_id"],
                    destination_airport_id=slot["destination_airport_id"],
                    departure_time=slot["departure_time"],
                    duration_minutes=slot["duration_minutes"],
                    is_international=slot["is_international"],
                    distance_km=slot["distance_km"],
                )

                if aircraft_state is None:
                    skipped_no_aircraft += 1
                    continue

                # Compute fare
                fare = self._compute_fare(
                    route=slot["route"],
                    departure_time=slot["departure_time"],
                )

                # Create flight
                flight = Flight(
                    flight_number=flight_number,
                    route_id=slot["route"].id,
                    aircraft_id=aircraft_state.aircraft_id,
                    departure_time=slot["departure_time"],
                    arrival_time=slot["departure_time"] + timedelta(
                        minutes=slot["duration_minutes"]
                    ),
                    base_fare=fare,
                    status=FlightStatus.SCHEDULED,
                    boarding_gate=None,
                )
                self.session.add(flight)
                created += 1
                by_route[slot["route"].id] = by_route.get(slot["route"].id, 0) + 1

                if created % 100 == 0:
                    self.session.flush()

            except IntegrityError:
                self.session.rollback()
                skipped_duplicate += 1
            except Exception as exc:
                self.session.rollback()
                route_id = slot.get("route").id if slot.get("route") else "?"
                errors.append(f"route={route_id}: {exc}")

            if on_progress and i % 25 == 0:
                on_progress(i + 1, total, f"Generating {flight_number}...")

        # Final commit
        try:
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            raise ScheduleGenerationError(f"Final commit failed: {exc}")

        elapsed = (datetime.utcnow() - t0).total_seconds()

        return {
            "created": created,
            "deleted_existing": deleted,
            "skipped_no_aircraft": skipped_no_aircraft,
            "skipped_duplicate": skipped_duplicate,
            "errors": errors[:10],
            "by_route": by_route,
            "duration_seconds": round(elapsed, 2),
            "aircraft_snapshot": aircraft_scheduler.snapshot(),
        }

    # ------------------------------------------------------------------
    # Slot building
    # ------------------------------------------------------------------

    def _build_slots(self, routes, start_date: date, end_date: date) -> list[dict]:
        """Return a flat list of schedule slots, sorted by departure time."""
        slots = []
        current = start_date

        while current <= end_date:
            for route in routes:
                freq = FrequencyPredictor.flights_per_day(route, current)
                times = TimeTemplateGenerator.for_frequency(freq)
                duration = route.estimated_duration_minutes
                is_intl = not FrequencyPredictor.is_domestic(route)
                distance = int(route.distance_km or 0)

                for t in times:
                    departure = datetime.combine(current, t)
                    slots.append({
                        "route": route,
                        "departure_time": departure,
                        "duration_minutes": duration,
                        "origin_airport_id": route.origin_airport_id,
                        "destination_airport_id": route.destination_airport_id,
                        "is_international": is_intl,
                        "distance_km": distance,
                    })

            current += timedelta(days=1)

        slots.sort(key=lambda s: s["departure_time"])
        return slots

    # ------------------------------------------------------------------
    # Fare
    # ------------------------------------------------------------------

    def _compute_fare(self, *, route, departure_time: datetime) -> Decimal:
        """Return the fare for a generated flight (ML-based when available)."""
        try:
            from app.ml.fare.service import FarePredictorService
            if FarePredictorService.is_available():
                predictor = FarePredictorService(self.session)
                return predictor.predict(
                    route=route,
                    departure_time=departure_time,
                )
        except Exception:
            pass

        try:
            from app.ml.fare.features import base_fare_for_route
            distance = int(route.distance_km if route else 500)
            return Decimal(str(base_fare_for_route(distance)))
        except Exception:
            return Decimal("50.00")

    # ------------------------------------------------------------------
    # Deletion (overwrite mode)
    # ------------------------------------------------------------------

    def _delete_flights_in_range(self, start_date: date, end_date: date) -> int:
        """Delete flights in [start, end] that have no active booking."""
        from app.models.booking import Booking, BookingStatus

        start_dt = datetime.combine(start_date, time_of_day.min)
        end_dt = datetime.combine(end_date, time_of_day.max)

        flights = (
            self.session.query(Flight)
            .filter(
                Flight.departure_time >= start_dt,
                Flight.departure_time <= end_dt,
            )
            .all()
        )

        deleted = 0
        for flight in flights:
            has_booking = (
                self.session.query(Booking)
                .filter(
                    Booking.flight_id == flight.id,
                    Booking.status.in_([
                        BookingStatus.CONFIRMED,
                        BookingStatus.CHECKED_IN,
                        BookingStatus.UNPAID,
                    ]),
                )
                .count()
            ) > 0

            if has_booking:
                continue

            self.session.delete(flight)
            deleted += 1

        self.session.flush()
        return deleted