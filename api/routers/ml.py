# api/routers/ml.py
"""
Machine learning endpoints.

Exposes:
  - No-show forecasting (admin / staff only)
  - Route recommendations (public — personalises for logged-in passengers)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ml.no_show.service import NoShowService
from app.ml.recommender.service import RecommenderService
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from api.deps import get_db, get_current_user
from api.security_jwt import decode_access_token


router = APIRouter()


# ------------------------------------------------------------------
# Optional authentication
# ------------------------------------------------------------------

oauth2_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_optional),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Return the current user if a valid token is present, otherwise None.

    Used for endpoints that work for both anonymous and authenticated
    users (e.g., the recommendations endpoint).
    """
    if not token:
        return None

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    return UserRepository(db).get_by_id(int(user_id))


def require_admin_or_staff(user: User = Depends(get_current_user)) -> User:
    """ML admin endpoints are for admin or staff only."""
    if user.role not in (UserRole.ADMIN, UserRole.STAFF):
        raise HTTPException(
            status_code=403,
            detail="Admin or staff access required.",
        )
    return user


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class NoShowForecast(BaseModel):
    flight_id: int
    bookings_count: int
    expected_no_shows: float
    expected_no_show_rate: float
    safe_overbooking: int
    confidence: str


class RouteRecommendation(BaseModel):
    route_id: int
    origin: str
    destination: str
    score: float


class RecommendationResponse(BaseModel):
    personalized: bool
    based_on: Optional[list[str]] = None
    recommendations: list[RouteRecommendation]


# ------------------------------------------------------------------
# Endpoints — No-Show
# ------------------------------------------------------------------

@router.get(
    "/flights/{flight_id}/no-show-forecast",
    response_model=NoShowForecast,
)
def no_show_forecast(
    flight_id: int,
    _user: User = Depends(require_admin_or_staff),
    db: Session = Depends(get_db),
):
    """
    Predict expected no-shows for a flight and suggest safe overbooking.
    Requires admin or staff role.
    """
    if not NoShowService.is_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "No-show model not trained yet. "
                "Run: python -m app.ml.no_show.train"
            ),
        )

    try:
        service = NoShowService(db)
        forecast = service.forecast_flight(flight_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}")

    return NoShowForecast(**forecast)


# ------------------------------------------------------------------
# Endpoints — Recommendations
# ------------------------------------------------------------------

@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
)
def get_recommendations(
    top_k: int = 3,
    user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Get route recommendations.

    Works for both anonymous visitors (returns global popular routes)
    and logged-in passengers with booking history (returns personalised
    recommendations based on item-item collaborative filtering).
    """
    if not RecommenderService.is_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "Recommender model not trained yet. "
                "Run: python -m app.ml.recommender.train"
            ),
        )

    passenger_id: Optional[int] = None

    if user is not None and user.role == UserRole.PASSENGER:
        from app.repositories.passenger_repository import PassengerRepository

        passenger = PassengerRepository(db).get_by_user_id(user.id)
        if passenger is not None:
            passenger_id = passenger.id

    try:
        service = RecommenderService(db)
        result = service.recommend_for_passenger(
            passenger_id,
            top_k=min(max(top_k, 1), 10),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation failed: {exc}",
        )

    return RecommendationResponse(**result)