# NexCraft Solutions - AI Sales OS — Setup Guide

## Prerequisites

- **Python 3.11** (3.12+/3.14 may fail installing `pydantic-core`; 3.11 is confirmed working)
- **Node.js 20+** and npm
- **PostgreSQL 14+** running locally (or reachable via a connection string)
- **Docker Desktop** (only needed if you want the n8n automation/scheduling piece — optional for just using the app manually)
- API keys: at least one of **OpenAI** or **Anthropic** (the app auto-fails-over between them), plus **Google Places API** key for lead discovery

## 1. Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements.txt
```

Create the database, then copy the env template and fill in your values:

```bash
createdb nexcraft_salesos
cp .env.example .env
```

Edit `backend/.env` and fill in: `DATABASE_URL`, `GOOGLE_PLACES_API_KEY`, and at least one of `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`. SMTP/IMAP are only needed for real email sending/receiving.

Also set `API_KEY` to a random secret (`python -c "import secrets; print(secrets.token_urlsafe(32))"`). Every request to the API must include it as an `X-API-Key` header; leaving it blank disables auth for quick local testing.

Run migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Backend should now be live at `http://127.0.0.1:8000` (docs at `/docs`).

## 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev -- -p 3500
```

Set `NEXT_PUBLIC_API_KEY` in `frontend/.env.local` to the same value as `backend/.env`'s `API_KEY`.

Open `http://localhost:3500`.

## 3. n8n (optional — scheduling/automation only)

Only needed if you want automated lead discovery / inbox polling on a schedule. Requires Docker Desktop.

```bash
cd n8n
cp .env.example .env
npm install
npx n8n start
```

Without n8n, everything still works — just trigger each action manually from the UI (e.g. "Check Inbox Now", "Search Now") instead of on a timer.

## 4. Or: run everything with Docker

Requires Docker Desktop. This starts Postgres, the backend, and the frontend together (n8n is not included — run it separately per step 3 if you want scheduling).

```bash
cp backend/.env.example backend/.env   # fill in your keys, including API_KEY
cp .env.example .env                   # set API_KEY to match backend/.env
docker compose up --build
```

Frontend at `http://localhost:3500`, backend at `http://localhost:8000`. Migrations run automatically on backend startup.

## Notes

- Never commit `.env` / `.env.local` — they're gitignored on purpose.
- `backend/requirements.txt` has pinned versions, so `pip install -r requirements.txt` reproduces the exact environment this was built and tested against.
- Run `python -m pytest -q` inside `backend/` (with the venv active) to confirm the backend is healthy before using it.
- `.github/workflows/ci.yml` runs the backend test suite and the frontend build automatically on every push/PR once this is on GitHub.
- The Docker images build correctly (`next build` and `pip install` were verified locally) but the full `docker compose up` was not run end-to-end in the environment this was built in (no working Docker daemon there) — verify it once on your machine.
