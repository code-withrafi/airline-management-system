import pytest

from app.config.database import SessionLocal
from app.models import (
    BoardingPass,
    BookingStatus,
)
from app.services.boarding_pass_service import BoardingPassService
from app.services.checkin_service import CheckInService
from app.services.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
    ValidationError,
)

from tests.test_checkin_service import (
    database_session,
    booking_factory,
)


@pytest.fixture
def checked_in_booking(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = CheckInService(database_session)
    service.check_in_booking(booking_id=booking.id)
    database_session.refresh(booking)
    return booking


# ======================================================================


def test_issue_pass_for_checked_in_booking(database_session, checked_in_booking):
    service = BoardingPassService(database_session)
    bp = service.issue_boarding_pass(
        booking_id=checked_in_booking.id,
        boarding_gate="A1",
        boarding_group="A",
    )
    assert bp.id is not None
    assert bp.boarding_pass_number.startswith("BP")
    assert bp.boarding_gate == "A1"


def test_issue_pass_rejected_for_confirmed_booking(database_session, booking_factory):
    booking = booking_factory(status=BookingStatus.CONFIRMED)
    service = BoardingPassService(database_session)
    with pytest.raises(ResourceConflictError):
        service.issue_boarding_pass(
            booking_id=booking.id,
            boarding_gate="A1",
            boarding_group="A",
        )


def test_issue_pass_rejected_for_duplicate(database_session, checked_in_booking):
    service = BoardingPassService(database_session)
    service.issue_boarding_pass(
        booking_id=checked_in_booking.id,
        boarding_gate="A1",
        boarding_group="A",
    )
    with pytest.raises(ResourceConflictError):
        service.issue_boarding_pass(
            booking_id=checked_in_booking.id,
            boarding_gate="A1",
            boarding_group="A",
        )


def test_issue_pass_rejects_empty_gate(database_session, checked_in_booking):
    service = BoardingPassService(database_session)
    with pytest.raises(ValidationError):
        service.issue_boarding_pass(
            booking_id=checked_in_booking.id,
            boarding_gate="",
            boarding_group="A",
        )


def test_issue_pass_rejects_empty_group(database_session, checked_in_booking):
    service = BoardingPassService(database_session)
    with pytest.raises(ValidationError):
        service.issue_boarding_pass(
            booking_id=checked_in_booking.id,
            boarding_gate="A1",
            boarding_group="",
        )


def test_get_pass_for_booking_missing_raises(database_session, checked_in_booking):
    service = BoardingPassService(database_session)
    with pytest.raises(ResourceNotFoundError):
        service.get_pass_for_booking(checked_in_booking.id)
