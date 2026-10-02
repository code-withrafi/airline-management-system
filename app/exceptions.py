class AuthenticationError(Exception):
    """Raised when authentication fails."""


class AuthorizationError(Exception):
    """Raised when a user is not authorized to perform an action."""


class ValidationError(Exception):
    """Raised when application data fails validation."""


class ResourceNotFoundError(Exception):
    """Raised when a requested database resource does not exist."""


class ResourceConflictError(Exception):
    """Raised when an operation conflicts with existing data."""


class DatabaseOperationError(Exception):
    """Raised when a database operation cannot be completed."""
