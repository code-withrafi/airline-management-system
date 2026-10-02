from app.repositories.dashboard_repository import DashboardRepository
from app.repositories.user_repository import UserRepository
from app.repositories.airport_repository import AirportRepository
from app.repositories.aircraft_repository import AircraftRepository
from app.repositories.seat_repository import SeatRepository
from app.repositories.flight_repository import FlightRepository
from app.repositories.route_repository import RouteRepository
from app.repositories.staff_repository import StaffRepository
from app.repositories.flight_staff_repository import FlightStaffRepository
from app.repositories.passenger_repository import PassengerRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.checkin_repository import CheckInRepository
from app.repositories.baggage_repository import BaggageRepository
from app.repositories.boarding_pass_repository import BoardingPassRepository


__all__ = [
    "DashboardRepository",
    "UserRepository",
    "AirportRepository",
    "AircraftRepository",
    "SeatRepository",
    "FlightRepository",
    "RouteRepository",
    "StaffRepository",
    "FlightStaffRepository",
    "PassengerRepository",
    "BookingRepository",
    "CheckInRepository",
    "BaggageRepository",
    "BoardingPassRepository",

]