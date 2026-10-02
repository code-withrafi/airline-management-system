from app.config.database import SessionLocal
from app.config.seed_database import STAFF_PASSWORD
from app.models import UserRole
from app.services.auth_service import AuthService
from app.services.exceptions import AuthenticationError


def test_admin_login():

    session = SessionLocal()

    try:

        auth_service = AuthService(session)

        result = auth_service.authenticate(
            "admin@airline.local",
            "Admin@12345",
        )

        assert result.email == "admin@airline.local"
        assert result.role == UserRole.ADMIN
        assert result.user_id > 0

    finally:

        session.close()


def test_staff_login():

    session = SessionLocal()

    try:

        auth_service = AuthService(session)

        result = auth_service.authenticate(
            "staff1@airline.local",
            STAFF_PASSWORD,
        )

        assert result.email == "staff1@airline.local"
        assert result.role == UserRole.STAFF
        assert result.user_id > 0

    finally:

        session.close()


def test_wrong_password():

    session = SessionLocal()

    try:

        auth_service = AuthService(session)

        try:

            auth_service.authenticate(
                "admin@airline.local",
                "WrongPassword",
            )

            assert False, (
                "Authentication should have failed."
            )

        except AuthenticationError as error:

            assert str(error) == (
                "Invalid email or password."
            )

    finally:

        session.close()


def test_unknown_email():

    session = SessionLocal()

    try:

        auth_service = AuthService(session)

        try:

            auth_service.authenticate(
                "unknown@airline.local",
                "SomePassword",
            )

            assert False, (
                "Authentication should have failed."
            )

        except AuthenticationError as error:

            assert str(error) == (
                "Invalid email or password."
            )

    finally:

        session.close()


def test_empty_email():

    session = SessionLocal()

    try:

        auth_service = AuthService(session)

        try:

            auth_service.authenticate(
                "",
                "SomePassword",
            )

            assert False, (
                "Authentication should have failed."
            )

        except AuthenticationError as error:

            assert str(error) == "Email is required."

    finally:

        session.close()


def test_empty_password():

    session = SessionLocal()

    try:

        auth_service = AuthService(session)

        try:

            auth_service.authenticate(
                "admin@airline.local",
                "",
            )

            assert False, (
                "Authentication should have failed."
            )

        except AuthenticationError as error:

            assert str(error) == "Password is required."

    finally:

        session.close()