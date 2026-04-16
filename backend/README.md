# NutriLens Backend

A lightweight FastAPI backend for NutriLens. The current backend uses Vertex AI Gemini for multimodal meal analysis, stores user profiles, meal logs, and memory records in SQLite, and exposes simple nutrition tracking endpoints.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Set your Google Cloud / Vertex AI configuration in `.env`.

Relevant configuration:

- `GEMINI_MODEL`
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `DATABASE_URL`
- `UPLOAD_DIR`
- `MEMORY_DIR`
- `MEMORY_RECENT_MEAL_LIMIT`

For local development with a service account JSON key:

- place the key file outside version control
- set `GOOGLE_APPLICATION_CREDENTIALS` to that JSON path
- ensure Vertex AI is enabled for the target GCP project
- set `GOOGLE_CLOUD_LOCATION=global` to use the Vertex AI global endpoint
- set `GOOGLE_CLOUD_LOCATION=asia-east2` when you want to target the Hong Kong region explicitly
- use `Invoke-RestMethod` or `curl.exe` to test HTTP endpoints on Windows PowerShell

## Run

```bash
uvicorn app.main:app --reload
```

Example health checks on Windows PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/gemini"
```

## Development notes

- Ongoing process log: `docs/process-log.md`
- Memory snapshot export directory: `storage/memory/{user_id}/`
- Gemini auth mode: Vertex AI + service account credentials

## Main endpoints

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
