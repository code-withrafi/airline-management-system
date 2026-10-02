# api/schemas/flight.py
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AirportSummary(BaseModel):
    """Public airport info embedded in route responses."""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    iata_code: str
    icao_code: str
    name: str
    city: str
    country: str
    timezone: str


class RouteSummary(BaseModel):
    """Public route info embedded in flight responses."""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    distance_km: int
    estimated_duration_minutes: int
    origin_airport: AirportSummary
    destination_airport: AirportSummary


class AircraftSummary(BaseModel):
    """Public aircraft info embedded in flight responses."""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    registration_number: str
    manufacturer: str
    model: str
    seat_capacity: int
    status: str          # converted from AircraftStatus enum in the router


class FlightResponse(BaseModel):
    """Full public flight shape returned to passengers."""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    flight_number: str
    departure_time: datetime
    arrival_time: datetime
    base_fare: Decimal                                # economy fare (legacy field)

    economy_fare: Decimal                             # ← NEW: computed
    business_fare: Decimal                            # ← NEW: computed

    status: str
    boarding_gate: Optional[str] = None
    route: RouteSummary
    aircraft: AircraftSummary


class FlightSearchResponse(BaseModel):
    """Envelope for search results — pagination-ready."""
    count: int
    results: list[FlightResponse]