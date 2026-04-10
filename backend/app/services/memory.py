import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

from app.core.config import get_settings
from app.repositories.meal_repository import list_meals
from app.repositories.memory_repository import archive_memory, list_memories, upsert_memory
from app.repositories.user_repository import get_user
from app.services.gemini import GeminiServiceError

MEMORY_TYPES = {"profile", "goal", "preference", "restriction", "pattern"}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "memory"


def _sanitize_memory_item(user_id: str, item: dict[str, Any]) -> dict[str, Any]:
    memory_type = str(item.get("memory_type") or "pattern").lower()
    if memory_type not in MEMORY_TYPES:
        memory_type = "pattern"
    title = str(item.get("title") or "Untitled memory").strip()
    summary = str(item.get("summary") or title).strip()
    return {
        "user_id": user_id,
        "memory_type": memory_type,
        "slug": str(item.get("slug") or _slugify(title)),
        "title": title,
        "summary": summary,
        "details": item.get("details"),
        "source_kind": item.get("source_kind") or "memory_refresh",
        "confidence": item.get("confidence") or "medium",
    }


def _memory_file_name(memory: dict[str, Any]) -> str:
    return f"{memory['memory_type']}_{memory['slug']}.md"


def _build_memory_markdown(memory: dict[str, Any]) -> str:
    return (
        "---\n"
        f"title: {memory['title']}\n"
        f"type: {memory['memory_type']}\n"
        f"summary: {memory['summary']}\n"
        f"source_kind: {memory.get('source_kind') or ''}\n"
        f"confidence: {memory.get('confidence') or ''}\n"
        f"updated_at: {memory['updated_at']}\n"
        "---\n\n"
        f"{memory['summary']}\n\n"
        f"{memory.get('details') or ''}\n"
    )


def _export_memory_snapshot(user_id: str, memories: list[dict[str, Any]]) -> str:
    settings = get_settings()
    user_dir = settings.memory_path / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    for existing in user_dir.glob("*.md"):
        existing.unlink()
    manifest_lines = ["# MEMORY", ""]
    for memory in memories:
        file_name = _memory_file_name(memory)
        (user_dir / file_name).write_text(_build_memory_markdown(memory), encoding="utf-8")
        manifest_lines.append(f"- [{memory['title']}]({file_name}) — {memory['summary']}")
    if len(manifest_lines) == 2:
        manifest_lines.append("No active memories yet.")
    manifest_path = user_dir / "MEMORY.md"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    return str(manifest_path)


def _summarize_meals_for_prompt(meals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summarized: list[dict[str, Any]] = []
    for meal in meals:
        summarized.append(
            {
                "meal_name": meal["meal_name"],
                "meal_time": meal["meal_time"],
                "estimated_calories": meal["estimated_calories"],
                "protein_g": meal["protein_g"],
                "carbs_g": meal["carbs_g"],
                "fat_g": meal["fat_g"],
                "health_flags": meal.get("health_flags", []),
                "source_notes": meal.get("source_notes"),
            }
        )
    return summarized


def _build_deterministic_memories(user: dict[str, Any], recent_meals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    memories: list[dict[str, Any]] = []
    if user.get("goal"):
        memories.append(
            {
                "memory_type": "goal",
                "slug": "primary_goal",
                "title": "Primary nutrition goal",
                "summary": f"User is currently focused on {user['goal']}.",
                "details": f"Use this goal to frame meal feedback and future recommendations. Goal source: user profile.",
                "source_kind": "user_profile",
                "confidence": "high",
            }
        )
    if user.get("dietary_preferences"):
        joined = ", ".join(user["dietary_preferences"])
        memories.append(
            {
                "memory_type": "preference",
                "slug": "dietary_preferences",
                "title": "Dietary preferences",
                "summary": f"User dietary preferences: {joined}.",
                "details": "Prefer meal suggestions and follow-up coaching that align with these stated preferences.",
                "source_kind": "user_profile",
                "confidence": "high",
            }
        )
    if user.get("dietary_restrictions"):
        joined = ", ".join(user["dietary_restrictions"])
        memories.append(
            {
                "memory_type": "restriction",
                "slug": "dietary_restrictions",
                "title": "Dietary restrictions",
                "summary": f"User dietary restrictions: {joined}.",
                "details": "These restrictions should be treated as hard constraints when generating meal suggestions.",
                "source_kind": "user_profile",
                "confidence": "high",
            }
        )
    if not recent_meals:
        return memories

    avg_protein = sum(meal["protein_g"] for meal in recent_meals) / len(recent_meals)
    avg_calories = sum(meal["estimated_calories"] for meal in recent_meals) / len(recent_meals)
    if avg_protein < 20:
        memories.append(
            {
                "memory_type": "pattern",
                "slug": "low_average_protein",
                "title": "Protein intake often low",
                "summary": f"Recent meals average about {avg_protein:.1f}g protein, which may be low for sustained satiety or muscle-supporting goals.",
                "details": "Prioritize protein-aware coaching in future summaries and meal suggestions.",
                "source_kind": "meal_pattern",
                "confidence": "medium",
            }
        )
    if avg_calories > 850:
        memories.append(
            {
                "memory_type": "pattern",
                "slug": "high_average_meal_calories",
                "title": "Meals are often calorie-dense",
                "summary": f"Recent meals average around {avg_calories:.0f} kcal per meal.",
                "details": "Future coaching can suggest lighter swaps, portion awareness, and balance across the rest of the day.",
                "source_kind": "meal_pattern",
                "confidence": "medium",
            }
        )
    late_meal_count = sum(1 for meal in recent_meals if _extract_hour(meal.get("meal_time")) >= 21)
    if late_meal_count >= 2:
        memories.append(
            {
                "memory_type": "pattern",
                "slug": "late_eating_pattern",
                "title": "Late eating pattern",
                "summary": f"Recent logs include {late_meal_count} meals recorded at or after 21:00.",
                "details": "Suggestions can account for irregular schedule and late-night eating habits.",
                "source_kind": "meal_pattern",
                "confidence": "medium",
            }
        )
    flag_counter: Counter[str] = Counter()
    for meal in recent_meals:
        flag_counter.update(meal.get("health_flags", []))
    for flag, count in flag_counter.items():
        if count >= 2:
            memories.append(
                {
                    "memory_type": "pattern",
                    "slug": f"flag_{_slugify(flag)}",
                    "title": f"Recurring nutrition flag: {flag}",
                    "summary": f"The flag '{flag}' appeared in {count} recent meal analyses.",
                    "details": "This indicates a repeated issue worth considering in future summaries and recommendations.",
                    "source_kind": "meal_pattern",
                    "confidence": "medium",
                }
            )
    return memories


def _extract_hour(value: str | None) -> int:
    if not value:
        return -1
    match = re.search(r"T(\d{2}):", value)
    if match:
        return int(match.group(1))
    return -1


def _extract_json(text: str) -> dict[str, Any]:
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1)
    return json.loads(text)


def _build_llm_prompt(user: dict[str, Any], recent_meals: list[dict[str, Any]], existing_memories: list[dict[str, Any]]) -> str:
    return (
        "You are maintaining a lightweight persistent memory system for a nutrition coaching backend. "
        "Your job is to identify durable user-specific memories that will improve future personalized dietary coaching. "
        "Prefer stable or repeated facts over one-off observations. Avoid medical diagnosis. Avoid duplicating existing memories. "
        "Return only valid JSON with the shape: "
        '{"upserts": [{"memory_type": "goal|preference|restriction|pattern|profile", "slug": "snake_case_slug", "title": "...", "summary": "...", "details": "...", "source_kind": "user_profile|meal_pattern|llm_inference", "confidence": "low|medium|high"}], "archives": [{"memory_type": "...", "slug": "..."}]}. '
        f"User profile: {json.dumps(user, ensure_ascii=False)}. "
        f"Recent meals: {json.dumps(_summarize_meals_for_prompt(recent_meals), ensure_ascii=False)}. "
        f"Existing memories: {json.dumps(existing_memories, ensure_ascii=False)}"
    )


async def _extract_llm_memories(user: dict[str, Any], recent_meals: list[dict[str, Any]], existing_memories: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    settings = get_settings()
    if not settings.gemini_api_key:
        return [], []
    endpoint = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": _build_llm_prompt(user, recent_meals, existing_memories)}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(endpoint, json=payload)
    if response.status_code >= 400:
        raise GeminiServiceError(f"Gemini memory refresh failed: {response.status_code} {response.text}")
    raw = response.json()
    candidates = raw.get("candidates") or []
    if not candidates:
        return [], []
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict))
    if not text:
        return [], []
    parsed = _extract_json(text)
    upserts = parsed.get("upserts") if isinstance(parsed.get("upserts"), list) else []
    archives = parsed.get("archives") if isinstance(parsed.get("archives"), list) else []
    return upserts, archives


async def refresh_user_memory(user_id: str, use_llm: bool = False) -> dict[str, Any]:
    settings = get_settings()
    user = get_user(user_id)
    recent_meals = list_meals(user_id=user_id)[: settings.memory_recent_meal_limit]
    existing_memories = list_memories(user_id=user_id, active_only=False)

    deterministic = [_sanitize_memory_item(user_id, item) for item in _build_deterministic_memories(user, recent_meals)]
    llm_upserts: list[dict[str, Any]] = []
    llm_archives: list[dict[str, str]] = []
    llm_error: str | None = None

    if use_llm:
        try:
            raw_upserts, raw_archives = await _extract_llm_memories(user, recent_meals, existing_memories)
            llm_upserts = [_sanitize_memory_item(user_id, item) for item in raw_upserts if isinstance(item, dict)]
            llm_archives = [
                {"memory_type": str(item.get("memory_type") or "pattern"), "slug": str(item.get("slug") or "")}
                for item in raw_archives
                if isinstance(item, dict) and item.get("slug")
            ]
        except (GeminiServiceError, json.JSONDecodeError) as exc:
            llm_error = str(exc)

    merged_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for item in deterministic + llm_upserts:
        merged_by_key[(item["memory_type"], item["slug"])] = item

    archived_count = 0
    managed_source_kinds = {"user_profile", "meal_pattern", "memory_refresh", "llm_inference"}
    current_keys = set(merged_by_key.keys())
    for memory in existing_memories:
        key = (memory["memory_type"], memory["slug"])
        if memory.get("source_kind") in managed_source_kinds and key not in current_keys and memory.get("is_active"):
            archive_memory(user_id=user_id, memory_type=memory["memory_type"], slug=memory["slug"])
            archived_count += 1

    for item in llm_archives:
        archive_memory(user_id=user_id, memory_type=item["memory_type"], slug=item["slug"])
        archived_count += 1

    for item in merged_by_key.values():
        upsert_memory(item)

    active_memories = list_memories(user_id=user_id, active_only=True)
    manifest_path = _export_memory_snapshot(user_id, active_memories)
    return {
        "user_id": user_id,
        "memory_count": len(active_memories),
        "archived_count": archived_count,
        "used_llm": use_llm,
        "llm_error": llm_error,
        "manifest_path": manifest_path,
        "memories": active_memories,
    }


def get_user_memory_manifest(user_id: str) -> dict[str, Any]:
    active_memories = list_memories(user_id=user_id, active_only=True)
    manifest_path = _export_memory_snapshot(user_id, active_memories)
    manifest = Path(manifest_path).read_text(encoding="utf-8")
    return {
        "user_id": user_id,
        "manifest_path": manifest_path,
        "manifest": manifest,
    }
