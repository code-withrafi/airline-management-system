# app/ml/no_show/service.py
"""
No-show prediction service.

Loads the trained model once, then serves predictions for bookings
and flights on demand.
"""

from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.ml.features import (
    no_show_features_from_booking,
    no_show_features_row,
)


MODEL_PATH = Path("app/ml/models/no_show_v1.pkl")

# Decision threshold for binary classification.
# Lower = higher recall (catch more no-shows) at the cost of some
# false positives. For an overbooking advisor we prefer catching
# marginal cases, so we set the threshold below the default 0.5.
NO_SHOW_THRESHOLD = 0.30


class NoShowService:
    """
    Predicts no-show probability for bookings and aggregates per flight.
    """

    _model = None   # class-level cache

    def __init__(self, session: Session):
        self.session = session
        self._ensure_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    @classmethod
    def _ensure_model(cls) -> None:
        if cls._model is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"No-show model not found at {MODEL_PATH}.\n"
                    f"Train it first: python -m app.ml.no_show.train"
                )
            cls._model = joblib.load(MODEL_PATH)

    @classmethod
    def is_available(cls) -> bool:
        return MODEL_PATH.exists()

    # ------------------------------------------------------------------
    # Prediction — single booking
    # ------------------------------------------------------------------

    def predict_booking_probability(self, booking) -> float:
        """Return P(no-show) in [0, 1] for a single booking."""
        prior_count = self._passenger_prior_booking_count(booking.passenger_id)
        features = no_show_features_from_booking(
            booking, passenger_booking_count=prior_count
        )
        row = np.array([no_show_features_row(features)])
        return float(self._model.predict_proba(row)[0, 1])

    def predict_booking_class(self, booking) -> int:
        """
        Return 1 if the booking is predicted as a no-show using
        the tuned decision threshold (NO_SHOW_THRESHOLD).
        """
        return int(self.predict_booking_probability(booking) >= NO_SHOW_THRESHOLD)

    # ------------------------------------------------------------------
    # Prediction — aggregate per flight
    # ------------------------------------------------------------------

    def forecast_flight(self, flight_id: int) -> dict:
        """
        Aggregate no-show predictions across all active bookings on a flight.

        Returns:
            {
              "flight_id": int,
              "bookings_count": int,
              "expected_no_shows": float,
              "expected_no_show_rate": float,
              "safe_overbooking": int,
              "confidence": str,
            }
        """
        from app.models.booking import Booking, BookingStatus
        from app.models.flight import Flight

        flight = self.session.get(Flight, flight_id)
        if flight is None:
            raise ValueError(f"Flight {flight_id} not found")

        active_statuses = (
            BookingStatus.CONFIRMED,
            BookingStatus.CHECKED_IN,
        )
        bookings = (
            self.session.query(Booking)
            .filter(
                Booking.flight_id == flight_id,
                Booking.status.in_(active_statuses),
            )
            .all()
        )

        if not bookings:
            return {
                "flight_id": flight_id,
                "bookings_count": 0,
                "expected_no_shows": 0.0,
                "expected_no_show_rate": 0.0,
                "safe_overbooking": 0,
                "confidence": "low",
            }

        probs = [self.predict_booking_probability(b) for b in bookings]
        expected = float(sum(probs))
        rate = expected / len(bookings)

        # Safe overbooking: floor of expected, with a safety margin.
        safe_overbooking = max(0, int(expected * 0.8))

        # Confidence based on sample size.
        if len(bookings) >= 100:
            confidence = "high"
        elif len(bookings) >= 30:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "flight_id": flight_id,
            "bookings_count": len(bookings),
            "expected_no_shows": round(expected, 2),
            "expected_no_show_rate": round(rate, 4),
            "safe_overbooking": safe_overbooking,
            "confidence": confidence,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _passenger_prior_booking_count(self, passenger_id: int) -> int:
        """Count how many bookings this passenger has made previously."""
        from app.models.booking import Booking

        return (
            self.session.query(Booking)
            .filter(Booking.passenger_id == passenger_id)
            .count()
        )