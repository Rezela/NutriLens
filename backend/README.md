# NutriLens Backend

A lightweight FastAPI backend for NutriLens. The first version uses the Gemini multimodal API to analyze food images and text, stores user profiles and meal logs in SQLite, and exposes simple nutrition tracking endpoints.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Set `GEMINI_API_KEY` in `.env`.

## Run

```bash
uvicorn app.main:app --reload
```

## Main endpoints

- `GET /health`
- `POST /api/v1/users`
- `PUT /api/v1/users/{user_id}`
- `GET /api/v1/users/{user_id}`
- `POST /api/v1/meals/analyze`
- `GET /api/v1/meals?user_id=...`
- `GET /api/v1/meals/stats/daily?user_id=...&date=YYYY-MM-DD`
