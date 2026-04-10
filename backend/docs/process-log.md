# NutriLens Backend Process Log

## Project Scope

- Build a lightweight backend-first MVP for NutriLens.
- Use Gemini as the initial remote multimodal model.
- Focus first on `image -> analysis -> meal log -> memory -> daily stats`.

## Current Architecture

- `FastAPI` for API layer
- `SQLite` for MVP persistence
- `Gemini API` for meal image analysis
- `storage/uploads` for uploaded images
- `storage/memory/{user_id}` for exported memory snapshot files

## Environment Setup

```bash
conda activate GenAI
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Required environment variables:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
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

### Memory v1

- `memories` table in SQLite
- Deterministic memory extraction from user profile and recent meals
- Optional Gemini-assisted memory refresh
- Per-user `MEMORY.md` snapshot export inspired by ClaudeCode manifest/index pattern
- Memory API endpoints for refresh, listing, and manifest export
- Automatic memory refresh after user profile creation/update
- Automatic deterministic memory refresh after saving a meal for a known user

## Current API Surface

- `GET /health`
- `POST /api/v1/users`
- `PUT /api/v1/users/{user_id}`
- `GET /api/v1/users/{user_id}`
- `POST /api/v1/meals/analyze`
- `GET /api/v1/meals?user_id=...`
- `GET /api/v1/meals/stats/daily?user_id=...&date=YYYY-MM-DD`
- `GET /api/v1/memories?user_id=...`
- `POST /api/v1/memories/refresh?user_id=...&use_llm=false`
- `GET /api/v1/memories/manifest/{user_id}`

## ClaudeCode-inspired Design Notes

- Keep memory records structured and typed rather than storing arbitrary chat history
- Scan/update existing memories instead of only appending new ones
- Separate memory index (`MEMORY.md`) from memory detail files
- Favor durable patterns and user-specific constraints over one-off observations

## Current Todo

- Improve memory extraction prompt quality and dedup behavior
- Refresh memories automatically on user profile updates and meal saves
- Add basic tests for memory repository and service
- Add recommendation module based on user goal + meal patterns
- Introduce nutrition database grounding instead of model-only estimates

## Open Questions

- How much of memory refresh should be synchronous vs background?
- Should meal analysis always trigger LLM memory refresh, or only deterministic refresh by default?
- What memory taxonomy best fits nutrition coaching in later versions?

## Change Log

### 2026-04-10

- Initialized backend scaffold under `NutriLens/backend`
- Added Gemini-based multimodal meal analysis flow
- Added SQLite user and meal persistence
- Added memory v1 architecture and process log
- Added automatic memory refresh wiring for user and meal flows
