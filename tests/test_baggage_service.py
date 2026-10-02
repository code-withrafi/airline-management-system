from decimal import Decimal

import pytest

from app.config.database import SessionLocal
from app.models import (
    Baggage,
    BookingStatus,
)
from app.services.baggage_service import BaggageService
from app.services.checkin_service import CheckInService
from app.services.exceptions import (
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
    checkin = service.check_in_booking(booking_id=booking.id)
    return booking, checkin


def test_add_baggage_succeeds(database_session, checked_in_booking):
    _, checkin = checked_in_booking
    service = BaggageService(database_session)
    bag = service.add_baggage(checkin_id=checkin.id, weight_kg=23.5)
    assert bag.id is not None
    assert bag.weight_kg == Decimal("23.50")


def test_add_baggage_generates_unique_tag(database_session, checked_in_booking):
    _, checkin = checked_in_booking
    service = BaggageService(database_session)
    b1 = service.add_baggage(checkin_id=checkin.id, weight_kg=10)
    b2 = service.add_baggage(checkin_id=checkin.id, weight_kg=15)
    assert b1.bag_tag != b2.bag_tag


def test_add_baggage_rejects_zero_weight(database_session, checked_in_booking):
    _, checkin = checked_in_booking
    service = BaggageService(database_session)
    with pytest.raises(ValidationError):
        service.add_baggage(checkin_id=checkin.id, weight_kg=0)


def test_add_baggage_rejects_negative_weight(database_session, checked_in_booking):
    _, checkin = checked_in_booking
    service = BaggageService(database_session)
    with pytest.raises(ValidationError):
        service.add_baggage(checkin_id=checkin.id, weight_kg=-5)


def test_add_baggage_rejects_over_max(database_session, checked_in_booking):
    _, checkin = checked_in_booking
    service = BaggageService(database_session)
    with pytest.raises(ValidationError):
        service.add_baggage(checkin_id=checkin.id, weight_kg=100)


def test_add_baggage_missing_checkin_rejected(database_session):
    service = BaggageService(database_session)
    with pytest.raises(ResourceNotFoundError):
        service.add_baggage(checkin_id=999999, weight_kg=10)


def test_get_baggage_for_checkin(database_session, checked_in_booking):
    _, checkin = checked_in_booking
    service = BaggageService(database_session)
    service.add_baggage(checkin_id=checkin.id, weight_kg=8)
    service.add_baggage(checkin_id=checkin.id, weight_kg=12)
    bags = service.get_baggage_for_checkin(checkin.id)
    assert len(bags) == 2


def test_remove_baggage(database_session, checked_in_booking):
    _, checkin = checked_in_booking
    service = BaggageService(database_session)
    bag = service.add_baggage(checkin_id=checkin.id, weight_kg=8)
    service.remove_baggage(bag.id)
    assert database_session.get(Baggage, bag.id) is None
