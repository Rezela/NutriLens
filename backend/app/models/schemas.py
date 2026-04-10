from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class UserProfileCreate(BaseModel):
    name: str
    age: int | None = None
    sex: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    activity_level: str | None = None
    goal: str | None = None
    dietary_preferences: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)


class UserProfileUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    sex: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    activity_level: str | None = None
    goal: str | None = None
    dietary_preferences: list[str] | None = None
    dietary_restrictions: list[str] | None = None


class UserProfileResponse(UserProfileCreate):
    id: str
    created_at: str
    updated_at: str


class MealItem(BaseModel):
    name: str
    estimated_portion: str | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None


class MealAnalysisResult(BaseModel):
    meal_name: str
    description: str | None = None
    estimated_calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    items: list[MealItem] = Field(default_factory=list)
    confidence: str | None = None
    health_flags: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    reasoning_summary: str | None = None


class MealAnalysisResponse(BaseModel):
    analysis: MealAnalysisResult
    saved_meal_id: str | None = None


class MealLogResponse(MealAnalysisResult):
    id: str
    user_id: str | None = None
    image_path: str | None = None
    source_notes: str | None = None
    meal_time: str
    created_at: str


class DailyNutritionStats(BaseModel):
    user_id: str
    date: str
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    meal_count: int


class MemoryRecordResponse(BaseModel):
    id: str
    user_id: str
    memory_type: str
    slug: str
    title: str
    summary: str
    details: str | None = None
    source_kind: str | None = None
    confidence: str | None = None
    is_active: bool
    created_at: str
    updated_at: str


class MemoryRefreshResponse(BaseModel):
    user_id: str
    memory_count: int
    archived_count: int
    used_llm: bool
    llm_error: str | None = None
    manifest_path: str
    memories: list[MemoryRecordResponse] = Field(default_factory=list)


class MemoryManifestResponse(BaseModel):
    user_id: str
    manifest_path: str
    manifest: str


class RecommendationSuggestion(BaseModel):
    category: str
    priority: str
    title: str
    message: str
    rationale: str


class DailyRecommendationResponse(BaseModel):
    user_id: str
    date: str
    goal: str | None = None
    calorie_target: float
    protein_target_g: float
    total_calories: float
    total_protein_g: float
    meal_count: int
    overview: str
    focus: list[str] = Field(default_factory=list)
    memory_signals: list[str] = Field(default_factory=list)
    suggestions: list[RecommendationSuggestion] = Field(default_factory=list)
