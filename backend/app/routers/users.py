from fastapi import APIRouter, HTTPException

from app.models.schemas import UserProfileCreate, UserProfileResponse, UserProfileUpdate
from app.repositories.user_repository import UserNotFoundError, create_user, get_user, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserProfileResponse)
def create_user_profile(payload: UserProfileCreate) -> dict:
    return create_user(payload.model_dump())


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: str) -> dict:
    try:
        return get_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc


@router.put("/{user_id}", response_model=UserProfileResponse)
def update_user_profile(user_id: str, payload: UserProfileUpdate) -> dict:
    try:
        return update_user(user_id, payload.model_dump(exclude_none=True))
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="User not found") from exc
