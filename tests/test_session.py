from app.models import UserRole
from app.services import (
    AuthenticationResult,
    SessionManager,
)


def create_admin_result():
    return AuthenticationResult(
        user_id=1,
        email="admin@airline.local",
        role=UserRole.ADMIN,
    )


def create_staff_result():
    return AuthenticationResult(
        user_id=2,
        email="staff1@airline.local",
        role=UserRole.STAFF,
    )


def create_passenger_result():
    return AuthenticationResult(
        user_id=3,
        email="passenger@airline.local",
        role=UserRole.PASSENGER,
    )


def test_new_session_is_not_authenticated():

    session = SessionManager()

    assert session.is_authenticated is False
    assert session.current_user is None


def test_admin_login():

    session = SessionManager()

    result = create_admin_result()

    session.login(result)

    assert session.is_authenticated is True
    assert session.current_user == result
    assert session.is_admin() is True


def test_staff_login():

    session = SessionManager()

    result = create_staff_result()

    session.login(result)

    assert session.is_authenticated is True
    assert session.current_user == result
    assert session.is_staff() is True


def test_passenger_login():

    session = SessionManager()

    result = create_passenger_result()

    session.login(result)

    assert session.is_authenticated is True
    assert session.current_user == result
    assert session.is_passenger() is True


def test_role_restriction():

    session = SessionManager()

    session.login(
        create_admin_result()
    )

    session.require_role(
        UserRole.ADMIN
    )

    try:

        session.require_role(
            UserRole.STAFF
        )

        assert False, (
            "STAFF role should be rejected."
        )

    except PermissionError:

        pass


def test_logout():

    session = SessionManager()

    session.login(
        create_admin_result()
    )

    assert session.is_authenticated is True

    session.logout()

    assert session.is_authenticated is False
    assert session.current_user is None


def test_unauthenticated_role_check():

    session = SessionManager()

    assert session.is_admin() is False
    assert session.is_staff() is False
    assert session.is_passenger() is False