import base64
import json
import re
from functools import lru_cache
from typing import Any

import google.auth
import httpx
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from app.core.config import get_settings

VERTEX_SCOPES = ("https://www.googleapis.com/auth/cloud-platform",)


class GeminiServiceError(Exception):
    pass


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _summarize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    first_candidate = candidates[0] if candidates and isinstance(candidates[0], dict) else {}
    content = first_candidate.get("content") if isinstance(first_candidate.get("content"), dict) else {}
    parts = content.get("parts") if isinstance(content.get("parts"), list) else []
    return {
        "candidate_count": len(candidates),
        "finish_reason": first_candidate.get("finishReason"),
        "prompt_feedback": payload.get("promptFeedback"),
        "part_keys": [sorted(part.keys()) for part in parts if isinstance(part, dict)],
        "usage_metadata": payload.get("usageMetadata"),
    }


def _extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise GeminiServiceError(f"Gemini returned no candidates: {_summarize_payload(payload)}")
    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part.get("text", "") for part in parts if isinstance(part, dict)]
    text = "\n".join(item for item in text_parts if item)
    if not text:
        raise GeminiServiceError(f"Gemini returned an empty response: {_summarize_payload(payload)}")
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


@lru_cache
def _load_service_account_credentials(credentials_path: str):
    return service_account.Credentials.from_service_account_file(credentials_path, scopes=list(VERTEX_SCOPES))


@lru_cache
def _load_default_credentials() -> tuple[Any, str | None]:
    credentials, project_id = google.auth.default(scopes=list(VERTEX_SCOPES))
    return credentials, project_id


def _describe_credentials(credentials: Any) -> dict[str, Any]:
    credential_source = "service_account_file" if isinstance(credentials, service_account.Credentials) else "application_default_credentials"
    return {
        "credential_source": credential_source,
        "service_account_email": getattr(credentials, "service_account_email", None),
    }


def _resolve_vertex_credentials() -> tuple[Any, str, str]:
    settings = get_settings()
    credentials_path = settings.google_application_credentials_path
    if credentials_path is not None:
        if not credentials_path.exists():
            raise GeminiServiceError(f"GOOGLE_APPLICATION_CREDENTIALS file not found: {credentials_path}")
        credentials = _load_service_account_credentials(str(credentials_path))
        project_id = settings.google_cloud_project or getattr(credentials, "project_id", None) or ""
    else:
        credentials, detected_project = _load_default_credentials()
        project_id = settings.google_cloud_project or detected_project or ""
    if not project_id:
        raise GeminiServiceError("GOOGLE_CLOUD_PROJECT is not configured")
    if not settings.google_cloud_location:
        raise GeminiServiceError("GOOGLE_CLOUD_LOCATION is not configured")
    return credentials, project_id, settings.google_cloud_location


def _format_runtime_context(runtime_context: dict[str, Any], endpoint: str | None = None) -> str:
    context_parts = [
        f"credential_source={runtime_context.get('credential_source')}",
        f"service_account_email={runtime_context.get('service_account_email') or 'unknown'}",
        f"project_id={runtime_context.get('project_id')}",
        f"location={runtime_context.get('location')}",
    ]
    if endpoint:
        context_parts.append(f"endpoint={endpoint}")
    return ", ".join(context_parts)


def _get_access_token() -> tuple[str, str, str, dict[str, Any]]:
    credentials, project_id, location = _resolve_vertex_credentials()
    if not credentials.valid or not getattr(credentials, "token", None):
        credentials.refresh(Request())
    access_token = getattr(credentials, "token", None)
    if not access_token:
        raise GeminiServiceError("Could not obtain Vertex AI access token")
    runtime_context = {
        **_describe_credentials(credentials),
        "project_id": project_id,
        "location": location,
    }
    return access_token, project_id, location, runtime_context


def _build_vertex_endpoint(project_id: str, location: str, model: str) -> str:
    if location == "global":
        return (
            f"https://aiplatform.googleapis.com/v1/projects/{project_id}"
            f"/locations/{location}/publishers/google/models/{model}:generateContent"
        )
    return (
        f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}"
        f"/locations/{location}/publishers/google/models/{model}:generateContent"
    )


async def generate_content(
    parts: list[dict[str, Any]],
    temperature: float = 0.2,
    response_mime_type: str | None = None,
    max_output_tokens: int | None = None,
    thinking_budget: int | None = None,
    timeout: int = 90,
) -> dict[str, Any]:
    settings = get_settings()
    access_token, project_id, location, runtime_context = _get_access_token()
    payload: dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": parts,
            }
        ],
        "generationConfig": {
            "temperature": temperature,
        },
    }
    if response_mime_type:
        payload["generationConfig"]["responseMimeType"] = response_mime_type
    if max_output_tokens is not None:
        payload["generationConfig"]["maxOutputTokens"] = max_output_tokens
    if thinking_budget is not None:
        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": thinking_budget}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    endpoint = _build_vertex_endpoint(project_id=project_id, location=location, model=settings.gemini_model)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(endpoint, headers=headers, json=payload)

    if response.status_code >= 400:
        context_label = _format_runtime_context(runtime_context, endpoint=endpoint)
        raise GeminiServiceError(f"Gemini request failed ({context_label}): {response.status_code} {response.text}")

    return response.json()


def extract_response_text(payload: dict[str, Any]) -> str:
    return _extract_text(payload)


def extract_response_json(payload: dict[str, Any]) -> dict[str, Any]:
    return _extract_json(_extract_text(payload))


async def check_gemini_health() -> dict[str, Any]:
    settings = get_settings()
    credentials, project_id, location = _resolve_vertex_credentials()
    credential_details = _describe_credentials(credentials)
    raw_payload = await generate_content(
        parts=[{"text": "Reply with OK."}],
        temperature=0,
        max_output_tokens=32,
        thinking_budget=0,
        timeout=30,
    )
    try:
        response_text = extract_response_text(raw_payload).strip()
    except GeminiServiceError as exc:
        raise GeminiServiceError(f"{exc}; raw_payload={json.dumps(raw_payload, ensure_ascii=False)}") from exc
    return {
        "status": "ok",
        "provider": "vertex_ai",
        "model": settings.gemini_model,
        "project_id": project_id,
        "location": location,
        "credential_source": credential_details["credential_source"],
        "service_account_email": credential_details["service_account_email"],
        "endpoint": _build_vertex_endpoint(project_id=project_id, location=location, model=settings.gemini_model),
        "response_text": response_text,
    }


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
    raw_payload = await generate_content(
        parts=[
            {"text": _build_prompt(notes, user_profile)},
            {
                "inlineData": {
                    "mimeType": mime_type,
                    "data": base64.b64encode(image_bytes).decode("utf-8"),
                }
            },
        ],
        temperature=0.2,
        response_mime_type="application/json",
        timeout=90,
    )
    json_payload = extract_response_json(raw_payload)
    return _normalize_analysis(json_payload)
