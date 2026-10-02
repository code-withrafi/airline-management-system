from app.models.user import User, UserRole
from app.models.passenger import Passenger
from app.models.staff import Staff
from app.models.airport import Airport
from app.models.route import Route
from app.models.aircraft import Aircraft, AircraftStatus
from app.models.seat import Seat, SeatClass, SeatPosition
from app.models.flight import Flight, FlightStatus
from app.models.flight_staff import (
    FlightStaff,
    AssignmentRole
)
from app.models.booking import (
    Booking,
    BookingStatus
)
from app.models.checkin import (
    CheckIn,
    CheckInMethod,
    CheckInStatus
)
from app.models.baggage import (
    Baggage,
    BaggageStatus
)
from app.models.boarding_pass import BoardingPass