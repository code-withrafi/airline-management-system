from sqlalchemy.orm import Session

from app.models import Flight, UserRole
from app.repositories.dashboard_repository import DashboardRepository
from app.services.application import application_context


class DashboardService:
    """
    Service layer for administrator dashboard operations.

    The service is responsible for authorization and coordinating
    dashboard-related data retrieval.
    """

    def __init__(self, session: Session):
        self.session = session
        self.repository = DashboardRepository(session)

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------

    def _require_admin(self) -> None:
        """
        Ensure that the currently authenticated user is an administrator.
        """

        application_context.session.require_role(UserRole.ADMIN)

    # ------------------------------------------------------------------
    # Dashboard statistics
    # ------------------------------------------------------------------

    def get_dashboard_statistics(self) -> dict[str, int]:
        """
        Return all administrator dashboard statistics.
        """

        self._require_admin()

        return self.repository.get_dashboard_statistics()

    # ------------------------------------------------------------------
    # Recent flights
    # ------------------------------------------------------------------

    def get_recent_flights(self, limit: int = 10) -> list[Flight]:
        """
        Return recent/upcoming flights for the administrator dashboard.
        """

        self._require_admin()

        if limit <= 0:
            return []

        return self.repository.get_recent_flights(limit)