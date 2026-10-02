from dataclasses import dataclass

from app.models import UserRole


@dataclass
class AuthenticationResult:
    """
    Represents the result of a successful authentication.
    """

    user_id: int
    email: str
    role: UserRole