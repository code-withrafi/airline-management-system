# app/services/flight_completion_service.py
"""
Service that transitions expired flights to COMPLETED.

A flight is "expired" when its arrival_time has passed by a grace
period. The service is called periodically by a background sweeper
and can also be invoked on-demand by the admin UI.
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.flight import Flight, FlightStatus


# Flights are marked complete only after this grace period past arrival.
# Gives time for late landings, buffer, and to avoid marking mid-flight.
COMPLETION_GRACE_MINUTES = 30

# Statuses that are eligible to become COMPLETED
COMPLETABLE_STATUSES = (
    FlightStatus.SCHEDULED,
    FlightStatus.BOARDING,
    FlightStatus.DEPARTED,
    FlightStatus.ARRIVED,
    FlightStatus.DELAYED,
)


class FlightCompletionService:
    """Marks flights as COMPLETED after their arrival time has passed."""

    def __init__(self, session: Session):
        self.session = session

    def complete_expired_flights(self) -> int:
        """
        Transition all eligible flights to COMPLETED.

        Returns the number of flights that were changed.
        """
        cutoff = datetime.utcnow() - timedelta(minutes=COMPLETION_GRACE_MINUTES)

        expired = (
            self.session.query(Flight)
            .filter(
                Flight.arrival_time <= cutoff,
                Flight.status.in_(COMPLETABLE_STATUSES),
            )
            .all()
        )

        if not expired:
            return 0

        for flight in expired:
            flight.status = FlightStatus.COMPLETED

        self.session.commit()
        return len(expired)