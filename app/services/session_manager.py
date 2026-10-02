from app.models import UserRole
from app.services.auth_result import AuthenticationResult


class SessionManager:
    """
    Stores the currently authenticated user for the
    lifetime of the desktop application.
    """

    def __init__(self):
        self._current_user: AuthenticationResult | None = None

    @property
    def current_user(self) -> AuthenticationResult | None:
        """
        Return the currently authenticated user.
        """

        return self._current_user

    @property
    def is_authenticated(self) -> bool:
        """
        Return True when a user is logged in.
        """

        return self._current_user is not None

    def login(self, result: AuthenticationResult):
        """
        Store a successful authentication result.
        """

        self._current_user = result

    def logout(self):
        """
        Clear the current user session.
        """

        self._current_user = None

    def require_authentication(self):
        """
        Raise an error if no user is logged in.
        """

        if not self.is_authenticated:
            raise PermissionError(
                "Authentication is required."
            )

    def has_role(self, role: UserRole) -> bool:
        """
        Check whether the current user has a specific role.
        """

        if not self.is_authenticated:
            return False

        return self._current_user.role == role

    def require_role(self, role: UserRole):
        """
        Require the current user to have a specific role.
        """

        self.require_authentication()

        if not self.has_role(role):
            raise PermissionError(
                "You do not have permission to perform this action."
            )

    def is_admin(self) -> bool:
        """
        Check whether the current user is an administrator.
        """

        return self.has_role(
            UserRole.ADMIN
        )

    def is_staff(self) -> bool:
        """
        Check whether the current user is staff.
        """

        return self.has_role(
            UserRole.STAFF
        )

    def is_passenger(self) -> bool:
        """
        Check whether the current user is a passenger.
        """

        return self.has_role(
            UserRole.PASSENGER
        )