# NutriLens Backend Process Log

## Project Scope

- Build a lightweight backend-first MVP for NutriLens.
- Use Gemini as the initial remote multimodal model.
- Focus first on `image -> analysis -> meal log -> memory -> daily stats`.

## Current Architecture

- `FastAPI` for API layer
- `SQLite` for MVP persistence
- `Vertex AI Gemini` for meal image analysis and optional LLM-backed memory refresh
- `storage/uploads` for uploaded images
- `storage/memory/{user_id}` for exported memory snapshot files
- `React + Vite` frontend consuming backend user, meal, stats, and recommendation endpoints for local integration testing

## Environment Setup

```bash
conda activate GenAI
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Required environment variables:

- `GEMINI_MODEL`
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `DATABASE_URL`
- `UPLOAD_DIR`
- `MEMORY_DIR`

## Implemented Features

### Backend scaffold

- FastAPI app entrypoint
- CORS config
- SQLite initialization
- User profile CRUD
- Meal analysis endpoint
- Meal log listing
- Daily nutrition stats
- Vertex AI service-account-based Gemini authentication

### Memory v1

- `memories` table in SQLite
- Deterministic memory extraction from user profile and recent meals
- Optional Gemini-assisted memory refresh
- Per-user `MEMORY.md` snapshot export inspired by ClaudeCode manifest/index pattern
- Memory API endpoints for refresh, listing, and manifest export
- Automatic memory refresh after user profile creation/update
- Automatic deterministic memory refresh after saving a meal for a known user

### Recommendation v1

- Deterministic daily recommendation service built on top of existing profile, meal, stats, and memory data
- Personalized calorie and protein target estimation based on user attributes and goal
- Ranked suggestion output with overview, focus items, and explicit rationale
- No extra LLM dependency required for base personalized recommendation output

### Frontend integration

- Shared frontend API client in `frontend/src/lib/nutrilens.ts` for users, meal stats, meal logs, meal analysis, and daily recommendations
- Onboarding now syncs the normalized local profile into backend user records and persists the returned `user_id`
- Dashboard now reads backend daily stats, recent meal logs, and recommendation output instead of relying only on mock data
- Dashboard summary now prefers backend recommendation calorie/protein targets when available to keep UI targets aligned with backend personalization
- Dashboard information hierarchy now emphasizes `Today overview -> Next best actions -> Recently logged`, with promotional content pushed lower in the page
- Macro cards now show explicit target values and bounded progress for faster scanning of daily nutrition status
- Recommendation card now surfaces memory signals and suggestion rationale for clearer coaching context
- Camera capture / gallery upload in the dashboard now calls the live meal analysis endpoint and refreshes dashboard state after save
- Local integration flow validated with Vite on `http://localhost:8080` and FastAPI on `http://127.0.0.1:8000`

## Current API Surface

- `GET /health`
- `GET /health/gemini`
- `POST /api/v1/users`
- `PUT /api/v1/users/{user_id}`
- `GET /api/v1/users/{user_id}`
- `POST /api/v1/meals/analyze`
- `GET /api/v1/meals?user_id=...`
- `GET /api/v1/meals/stats/daily?user_id=...&date=YYYY-MM-DD`
- `GET /api/v1/memories?user_id=...`
- `POST /api/v1/memories/refresh?user_id=...&use_llm=false`
- `GET /api/v1/memories/manifest/{user_id}`
- `GET /api/v1/recommendations/daily?user_id=...&date=YYYY-MM-DD`

## ClaudeCode-inspired Design Notes

- Keep memory records structured and typed rather than storing arbitrary chat history
- Scan/update existing memories instead of only appending new ones
- Separate memory index (`MEMORY.md`) from memory detail files
- Favor durable patterns and user-specific constraints over one-off observations

## Current Todo

- Improve memory extraction prompt quality and dedup behavior
- Add basic tests for memory repository and service
- Add frontend tests for onboarding sync, dashboard data loading, and meal analysis upload flows
- Introduce nutrition database grounding instead of model-only estimates

## Open Questions

- How much of memory refresh should be synchronous vs background?
- Should meal analysis always trigger LLM memory refresh, or only deterministic refresh by default?
- What memory taxonomy best fits nutrition coaching in later versions?
- How much onboarding data should be moved from local-only calculation into backend-managed profile fields in the next iteration?

## Change Log

### 2026-04-16

- Integrated the React frontend onboarding flow with backend user creation/update
- Wired dashboard daily stats, recent meals, and live meal image analysis to the FastAPI backend
- Added frontend consumption of the deterministic daily recommendation endpoint in the dashboard
- Aligned dashboard calorie/protein targets with backend recommendation output and exposed richer recommendation details in the UI
- Reworked dashboard information architecture to prioritize daily overview, next actions, and recent logs over promotional content
- Added frontend `.env.example` and README instructions for `VITE_API_BASE_URL` local API routing
- Verified local frontend build after the new integration changes

### 2026-04-10

- Initialized backend scaffold under `NutriLens/backend`
- Added Gemini-based multimodal meal analysis flow
- Added SQLite user and meal persistence
- Added memory v1 architecture and process log
- Added automatic memory refresh wiring for user and meal flows
- Added deterministic recommendation v1 using user profile, stats, meals, and active memories
- Switched backend Gemini authentication plan to Vertex AI + service account
