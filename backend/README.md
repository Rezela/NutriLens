# NutriLens Backend

A lightweight FastAPI backend for NutriLens. The first version uses the Gemini multimodal API to analyze food images and text, stores user profiles, meal logs, and memory records in SQLite, and exposes simple nutrition tracking endpoints.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Set `GEMINI_API_KEY` in `.env`.

Relevant configuration:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `DATABASE_URL`
- `UPLOAD_DIR`
- `MEMORY_DIR`
- `MEMORY_RECENT_MEAL_LIMIT`

## Run

```bash
uvicorn app.main:app --reload
```

## Development notes

- Ongoing process log: `docs/process-log.md`
- Memory snapshot export directory: `storage/memory/{user_id}/`

## Main endpoints

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
- `GET /api/v1/recommendations/daily?user_id=...&date=YYYY-MM-DD`

## Memory v1

Memory v1 is inspired by ClaudeCode's structured memory approach:

- memory is stored as typed records instead of raw chat history
- existing memory is refreshed rather than only appended to
- each user gets a `MEMORY.md` manifest plus per-memory markdown files
- the first implementation combines deterministic extraction with optional Gemini-assisted refinement

## Recommendation v1

Recommendation v1 is deterministic and built on top of the current backend data model:

- consumes `user profile`, `daily stats`, `recent meals`, and `active memories`
- estimates a calorie target and protein target from user attributes and stated goal
- produces a short overview, focus areas, memory signals, and ranked suggestions
- keeps personalized advice available even when no extra LLM call is made
