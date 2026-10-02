from datetime import date as date_type, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.models.flight import FlightStatus
from app.repositories.airport_repository import AirportRepository
from app.repositories.flight_repository import FlightRepository
from app.repositories.route_repository import RouteRepository
from app.services.pricing import calculate_fare
from api.deps import get_db
from api.schemas.flight import (
    AircraftSummary,
    FlightResponse,
    FlightSearchResponse,
)

router = APIRouter()


def _to_flight_response(flight) -> FlightResponse:
    aircraft = flight.aircraft

    aircraft_summary = (
        AircraftSummary(
            id=aircraft.id,
            registration_number=aircraft.registration_number,
            manufacturer=aircraft.manufacturer,
            model=aircraft.model,
            seat_capacity=aircraft.seat_capacity,
            status=getattr(aircraft.status, "value", str(aircraft.status)),
        )
        if aircraft is not None
        else None
    )

    return FlightResponse(
        id=flight.id,
        flight_number=flight.flight_number,
        departure_time=flight.departure_time,
        arrival_time=flight.arrival_time,
        base_fare=flight.base_fare,
        economy_fare=calculate_fare(flight.base_fare, "ECONOMY"),
        business_fare=calculate_fare(flight.base_fare, "BUSINESS"),
        status=flight.status.value,
        boarding_gate=flight.boarding_gate,
        route=flight.route,
        aircraft=aircraft_summary,
    )


@router.get("/airports/search")
def search_airports(
    q: str = Query("", max_length=100),
    db: Session = Depends(get_db),
):
    """
    Public airport search.

    Searches by:
    - city
    - airport name
    - country
    - IATA code
    - ICAO code
    """

    search_text = q.strip()

    airport_repo = AirportRepository(db)

    airports = airport_repo.search(search_text)

    return [
        {
            "id": airport.id,
            "iata_code": airport.iata_code,
            "icao_code": airport.icao_code,
            "name": airport.name,
            "city": airport.city,
            "country": airport.country,
        }
        for airport in airports
        if airport.is_active
    ][:10]


@router.get("/search", response_model=FlightSearchResponse)
def search_flights(
    origin: str = Query(
        ...,
        min_length=3,
        max_length=3,
        description="Origin IATA code",
    ),
    destination: str = Query(
        ...,
        min_length=3,
        max_length=3,
        description="Destination IATA code",
    ),
    date: date_type = Query(
        ...,
        description="Departure date (YYYY-MM-DD)",
    ),
    db: Session = Depends(get_db),
):
    """
    Public flight search — no authentication required.
    """

    origin_code = origin.strip().upper()
    destination_code = destination.strip().upper()

    if origin_code == destination_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Origin and destination must be different.",
        )

    airport_repo = AirportRepository(db)
    route_repo = RouteRepository(db)
    flight_repo = FlightRepository(db)

    origin_airport = airport_repo.get_by_iata_code(origin_code)

    if origin_airport is None or not origin_airport.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Origin airport '{origin_code}' not found or inactive.",
        )

    destination_airport = airport_repo.get_by_iata_code(destination_code)

    if destination_airport is None or not destination_airport.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Destination airport '{destination_code}' not found or inactive.",
        )

    routes = route_repo.get_all_by_airports(
        origin_airport.id,
        destination_airport.id,
    )

    route_ids = {route.id for route in routes}

    if not route_ids:
        return FlightSearchResponse(
            count=0,
            results=[],
        )

    day_start = datetime.combine(date, time.min)
    day_end = datetime.combine(date, time.max)

    flights = flight_repo.search(
        status=FlightStatus.SCHEDULED,
        start_date=day_start,
        end_date=day_end,
    )

    matching = [
        flight
        for flight in flights
        if flight.route_id in route_ids
    ]

    return FlightSearchResponse(
        count=len(matching),
        results=[
            _to_flight_response(flight)
            for flight in matching
        ],
    )


@router.get("/{flight_id}", response_model=FlightResponse)
def get_flight(
    flight_id: int,
    db: Session = Depends(get_db),
):
    """Public flight detail — no authentication required."""

    flight_repo = FlightRepository(db)

    flight = flight_repo.get_by_id(flight_id)

    if flight is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found.",
        )

    return _to_flight_response(flight)