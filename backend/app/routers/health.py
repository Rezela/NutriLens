from fastapi import APIRouter
from fastapi import HTTPException

from app.services.gemini import GeminiServiceError, check_gemini_health

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/health/gemini")
async def gemini_health_check() -> dict:
    try:
        return await check_gemini_health()
    except GeminiServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
