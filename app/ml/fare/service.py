# app/ml/fare/service.py
"""
Fare prediction service.

Produces a final fare = base_fare(distance) × predicted_multiplier.
"""

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.ml.fare.features import (
    base_fare_for_route,
    fare_features,
    fare_features_row,
)


MODEL_PATH = Path("app/ml/models/fare_v1.pkl")


class FarePredictorService:
    """Predicts a per-flight fare using distance base + ML multiplier."""

    _model = None

    def __init__(self, session: Session):
        self.session = session
        self._ensure_model()

    @classmethod
    def _ensure_model(cls) -> None:
        if cls._model is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Fare model not found at {MODEL_PATH}.\n"
                    f"Train it first: python -m app.ml.fare.train"
                )
            cls._model = joblib.load(MODEL_PATH)

    @classmethod
    def is_available(cls) -> bool:
        return MODEL_PATH.exists()

    def predict(
        self,
        *,
        route,
        departure_time: datetime,
    ) -> Decimal:
        """
        Return the economy fare for a flight.

        Uses route distance for the base fare and the ML model for
        the multiplier. Falls back to just the base fare if the model
        fails.
        """
        distance_km = int(route.distance_km if route else 500)
        base = base_fare_for_route(distance_km)

        try:
            features = fare_features(
                route_distance_km=distance_km,
                departure_time=departure_time,
            )
            row = np.array([fare_features_row(features)])
            multiplier = float(self._model.predict(row)[0])
        except Exception:
            multiplier = 1.0

        fare = Decimal(str(base)) * Decimal(str(multiplier))
        return fare.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def predict_multiplier_only(self, *, route, departure_time: datetime) -> float:
        """Return just the multiplier (for debugging / reporting)."""
        distance_km = int(route.distance_km if route else 500)
        features = fare_features(
            route_distance_km=distance_km,
            departure_time=departure_time,
        )
        row = np.array([fare_features_row(features)])
        return float(self._model.predict(row)[0])