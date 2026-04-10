from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import DailyRecommendationResponse
from app.repositories.user_repository import UserNotFoundError
from app.services.recommendation import build_daily_recommendation

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/daily", response_model=DailyRecommendationResponse)
def get_daily_recommendation(user_id: str, target_date: date | None = Query(default=None, alias="date")) -> dict:
    try:
        return build_daily_recommendation(user_id=user_id, target_date=target_date or date.today())
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
