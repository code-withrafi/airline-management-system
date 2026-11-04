# app/services/schedule/aircraft.py
"""
Aircraft assignment for the flight schedule generator.

The key constraint: when an aircraft flies A → B, the SAME aircraft
must fly B → A later. We track each aircraft's location and
availability timeline, and only assign an aircraft to a new flight
when:
  1. The aircraft is at the flight's origin at departure time
  2. Enough turnaround time has passed since its last arrival
  3. The aircraft is capable of flying the route distance
     (ATR turboprops are blocked from routes > 600 km)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.models.aircraft import Aircraft, AircraftStatus
from app.services.schedule.aircraft_range import aircraft_can_serve_route


# Turnaround times
DOMESTIC_TURNAROUND_MIN = 45
INTERNATIONAL_TURNAROUND_MIN = 90


@dataclass
class _AircraftState:
    aircraft_id: int
    registration: str
    seat_capacity: int
    manufacturer: str
    model: str
    current_location_id: int | None = None       # airport ID
    available_at: datetime | None = None          # when the aircraft is free
    schedule: list = field(default_factory=list)  # list of (departure, arrival)


class AircraftScheduler:
    """
    Assigns aircraft to flights while respecting the round-trip rule
    AND the aircraft range constraint.
    """

    def __init__(self, session):
        self.session = session
        self._state: dict[int, _AircraftState] = {}
        self._load_active_aircraft()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_active_aircraft(self):
        """Load all ACTIVE aircraft."""
        aircraft_list = (
            self.session.query(Aircraft)
            .filter(Aircraft.status == AircraftStatus.ACTIVE)
            .all()
        )

        for a in aircraft_list:
            self._state[a.id] = _AircraftState(
                aircraft_id=a.id,
                registration=a.registration_number,
                seat_capacity=a.seat_capacity,
                manufacturer=a.manufacturer or "",
                model=a.model or "",
                current_location_id=None,
                available_at=None,
                schedule=[],
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assign(
        self,
        *,
        origin_airport_id: int,
        destination_airport_id: int,
        departure_time: datetime,
        duration_minutes: int,
        is_international: bool,
        distance_km: int = 0,
        preferred_aircraft_id: int | None = None,
    ) -> _AircraftState | None:
        """
        Return an aircraft that can operate this flight.

        Returns None if no aircraft is available OR if no aircraft is
        range-capable for the route.
        """
        turnaround = (
            INTERNATIONAL_TURNAROUND_MIN if is_international
            else DOMESTIC_TURNAROUND_MIN
        )
        turnaround_delta = timedelta(minutes=turnaround)
        arrival_time = departure_time + timedelta(minutes=duration_minutes)

        # Build candidate list
        candidates = []
        if preferred_aircraft_id and preferred_aircraft_id in self._state:
            candidates.append(self._state[preferred_aircraft_id])
        for state in self._state.values():
            if state not in candidates:
                candidates.append(state)

        # Sort by earliest availability
        candidates.sort(key=lambda s: s.available_at or datetime.min)

        for state in candidates:
            # ---- Range constraint ----
            if not self._aircraft_in_range(state, distance_km):
                continue

            # ---- Round-trip + turnaround constraint ----
            if self._can_operate(
                state,
                origin_id=origin_airport_id,
                departure_time=departure_time,
                turnaround_delta=turnaround_delta,
            ):
                # Assign it
                state.current_location_id = destination_airport_id
                state.available_at = arrival_time + turnaround_delta
                state.schedule.append((departure_time, arrival_time))
                return state

        return None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _aircraft_in_range(state: _AircraftState, distance_km: int) -> bool:
        """Return True if this aircraft can fly the given distance."""

        class _Wrapper:
            pass

        wrapper = _Wrapper()
        wrapper.manufacturer = state.manufacturer
        wrapper.model = state.model
        return aircraft_can_serve_route(wrapper, distance_km)

    @staticmethod
    def _can_operate(
        state: _AircraftState,
        *,
        origin_id: int,
        departure_time: datetime,
        turnaround_delta: timedelta,
    ) -> bool:
        """Return True if the aircraft can operate this flight."""
        # Case 1: never flown yet
        if state.current_location_id is None and state.available_at is None:
            return True

        # Case 2: must be at departure airport
        if state.current_location_id != origin_id:
            return False

        # Case 3: must have completed turnaround
        if state.available_at is not None and departure_time < state.available_at:
            return False

        return True

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        """Return a summary of aircraft utilization."""
        return {
            "aircraft_count": len(self._state),
            "total_flights_assigned": sum(
                len(s.schedule) for s in self._state.values()
            ),
            "per_aircraft": [
                {
                    "id": s.aircraft_id,
                    "registration": s.registration,
                    "manufacturer": s.manufacturer,
                    "flights": len(s.schedule),
                }
                for s in self._state.values()
            ],
        }