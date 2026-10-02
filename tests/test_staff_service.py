import pytest

from app.config.database import SessionLocal
from app.models import Staff, User, UserRole
from app.services.staff_service import StaffService


@pytest.fixture
def database_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def staff_factory(database_session):
    """
    Create a Staff row with a specific position.
    Cleans up at the end of the test.
    """
    import uuid
    created_ids = []

    def _create(position: str):
        tag = uuid.uuid4().hex[:6].upper()

        user = User(
            email=f"staff-{tag}@test.local",
            password_hash="x",
            role=UserRole.STAFF,
        )
        database_session.add(user)
        database_session.flush()

        staff = Staff(
            user_id=user.id,
            employee_id=f"EMP{tag}",
            first_name="Test",
            last_name="Staff",
            phone="000000",
            position=position,
        )
        database_session.add(staff)
        database_session.commit()

        created_ids.append((staff.id, user.id))
        return staff

    yield _create

    for staff_id, user_id in created_ids:
        s = database_session.get(Staff, staff_id)
        if s is not None:
            database_session.delete(s)
        u = database_session.get(User, user_id)
        if u is not None:
            database_session.delete(u)

    try:
        database_session.commit()
    except Exception:
        database_session.rollback()


# ======================================================================


def test_is_checkin_officer_true(database_session, staff_factory):
    staff = staff_factory("Check-in Officer")
    service = StaffService(database_session)
    assert service.is_checkin_officer(staff.user_id) is True


def test_is_checkin_officer_false_for_ground_staff(database_session, staff_factory):
    staff = staff_factory("Ground Staff")
    service = StaffService(database_session)
    assert service.is_checkin_officer(staff.user_id) is False


def test_is_checkin_officer_false_for_supervisor(database_session, staff_factory):
    staff = staff_factory("Supervisor")
    service = StaffService(database_session)
    assert service.is_checkin_officer(staff.user_id) is False


def test_is_checkin_officer_case_insensitive(database_session, staff_factory):
    staff = staff_factory("CHECK-IN OFFICER")
    service = StaffService(database_session)
    assert service.is_checkin_officer(staff.user_id) is True


def test_is_checkin_officer_missing_staff(database_session):
    service = StaffService(database_session)
    assert service.is_checkin_officer(999999) is False
