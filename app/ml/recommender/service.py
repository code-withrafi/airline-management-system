# app/ml/recommender/service.py
"""
Recommendation service.

Produces personalised route recommendations using the trained
item-item similarity matrix, with a popularity-based fallback
for cold-start (anonymous / new) users.
"""

from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session


MODEL_PATH = Path("app/ml/models/recommender_v1.pkl")


class RecommenderService:
    """
    Produces route recommendations for a passenger.

    Two modes:
      - Personalised: if the passenger has booking history
      - Popularity fallback: otherwise (or if not logged in)
    """

    _artifact = None   # class-level cache

    def __init__(self, session: Session):
        self.session = session
        self._ensure_artifact()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    @classmethod
    def _ensure_artifact(cls) -> None:
        if cls._artifact is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Recommender model not found at {MODEL_PATH}.\n"
                    f"Train it first: python -m app.ml.recommender.train"
                )
            cls._artifact = joblib.load(MODEL_PATH)

    @classmethod
    def is_available(cls) -> bool:
        return MODEL_PATH.exists()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend_for_passenger(
        self,
        passenger_id: int | None,
        *,
        top_k: int = 3,
    ) -> dict:
        """
        Return a recommendation response.

        If `passenger_id` is None (anonymous) or the passenger has no
        booking history, returns popularity-based recommendations.

        Returns:
            {
              "personalized": bool,
              "based_on": list[str] | None,
              "recommendations": [
                {"route_id": int, "origin": str, "destination": str,
                 "score": float},
                ...
              ]
            }
        """
        if passenger_id is None:
            return self._popularity_fallback(top_k=top_k)

        booked_route_ids = self._booked_route_ids(passenger_id)

        if not booked_route_ids:
            return self._popularity_fallback(top_k=top_k)

        return self._personalized(booked_route_ids, top_k=top_k)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _booked_route_ids(self, passenger_id: int) -> list[int]:
        """Return route IDs of flights this passenger has booked."""
        from app.models.booking import Booking

        rows = (
            self.session.query(Booking)
            .filter(Booking.passenger_id == passenger_id)
            .all()
        )

        route_ids = set()
        for b in rows:
            if b.flight and b.flight.route_id:
                route_ids.add(int(b.flight.route_id))
        return sorted(route_ids)

    def _personalized(self, booked_route_ids: list[int], *, top_k: int) -> dict:
        """Item-item collaborative filtering for a passenger."""
        artifact = self._artifact
        route_ids = artifact["route_ids"]
        route_index = artifact["route_index"]
        similarity = artifact["similarity"]

        # Only consider routes we know about
        known = [r for r in booked_route_ids if r in route_index]
        if not known:
            return self._popularity_fallback(top_k=top_k)

        # Aggregate similarity across all booked routes
        candidate_scores = np.zeros(len(route_ids), dtype=float)
        for r in known:
            i = route_index[r]
            candidate_scores += similarity[i]

        # Normalise by number of seed routes
        candidate_scores /= len(known)

        # Exclude already-booked routes
        for r in known:
            candidate_scores[route_index[r]] = 0.0

        # Rank
        top_idx = np.argsort(-candidate_scores)[:top_k]

        # Build response
        recommendations = []
        for idx in top_idx:
            if candidate_scores[idx] <= 0:
                continue
            route_id = int(route_ids[idx])          # numpy → Python int
            origin, destination = self._route_codes(route_id)
            recommendations.append({
                "route_id": route_id,
                "origin": origin,
                "destination": destination,
                "score": round(float(candidate_scores[idx]), 4),
            })

        # If we filtered everything out, fall back
        if not recommendations:
            return self._popularity_fallback(top_k=top_k)

        return {
            "personalized": True,
            "based_on": [self._route_label(int(r)) for r in known],
            "recommendations": recommendations,
        }

    def _popularity_fallback(self, *, top_k: int) -> dict:
        """Return the top-K most popular routes globally."""
        artifact = self._artifact
        popularity_sorted = artifact["popularity_sorted"]

        recommendations = []
        for route_id, count in popularity_sorted[:top_k]:
            route_id = int(route_id)                # numpy → Python int
            origin, destination = self._route_codes(route_id)
            recommendations.append({
                "route_id": route_id,
                "origin": origin,
                "destination": destination,
                "score": float(count),
            })

        return {
            "personalized": False,
            "based_on": None,
            "recommendations": recommendations,
        }

    def _route_codes(self, route_id: int) -> tuple[str, str]:
        """Return (origin_iata, destination_iata) for a route."""
        from app.models.route import Route

        route = self.session.get(Route, route_id)
        if route is None:
            return ("?", "?")
        origin = (
            route.origin_airport.iata_code
            if route.origin_airport else "?"
        )
        destination = (
            route.destination_airport.iata_code
            if route.destination_airport else "?"
        )
        return (origin, destination)

    def _route_label(self, route_id: int) -> str:
        o, d = self._route_codes(route_id)
        return f"{o} \u2192 {d}"