from sqlalchemy.orm import Session

from app.models import User
from app.repositories.user_repository import UserRepository
from app.services.auth_result import AuthenticationResult
from app.services.exceptions import AuthenticationError
from app.utils.security import verify_password


class AuthService:
    """
    Handles application authentication logic.
    """

    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> AuthenticationResult:
        """
        Authenticate a user using email and password.

        Raises:
            AuthenticationError:
                If credentials are invalid or account is inactive.
        """

        normalized_email = email.lower().strip()

        if not normalized_email:
            raise AuthenticationError(
                "Email is required."
            )

        if not password:
            raise AuthenticationError(
                "Password is required."
            )

        user = self.user_repository.get_by_email(
            normalized_email
        )

        if user is None:
            raise AuthenticationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise AuthenticationError(
                "This account is inactive."
            )

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise AuthenticationError(
                "Invalid email or password."
            )

        return AuthenticationResult(
            user_id=user.id,
            email=user.email,
            role=user.role,
        )