from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.core.config import get_settings
from app.models.schemas import DailyNutritionStats, MealAnalysisResponse, MealLogResponse
from app.repositories.meal_repository import create_meal_log, get_daily_stats, list_meals
from app.repositories.user_repository import UserNotFoundError, get_user
from app.services.gemini import GeminiServiceError, analyze_food_image
from app.services.memory import refresh_user_memory

router = APIRouter(prefix="/meals", tags=["meals"])


def _save_upload(file: UploadFile, content: bytes) -> str:
    settings = get_settings()
    suffix = Path(file.filename or "meal.jpg").suffix or ".jpg"
    file_name = f"{uuid4()}{suffix}"
    destination = settings.upload_path / file_name
    destination.write_bytes(content)
    return str(destination)


@router.post("/analyze", response_model=MealAnalysisResponse)
async def analyze_meal(
    image: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    meal_time: str | None = Form(default=None),
    save_result: bool = Form(default=True),
) -> dict:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")

    user_profile = None
    if user_id:
        try:
            user_profile = get_user(user_id)
        except UserNotFoundError as exc:
            raise HTTPException(status_code=404, detail="User not found") from exc

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    image_path = _save_upload(image, image_bytes)

    try:
        analysis = await analyze_food_image(
            image_bytes=image_bytes,
            mime_type=image.content_type,
            notes=notes,
            user_profile=user_profile,
        )
    except GeminiServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    saved_meal_id = None
    if save_result:
        meal_payload = {
            **analysis,
            "user_id": user_id,
            "image_path": image_path,
            "meal_time": meal_time or datetime.utcnow().isoformat(),
            "source_notes": notes,
            "raw_model_output": analysis,
        }
        meal_record = create_meal_log(meal_payload)
        saved_meal_id = meal_record["id"]
        if user_id:
            await refresh_user_memory(user_id=user_id, use_llm=False)

    return {
        "analysis": analysis,
        "saved_meal_id": saved_meal_id,
    }


@router.get("", response_model=list[MealLogResponse])
def get_meal_logs(user_id: str | None = Query(default=None)) -> list[dict]:
    return list_meals(user_id=user_id)


@router.get("/stats/daily", response_model=DailyNutritionStats)
def get_daily_nutrition_stats(user_id: str, target_date: date | None = Query(default=None, alias="date")) -> dict:
    stats_date = target_date or date.today()
    return get_daily_stats(user_id=user_id, target_date=stats_date)
