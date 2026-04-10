from datetime import date
from typing import Any

from app.repositories.meal_repository import get_daily_stats, list_meals
from app.repositories.memory_repository import list_memories
from app.repositories.user_repository import get_user

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def _normalize_goal(goal: str | None) -> str:
    text = (goal or "").lower()
    if any(keyword in text for keyword in ("lose", "loss", "fat", "cut", "减脂", "减重")):
        return "fat_loss"
    if any(keyword in text for keyword in ("gain", "bulk", "muscle", "增肌")):
        return "muscle_gain"
    if any(keyword in text for keyword in ("maintain", "maintenance", "保持")):
        return "maintenance"
    return "general_health"


def _activity_multiplier(activity_level: str | None) -> float:
    text = (activity_level or "").lower()
    if "very" in text and "active" in text:
        return ACTIVITY_MULTIPLIERS["very_active"]
    if "moderate" in text:
        return ACTIVITY_MULTIPLIERS["moderate"]
    if "light" in text:
        return ACTIVITY_MULTIPLIERS["light"]
    if "active" in text:
        return ACTIVITY_MULTIPLIERS["active"]
    return ACTIVITY_MULTIPLIERS["sedentary"]


def _estimate_calorie_target(user: dict[str, Any], goal_type: str) -> float:
    weight = user.get("weight_kg")
    height = user.get("height_cm")
    age = user.get("age")
    sex = str(user.get("sex") or "").lower()
    if isinstance(weight, (int, float)) and isinstance(height, (int, float)) and isinstance(age, (int, float)) and weight > 0 and height > 0 and age > 0:
        sex_adjustment = -78
        if sex in {"male", "man", "m"}:
            sex_adjustment = 5
        elif sex in {"female", "woman", "f"}:
            sex_adjustment = -161
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + sex_adjustment
        baseline = bmr * _activity_multiplier(user.get("activity_level"))
    elif isinstance(weight, (int, float)) and weight > 0:
        baseline = weight * 30
    else:
        baseline = 2000.0
    adjustments = {
        "fat_loss": -350,
        "muscle_gain": 250,
        "maintenance": 0,
        "general_health": 0,
    }
    return round(max(1200.0, baseline + adjustments[goal_type]), 1)


def _estimate_protein_target(user: dict[str, Any], goal_type: str) -> float:
    weight = user.get("weight_kg")
    factors = {
        "fat_loss": 1.6,
        "muscle_gain": 1.8,
        "maintenance": 1.4,
        "general_health": 1.2,
    }
    fallbacks = {
        "fat_loss": 100.0,
        "muscle_gain": 120.0,
        "maintenance": 90.0,
        "general_health": 90.0,
    }
    if isinstance(weight, (int, float)) and weight > 0:
        return round(weight * factors[goal_type], 1)
    return fallbacks[goal_type]


def _build_overview(
    stats: dict[str, Any],
    calorie_target: float,
    protein_target: float,
    user: dict[str, Any],
    memory_count: int,
) -> str:
    goal_text = user.get("goal") or "general health"
    return (
        f"For {stats['date']}, the user logged {stats['meal_count']} meals, reached {stats['total_calories']:.0f}/{calorie_target:.0f} kcal, "
        f"and {stats['total_protein_g']:.0f}/{protein_target:.0f} g protein. "
        f"Recommendations are aligned with the current goal of {goal_text} and {memory_count} active memory signals."
    )


def _protein_examples(user: dict[str, Any]) -> str:
    preferences = [item.lower() for item in user.get("dietary_preferences", [])]
    restrictions = [item.lower() for item in user.get("dietary_restrictions", [])]
    if any(keyword in preferences + restrictions for keyword in ("vegan", "plant-based", "素食")):
        return "tofu, tempeh, edamame, soy milk, lentils"
    if any(keyword in preferences + restrictions for keyword in ("vegetarian", "蛋奶素")):
        return "Greek yogurt, eggs, tofu, tempeh, cottage cheese"
    return "chicken, fish, eggs, Greek yogurt, tofu"


def _add_suggestion(
    suggestions: list[dict[str, Any]],
    seen_titles: set[str],
    category: str,
    priority: str,
    title: str,
    message: str,
    rationale: str,
) -> None:
    if title in seen_titles:
        return
    seen_titles.add(title)
    suggestions.append(
        {
            "category": category,
            "priority": priority,
            "title": title,
            "message": message,
            "rationale": rationale,
        }
    )


def build_daily_recommendation(user_id: str, target_date: date) -> dict[str, Any]:
    user = get_user(user_id)
    stats = get_daily_stats(user_id=user_id, target_date=target_date)
    memories = list_memories(user_id=user_id, active_only=True)
    all_meals = list_meals(user_id=user_id)
    day_prefix = target_date.isoformat()
    todays_meals = [meal for meal in all_meals if str(meal.get("meal_time") or "").startswith(day_prefix)]
    recent_meal = todays_meals[0] if todays_meals else (all_meals[0] if all_meals else None)

    goal_type = _normalize_goal(user.get("goal"))
    calorie_target = _estimate_calorie_target(user, goal_type)
    protein_target = _estimate_protein_target(user, goal_type)
    calorie_gap = round(calorie_target - stats["total_calories"], 1)
    protein_gap = round(protein_target - stats["total_protein_g"], 1)

    suggestions: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    focus: list[str] = []

    if stats["meal_count"] == 0:
        focus.append("Build meal logging consistency")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="tracking",
            priority="high",
            title="Start with a balanced first meal",
            message=f"When you log the next meal, include a clear protein source plus produce. Good options: {_protein_examples(user)}.",
            rationale="No meals are logged for the selected date, so the first priority is establishing a usable nutrition baseline.",
        )
    if protein_gap > 20:
        focus.append("Increase protein density")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="protein",
            priority="high" if protein_gap > 35 else "medium",
            title="Close the protein gap",
            message=f"The user is about {protein_gap:.0f} g below the estimated protein target. Add one protein-focused meal or snack using foods like {_protein_examples(user)}.",
            rationale="Protein is below the estimated daily target derived from body weight and goal.",
        )
    if goal_type == "fat_loss" and stats["total_calories"] > calorie_target * 1.1:
        focus.append("Lower calorie density")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="energy",
            priority="high",
            title="Use a lighter next meal",
            message="Calories are already above the estimated target for fat loss. Keep the next meal lighter by prioritizing lean protein, vegetables, and lower-calorie sides.",
            rationale="Daily energy intake is running above the personalized target for the stated goal.",
        )
    if goal_type == "muscle_gain" and calorie_gap > 350:
        focus.append("Support calorie surplus for muscle gain")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="energy",
            priority="high",
            title="Add a recovery snack",
            message="The user is still well below the estimated calorie target for muscle gain. Add an extra snack or mini-meal that combines protein and carbohydrates.",
            rationale="Muscle gain usually needs both sufficient calories and protein across the day.",
        )
    if goal_type in {"maintenance", "general_health"} and calorie_gap > 500 and stats["meal_count"] > 0:
        focus.append("Round out the day more evenly")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="energy",
            priority="medium",
            title="Even out intake across the day",
            message="Intake is still quite low relative to the estimated daily target. A balanced final meal or snack may help keep energy steadier.",
            rationale="Very low intake can make it harder to sustain energy and adherence, even outside explicit fat-loss goals.",
        )

    memory_by_slug = {memory["slug"]: memory for memory in memories}
    if "low_average_protein" in memory_by_slug:
        focus.append("Break the low-protein pattern")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="pattern",
            priority="high" if protein_gap > 0 else "medium",
            title="Anchor meals around protein",
            message=f"Recent logs suggest protein is often low. Build each main meal around a reliable protein anchor such as {_protein_examples(user)} before adding sides.",
            rationale=memory_by_slug["low_average_protein"]["summary"],
        )
    if "high_average_meal_calories" in memory_by_slug:
        focus.append("Improve portion awareness")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="pattern",
            priority="medium",
            title="Reduce calorie density per meal",
            message="Recent meals are often calorie-dense. Use one plate-style rule: keep half the plate vegetables, one quarter protein, and one quarter carb-rich staples.",
            rationale=memory_by_slug["high_average_meal_calories"]["summary"],
        )
    if "late_eating_pattern" in memory_by_slug:
        focus.append("Shift calories earlier when possible")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="timing",
            priority="medium",
            title="Front-load more calories earlier",
            message="Late eating appears repeatedly in the logs. If schedule allows, move part of dinner or snacks earlier to reduce end-of-day hunger spikes.",
            rationale=memory_by_slug["late_eating_pattern"]["summary"],
        )

    recurring_flags = [memory for memory in memories if memory["slug"].startswith("flag_")]
    for memory in recurring_flags[:2]:
        flag_name = memory["title"].replace("Recurring nutrition flag: ", "")
        _add_suggestion(
            suggestions,
            seen_titles,
            category="flag",
            priority="medium",
            title=f"Watch recurring flag: {flag_name}",
            message=f"This flag has appeared repeatedly in meal analysis. Use the next meal to actively offset it with a simpler, more balanced choice.",
            rationale=memory["summary"],
        )

    if recent_meal and recent_meal.get("health_flags"):
        recent_flags = ", ".join(recent_meal["health_flags"][:3])
        _add_suggestion(
            suggestions,
            seen_titles,
            category="meal_feedback",
            priority="medium",
            title="Adjust from the latest meal",
            message=f"The latest logged meal raised these flags: {recent_flags}. Use the next meal to rebalance with more protein, fiber, and less excess energy where possible.",
            rationale="The most recent meal is a strong short-term signal for what to correct next.",
        )

    if not suggestions:
        _add_suggestion(
            suggestions,
            seen_titles,
            category="maintenance",
            priority="low",
            title="Stay consistent with the current pattern",
            message="Today's intake appears reasonably aligned with the estimated target. The main recommendation is to keep logging meals and maintain the same level of balance.",
            rationale="No strong corrective signal was detected from today’s stats or active memory patterns.",
        )

    memory_signals = [memory["summary"] for memory in memories[:5]]
    focus = list(dict.fromkeys(focus))[:5]
    return {
        "user_id": user_id,
        "date": stats["date"],
        "goal": user.get("goal"),
        "calorie_target": calorie_target,
        "protein_target_g": protein_target,
        "total_calories": stats["total_calories"],
        "total_protein_g": stats["total_protein_g"],
        "meal_count": stats["meal_count"],
        "overview": _build_overview(stats, calorie_target, protein_target, user, len(memories)),
        "focus": focus,
        "memory_signals": memory_signals,
        "suggestions": suggestions[:6],
    }
