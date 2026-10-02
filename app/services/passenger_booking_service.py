from datetime import date, datetime, time

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import (
    Booking,
    BookingStatus,
    FlightStatus,
    Passenger,
)

from app.repositories import (
    AirportRepository,
    BookingRepository,
    FlightRepository,
    PassengerRepository,
    RouteRepository,
    SeatRepository,
)

from app.services.booking_availability_service import (
    BookingAvailabilityService,
)
from app.services.booking_service import BookingService
from app.services.payment_service import (
    PaymentResult,
    PaymentService,
)
from app.services.exceptions import (
    AuthorizationError,
    DatabaseOperationError,
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)


class PassengerBookingService:
    """
    Passenger-facing orchestration layer.

    Wraps BookingService, PaymentService, and several repositories
    with:

    - user_id -> passenger resolution
    - ownership checks (a passenger can only act on their own bookings)
    - passenger-safe flight reads (bypassing FlightService's admin guard)
    - a seat-map builder for the GUI
    """

    BOOKABLE_STATUSES = (
        FlightStatus.SCHEDULED,
        FlightStatus.DELAYED,
        FlightStatus.BOARDING,
    )

    SEARCHABLE_STATUSES = (
        FlightStatus.SCHEDULED,
        FlightStatus.DELAYED,
        FlightStatus.BOARDING,
    )

    def __init__(
        self,
        session: Session,
    ):

        self.session = session

        self.booking_service = (
            BookingService(
                session
            )
        )

        self.payment_service = (
            PaymentService()
        )

        self.availability_service = (
            BookingAvailabilityService(
                session
            )
        )

        self.passenger_repository = (
            PassengerRepository(
                session
            )
        )

        self.booking_repository = (
            BookingRepository(
                session
            )
        )

        self.flight_repository = (
            FlightRepository(
                session
            )
        )

        self.seat_repository = (
            SeatRepository(
                session
            )
        )

        self.route_repository = (
            RouteRepository(
                session
            )
        )

        self.airport_repository = (
            AirportRepository(
                session
            )
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_id(
        value: int,
        name: str,
    ) -> None:

        if isinstance(value, bool):

            raise ValidationError(
                f"{name} must be a positive integer."
            )

        if not isinstance(value, int):

            raise ValidationError(
                f"{name} must be a positive integer."
            )

        if value <= 0:

            raise ValidationError(
                f"{name} must be a positive integer."
            )

    def _resolve_passenger(
        self,
        user_id: int,
    ) -> Passenger:
        """
        Resolve a User id to the linked Passenger profile.
        """

        self._validate_id(
            user_id,
            "User ID"
        )

        try:

            passenger = (
                self.passenger_repository
                .get_by_user_id(
                    user_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to resolve passenger profile."
            ) from exc

        if passenger is None:

            raise ResourceNotFoundError(
                "Passenger profile was not found."
            )

        return passenger

    @staticmethod
    def _assert_owns_booking(
        passenger_id: int,
        booking: Booking,
    ) -> None:

        if booking.passenger_id != passenger_id:

            raise AuthorizationError(
                "This booking does not belong to you."
            )

    @staticmethod
    def _assert_flight_bookable(
        flight,
    ) -> None:

        if flight.status not in PassengerBookingService.BOOKABLE_STATUSES:

            raise ResourceConflictError(
                "This flight is not open for booking."
            )

        if flight.departure_time <= datetime.utcnow():

            raise ResourceConflictError(
                "This flight has already departed."
            )

    def _load_booking_for_user(
        self,
        user_id: int,
        booking_id: int,
    ) -> tuple[Passenger, Booking]:
        """
        Load a booking and verify ownership in one call.
        """

        self._validate_id(
            booking_id,
            "Booking ID"
        )

        passenger = self._resolve_passenger(
            user_id
        )

        try:

            booking = (
                self.booking_repository
                .get_by_id(
                    booking_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve booking."
            ) from exc

        if booking is None:

            raise ResourceNotFoundError(
                "Booking was not found."
            )

        self._assert_owns_booking(
            passenger.id,
            booking,
        )

        return passenger, booking

    # ------------------------------------------------------------------
    # Flight search
    # ------------------------------------------------------------------

    def list_airports_for_search(
        self,
    ) -> list:
        """
        Return all airports for populating search combo boxes.
        """

        try:

            return (
                self.airport_repository
                .get_all()
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to load airports."
            ) from exc

    def search_flights(
        self,
        *,
        origin_code: str,
        destination_code: str,
        on_date: date,
    ) -> list:
        """
        Search flights between two airports on a given calendar date.

        Returns an empty list if no route or no matching flight exists.
        Raises ValidationError for bad input.
        """

        if not isinstance(origin_code, str) or not origin_code.strip():

            raise ValidationError(
                "Origin airport code is required."
            )

        if not isinstance(destination_code, str) or not destination_code.strip():

            raise ValidationError(
                "Destination airport code is required."
            )

        if not isinstance(on_date, date):

            raise ValidationError(
                "Search date must be a valid date."
            )

        origin_code = origin_code.strip().upper()
        destination_code = destination_code.strip().upper()

        if origin_code == destination_code:

            raise ValidationError(
                "Origin and destination must differ."
            )

        try:

            origin = (
                self.airport_repository
                .get_by_iata_code(
                    origin_code
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to look up origin airport."
            ) from exc

        if origin is None:

            raise ResourceNotFoundError(
                f"Unknown origin airport code: {origin_code}."
            )

        try:

            destination = (
                self.airport_repository
                .get_by_iata_code(
                    destination_code
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to look up destination airport."
            ) from exc

        if destination is None:

            raise ResourceNotFoundError(
                f"Unknown destination airport code: {destination_code}."
            )

        try:

            routes = (
                self.route_repository
                .get_all_by_airports(
                    origin.id,
                    destination.id,
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to look up routes."
            ) from exc

        if not routes:

            return []

        route_ids = [
            route.id
            for route in routes
        ]

        start_of_day = datetime.combine(
            on_date,
            time.min,
        )

        end_of_day = datetime.combine(
            on_date,
            time.max,
        )

        try:

            flights: list = []

            for route_id in route_ids:

                flights.extend(
                    self.flight_repository
                    .search(
                        route_id=route_id,
                        status=list(
                            self.SEARCHABLE_STATUSES
                        ),
                        start_date=start_of_day,
                        end_date=end_of_day,
                    )
                )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to search flights."
            ) from exc

        flights.sort(
            key=lambda f: f.departure_time
        )

        return flights

    # ------------------------------------------------------------------
    # Seat map
    # ------------------------------------------------------------------

    def get_seat_map(
        self,
        flight_id: int,
    ) -> dict:
        """
        Build a seat-map payload for the GUI.

        Shape:
            {
                "flight":     <Flight>,
                "aircraft_id": <int>,
                "rows":       [1, 2, 3, ...],
                "columns":    ["A", "B", ...],
                "seats": [
                    {
                        "id": <int>,
                        "number": "1A",
                        "row": 1,
                        "col": "A",
                        "seat_class": "ECONOMY",
                        "position": "WINDOW",
                        "available": True,
                        "fare": <Decimal>,
                    },
                    ...
                ],
            }
        """

        self._validate_id(
            flight_id,
            "Flight ID"
        )

        try:

            flight = (
                self.flight_repository
                .get_by_id(
                    flight_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve flight."
            ) from exc

        if flight is None:

            raise ResourceNotFoundError(
                "Flight was not found."
            )

        try:

            seats = (
                self.seat_repository
                .get_layout(
                    flight.aircraft_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve seat layout."
            ) from exc

        try:

            existing_bookings = (
                self.booking_repository
                .get_by_flight(
                    flight_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve flight bookings."
            ) from exc

        # With the partial unique index in place, only ACTIVE
        # bookings block a seat. CANCELLED / REFUNDED bookings
        # free the seat for re-booking.
        booked_seat_ids = {
            booking.seat_id
            for booking in existing_bookings
            if booking.status not in (
                BookingStatus.CANCELLED,
                BookingStatus.REFUNDED,
            )
        }

        rows = sorted({
            seat.row_number
            for seat in seats
        })

        columns = sorted({
            self._column_letter(
                seat.seat_number
            )
            for seat in seats
        })

        seat_payload = [
            {
                "id": seat.id,
                "number": seat.seat_number,
                "row": seat.row_number,
                "col": self._column_letter(
                    seat.seat_number
                ),
                "seat_class": seat.seat_class.value,
                "position": seat.position.value,
                "available": seat.id not in booked_seat_ids,
                "fare": flight.base_fare,
            }
            for seat in seats
        ]

        return {
            "flight": flight,
            "aircraft_id": flight.aircraft_id,
            "rows": rows,
            "columns": columns,
            "seats": seat_payload,
        }

    @staticmethod
    def _column_letter(
        seat_number: str,
    ) -> str:
        """
        Extract the column letter(s) from a seat number like '12A'.
        """

        letters = "".join(
            ch
            for ch in seat_number
            if ch.isalpha()
        )

        return letters.upper() or "?"

    # ------------------------------------------------------------------
    # Booking lifecycle
    # ------------------------------------------------------------------

    def create_booking(
        self,
        *,
        user_id: int,
        flight_id: int,
        seat_id: int,
    ) -> Booking:
        """
        Create an UNPAID booking for the current passenger.

        Delegates to BookingService.create_booking, which:
        - validates passenger / flight / seat exist
        - validates seat availability
        - generates the booking reference
        - commits the transaction
        """

        passenger = self._resolve_passenger(
            user_id
        )

        self._validate_id(
            flight_id,
            "Flight ID"
        )

        self._validate_id(
            seat_id,
            "Seat ID"
        )

        try:

            flight = (
                self.flight_repository
                .get_by_id(
                    flight_id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve flight."
            ) from exc

        if flight is None:

            raise ResourceNotFoundError(
                "Flight was not found."
            )

        self._assert_flight_bookable(
            flight
        )

        return (
            self.booking_service
            .create_booking(
                passenger_id=passenger.id,
                flight_id=flight_id,
                seat_id=seat_id,
                fare_amount=flight.base_fare,
            )
        )

    def pay_for_booking(
        self,
        *,
        user_id: int,
        booking_id: int,
        card_number: str,
        expiry: str,
        cvv: str,
        cardholder_name: str,
    ) -> tuple[Booking, PaymentResult]:
        """
        Process a mock payment for an UNPAID booking.

        Returns (booking, payment_result).

        On payment failure, the booking remains UNPAID and the
        result carries the failure reason.
        """

        passenger, booking = self._load_booking_for_user(
            user_id,
            booking_id,
        )

        if booking.status != BookingStatus.UNPAID:

            raise ResourceConflictError(
                "This booking is not awaiting payment."
            )

        result = (
            self.payment_service
            .process_payment(
                booking_id=booking.id,
                amount=float(booking.fare_amount),
                card_number=card_number,
                expiry=expiry,
                cvv=cvv,
                cardholder_name=cardholder_name,
            )
        )

        if not result.success:

            return booking, result

        try:

            booking = (
                self.booking_service
                .mark_as_paid(
                    booking.id
                )
            )

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            raise

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to confirm booking after payment."
            ) from exc

        return booking, result

    def cancel_unpaid_booking(
        self,
        *,
        user_id: int,
        booking_id: int,
    ) -> Booking:
        """
        Cancel an UNPAID booking. Paid bookings must request a refund.
        """

        passenger, booking = self._load_booking_for_user(
            user_id,
            booking_id,
        )

        if booking.status != BookingStatus.UNPAID:

            raise ResourceConflictError(
                "Only unpaid bookings can be cancelled directly. "
                "Request a refund instead."
            )

        try:

            return (
                self.booking_service
                .cancel_booking(
                    booking.id
                )
            )

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            raise

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to cancel booking."
            ) from exc

    def request_refund(
        self,
        *,
        user_id: int,
        booking_id: int,
    ) -> Booking:
        """
        Request a refund for a CONFIRMED booking.
        """

        passenger, booking = self._load_booking_for_user(
            user_id,
            booking_id,
        )

        try:

            return (
                self.booking_service
                .request_refund(
                    booking.id
                )
            )

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            raise

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to request refund."
            ) from exc

    def preview_refund(
        self,
        *,
        user_id: int,
        booking_id: int,
    ) -> dict:
        """
        Return a refund preview for a CONFIRMED booking.
        """

        passenger, booking = self._load_booking_for_user(
            user_id,
            booking_id,
        )

        try:

            return (
                self.booking_service
                .preview_refund(
                    booking.id
                )
            )

        except (
            ResourceNotFoundError,
            ResourceConflictError,
            ValidationError,
        ):

            raise

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to preview refund."
            ) from exc

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_my_bookings(
        self,
        *,
        user_id: int,
    ) -> list[Booking]:
        """
        Return all bookings for the current passenger,
        newest first.
        """

        passenger = self._resolve_passenger(
            user_id
        )

        try:

            return (
                self.booking_repository
                .get_by_passenger(
                    passenger.id
                )
            )

        except SQLAlchemyError as exc:

            raise DatabaseOperationError(
                "Unable to retrieve your bookings."
            ) from exc

    def get_booking_details(
        self,
        *,
        user_id: int,
        booking_id: int,
    ) -> dict:
        """
        Return a rich detail dict for one booking.
        """

        passenger, booking = self._load_booking_for_user(
            user_id,
            booking_id,
        )

        return {
            "booking": booking,
            "flight": booking.flight,
            "route": booking.flight.route,
            "aircraft": booking.flight.aircraft,
            "seat": booking.seat,
            "passenger": passenger,
            "boarding_pass": booking.boarding_pass,
            "checkin": booking.checkin,
        }
