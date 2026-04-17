# NutriLens

**A Multimodal AI Nutrition Coach for Personalized Dietary Tracking and Guidance**

## Team Members
- **ZHAO Junyi** (21270452) - jzhaocr@connect.ust.hk
- **SHE Xiaojun** (21287259) - xsheaa@connect.ust.hk
- **QIAN kun** (21260720) - kqianae@connect.ust.hk
- **Jason Jonarto** (21269295) - jjonarto@connect.ust.hk

## Tech Stack (Frontend)
- **Framework:** React 18 / Vite
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **Routing:** React Router
- **Data Fetching:** TanStack React Query

## Environment Variables

Copy `.env.example` to `.env.local` and adjust the backend base URL when needed:

```bash
copy .env.example .env.local
```

Available variables:

- `VITE_API_BASE_URL`: base URL for the FastAPI backend. Defaults to `http://127.0.0.1:8000` if omitted.

## How to Run
1. Install dependencies:
   ```bash
   npm install
   ```
2. Configure the backend API URL for local development:
   ```bash
   copy .env.example .env.local
   ```
   The default file already points to the local backend on `http://127.0.0.1:8000`.
3. Make sure the backend is running:
   ```bash
   uvicorn app.main:app --reload
   ```
   By default the frontend calls `/api/v1/users`, `/api/v1/meals`, `/api/v1/meals/analyze`, `/api/v1/meals/stats/daily`, and `/api/v1/recommendations/daily` on the backend base URL.
4. Start the development server:
   ```bash
   npm run dev
   ```

## Local Integration Notes

- Frontend dev server runs on `http://localhost:8080`
- Backend dev server runs on `http://127.0.0.1:8000`
- Onboarding syncs a normalized local profile into the backend and stores the returned `user_id`
- Dashboard reads live meal stats, recent meal logs, meal analysis results, and daily recommendations from the backend
