from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import MemoryManifestResponse, MemoryRefreshResponse, MemoryRecordResponse
from app.repositories.user_repository import UserNotFoundError, get_user
from app.services.memory import get_user_memory_manifest, refresh_user_memory
from app.repositories.memory_repository import list_memories

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("", response_model=list[MemoryRecordResponse])
def get_memories(user_id: str, active_only: bool = Query(default=True)) -> list[dict]:
    try:
        get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
    return list_memories(user_id=user_id, active_only=active_only)


@router.post("/refresh", response_model=MemoryRefreshResponse)
async def refresh_memories(user_id: str, use_llm: bool = Query(default=False)) -> dict:
    try:
        return await refresh_user_memory(user_id=user_id, use_llm=use_llm)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


@router.get("/manifest/{user_id}", response_model=MemoryManifestResponse)
def get_memory_manifest(user_id: str) -> dict:
    try:
        get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
    return get_user_memory_manifest(user_id)
