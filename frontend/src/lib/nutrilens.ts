const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const API_V1_BASE_URL = `${API_BASE_URL}/api/v1`;
const STORAGE_USER_ID_KEY = "nutrilensUserId";

export type StoredGoal = "lose-weight" | "maintain" | "gain-weight";
export type StoredGender = "male" | "female" | "other";
export type StoredWorkoutFrequency = "0-2" | "3-5" | "6+";

export interface StoredUserProfile {
  userId: string | null;
  name: string;
  age: number | null;
  sex: StoredGender | null;
  heightCm: number | null;
  weightKg: number | null;
  activityLevel: string | null;
  goal: StoredGoal | null;
  birthday: string | null;
  targetCalories: number | null;
  targetProtein: number | null;
  targetCarbs: number | null;
  targetFats: number | null;
  targetWeight: number | null;
  targetDate: string | null;
}

export interface UserProfileResponse {
  id: string;
  name: string;
  age: number | null;
  sex: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  activity_level: string | null;
  goal: string | null;
  dietary_preferences: string[];
  dietary_restrictions: string[];
  created_at: string;
  updated_at: string;
}

export interface MealItem {
  name: string;
  estimated_portion?: string | null;
  calories?: number | null;
  protein_g?: number | null;
  carbs_g?: number | null;
  fat_g?: number | null;
}

export interface MealAnalysisResult {
  meal_name: string;
  description?: string | null;
  estimated_calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  items: MealItem[];
  confidence?: string | null;
  health_flags: string[];
  follow_up_questions: string[];
  reasoning_summary?: string | null;
}

export interface MealAnalysisResponse {
  analysis: MealAnalysisResult;
  saved_meal_id: string | null;
}

export interface MealLogResponse extends MealAnalysisResult {
  id: string;
  user_id: string | null;
  image_path: string | null;
  source_notes: string | null;
  meal_time: string;
  created_at: string;
}

export interface DailyNutritionStats {
  user_id: string;
  date: string;
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
  meal_count: number;
}

export interface RecommendationSuggestion {
  category: string;
  priority: string;
  title: string;
  message: string;
  rationale: string;
}

export interface DailyRecommendationResponse {
  user_id: string;
  date: string;
  goal: string | null;
  calorie_target: number;
  protein_target_g: number;
  total_calories: number;
  total_protein_g: number;
  meal_count: number;
  overview: string;
  focus: string[];
  memory_signals: string[];
  suggestions: RecommendationSuggestion[];
}

function readStorageNumber(key: string): number | null {
  const rawValue = localStorage.getItem(key);
  if (!rawValue) {
    return null;
  }
  const parsed = Number(rawValue);
  return Number.isFinite(parsed) ? parsed : null;
}

function readStorageString<T extends string>(key: string): T | null {
  const rawValue = localStorage.getItem(key);
  return rawValue ? (rawValue as T) : null;
}

function calculateAge(birthYear: number | null, birthMonth: number | null, birthDay: number | null): number | null {
  if (!birthYear || !birthMonth || !birthDay) {
    return null;
  }

  const today = new Date();
  let age = today.getFullYear() - birthYear;
  const hasBirthdayPassed = today.getMonth() + 1 > birthMonth || (today.getMonth() + 1 === birthMonth && today.getDate() >= birthDay);

  if (!hasBirthdayPassed) {
    age -= 1;
  }

  return age >= 0 ? age : null;
}

function buildBirthdayString(birthYear: number | null, birthMonth: number | null, birthDay: number | null): string | null {
  if (!birthYear || !birthMonth || !birthDay) {
    return null;
  }

  const month = String(birthMonth).padStart(2, "0");
  const day = String(birthDay).padStart(2, "0");
  return `${birthYear}-${month}-${day}`;
}

function mapActivityLevel(workoutFrequency: StoredWorkoutFrequency | null): string | null {
  if (!workoutFrequency) {
    return null;
  }

  if (workoutFrequency === "0-2") {
    return "light";
  }
  if (workoutFrequency === "3-5") {
    return "moderate";
  }
  return "active";
}

async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_V1_BASE_URL}${path}`, init);

  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;

    try {
      const errorPayload = await response.json();
      if (typeof errorPayload?.detail === "string") {
        message = errorPayload.detail;
      }
    } catch {
      const rawText = await response.text();
      if (rawText) {
        message = rawText;
      }
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function getStoredUserProfile(): StoredUserProfile {
  const birthYear = readStorageNumber("userBirthYear");
  const birthMonth = readStorageNumber("userBirthMonth");
  const birthDay = readStorageNumber("userBirthDay");
  const workoutFrequency = readStorageString<StoredWorkoutFrequency>("userWorkoutFrequency");

  return {
    userId: localStorage.getItem(STORAGE_USER_ID_KEY),
    name: localStorage.getItem("userName") || "NutriLens User",
    age: calculateAge(birthYear, birthMonth, birthDay),
    sex: readStorageString<StoredGender>("userGender"),
    heightCm: readStorageNumber("userHeight"),
    weightKg: readStorageNumber("userWeight"),
    activityLevel: mapActivityLevel(workoutFrequency),
    goal: readStorageString<StoredGoal>("userGoal"),
    birthday: buildBirthdayString(birthYear, birthMonth, birthDay),
    targetCalories: readStorageNumber("targetCalories"),
    targetProtein: readStorageNumber("targetProtein"),
    targetCarbs: readStorageNumber("targetCarbs"),
    targetFats: readStorageNumber("targetFats"),
    targetWeight: readStorageNumber("goalTargetWeight"),
    targetDate: localStorage.getItem("goalTargetDate"),
  };
}

export function setStoredUserId(userId: string): void {
  localStorage.setItem(STORAGE_USER_ID_KEY, userId);
}

export async function syncUserProfileFromStorage(): Promise<UserProfileResponse> {
  const storedProfile = getStoredUserProfile();
  const payload = {
    name: storedProfile.name,
    age: storedProfile.age,
    sex: storedProfile.sex,
    height_cm: storedProfile.heightCm,
    weight_kg: storedProfile.weightKg,
    activity_level: storedProfile.activityLevel,
    goal: storedProfile.goal,
    dietary_preferences: [],
    dietary_restrictions: [],
  };

  const response = storedProfile.userId
    ? await apiRequest<UserProfileResponse>(`/users/${storedProfile.userId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
    : await apiRequest<UserProfileResponse>("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

  setStoredUserId(response.id);
  return response;
}

export async function fetchDailyNutritionStats(userId: string, date: string): Promise<DailyNutritionStats> {
  const params = new URLSearchParams({ user_id: userId, date });
  return apiRequest<DailyNutritionStats>(`/meals/stats/daily?${params.toString()}`);
}

export async function fetchDailyRecommendation(userId: string, date: string): Promise<DailyRecommendationResponse> {
  const params = new URLSearchParams({ user_id: userId, date });
  return apiRequest<DailyRecommendationResponse>(`/recommendations/daily?${params.toString()}`);
}

export async function fetchMealLogs(userId: string): Promise<MealLogResponse[]> {
  const params = new URLSearchParams({ user_id: userId });
  return apiRequest<MealLogResponse[]>(`/meals?${params.toString()}`);
}

export async function analyzeMealImage(options: {
  image: File;
  userId?: string | null;
  notes?: string;
  mealTime?: string;
  saveResult?: boolean;
}): Promise<MealAnalysisResponse> {
  const formData = new FormData();
  formData.append("image", options.image);

  if (options.userId) {
    formData.append("user_id", options.userId);
  }
  if (options.notes) {
    formData.append("notes", options.notes);
  }
  if (options.mealTime) {
    formData.append("meal_time", options.mealTime);
  }
  if (typeof options.saveResult === "boolean") {
    formData.append("save_result", String(options.saveResult));
  }

  return apiRequest<MealAnalysisResponse>("/meals/analyze", {
    method: "POST",
    body: formData,
  });
}
