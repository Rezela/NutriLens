import base64
import json
import re
from typing import Any

import httpx

from app.core.config import get_settings


class GeminiServiceError(Exception):
    pass


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise GeminiServiceError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part.get("text", "") for part in parts if isinstance(part, dict)]
    text = "\n".join(item for item in text_parts if item)
    if not text:
        raise GeminiServiceError("Gemini returned an empty response")
    return text


def _extract_json(text: str) -> dict[str, Any]:
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise GeminiServiceError("Gemini response was not valid JSON")
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise GeminiServiceError("Gemini response JSON could not be parsed") from exc


def _normalize_items(items: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    if not isinstance(items, list):
        return normalized
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "name": str(item.get("name") or "Unknown item"),
                "estimated_portion": item.get("estimated_portion") or item.get("portion"),
                "calories": _safe_float(item.get("calories")),
                "protein_g": _safe_float(item.get("protein_g")),
                "carbs_g": _safe_float(item.get("carbs_g")),
                "fat_g": _safe_float(item.get("fat_g")),
            }
        )
    return normalized


def _normalize_analysis(raw: dict[str, Any]) -> dict[str, Any]:
    macros = raw.get("macros") if isinstance(raw.get("macros"), dict) else {}
    return {
        "meal_name": str(raw.get("meal_name") or raw.get("title") or "Unknown meal"),
        "description": raw.get("description"),
        "estimated_calories": _safe_float(raw.get("estimated_calories") or raw.get("calories")),
        "protein_g": _safe_float(raw.get("protein_g") or macros.get("protein_g")),
        "carbs_g": _safe_float(raw.get("carbs_g") or macros.get("carbs_g")),
        "fat_g": _safe_float(raw.get("fat_g") or macros.get("fat_g")),
        "items": _normalize_items(raw.get("items")),
        "confidence": raw.get("confidence"),
        "health_flags": raw.get("health_flags") if isinstance(raw.get("health_flags"), list) else [],
        "follow_up_questions": raw.get("follow_up_questions") if isinstance(raw.get("follow_up_questions"), list) else [],
        "reasoning_summary": raw.get("reasoning_summary") or raw.get("summary"),
    }


def _build_prompt(notes: str | None, user_profile: dict[str, Any] | None) -> str:
    profile_text = json.dumps(user_profile or {}, ensure_ascii=False)
    note_text = notes or ""
    return (
        "You are an AI nutrition analysis assistant. Analyze the meal image and optional notes. "
        "Return only valid JSON with these fields: meal_name, description, estimated_calories, "
        "protein_g, carbs_g, fat_g, items, confidence, health_flags, follow_up_questions, reasoning_summary. "
        "Each item in items should contain name, estimated_portion, calories, protein_g, carbs_g, fat_g. "
        "Use conservative estimates when uncertain and avoid medical diagnosis. "
        f"User profile: {profile_text}. "
        f"User notes: {note_text}"
    )


async def analyze_food_image(
    image_bytes: bytes,
    mime_type: str,
    notes: str | None = None,
    user_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiServiceError("GEMINI_API_KEY is not configured")

    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": _build_prompt(notes, user_profile)},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": base64.b64encode(image_bytes).decode("utf-8"),
                        }
                    },
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(endpoint, json=payload)

    if response.status_code >= 400:
        raise GeminiServiceError(f"Gemini request failed: {response.status_code} {response.text}")

    raw_payload = response.json()
    text = _extract_text(raw_payload)
    json_payload = _extract_json(text)
    return _normalize_analysis(json_payload)
