# Production Deployment

BoardroomAI can run as a web app, Docker stack, or Windows desktop shell without changing API paths.
The production work keeps `/api/v1/*`, `/health`, and the WebSocket route stable.

## Recommended Targets

- Frontend: Vercel or the `frontend` Docker image.
- Backend: Railway, Render, Fly.io, or the `backend` Docker image.
- Data services: managed PostgreSQL, Redis, and Qdrant for public deployments.
- Local/portfolio demo: `docker compose up -d`.

## Required Environment

Copy `.env.production.example` and set real values:

```text
APP_ENV=production
DEPLOYMENT_TARGET=auto
PUBLIC_FRONTEND_URL=https://your-frontend.example.com
PUBLIC_API_URL=https://your-api.example.com
FRONTEND_BASE_URL=https://your-frontend.example.com
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST:5432/boardroom_ai
REDIS_URL=redis://USER:PASSWORD@HOST:6379/0
QDRANT_URL=https://your-qdrant.example.com
SESSION_SECRET=replace-with-at-least-32-random-characters
API_INTERNAL_BASE_URL=https://your-api.example.com
NEXT_PUBLIC_API_BASE_URL=https://your-api.example.com
NEXT_PUBLIC_WS_BASE_URL=wss://your-api.example.com
```

Provider keys are optional. Missing providers degrade live evidence and appear in diagnostics.

## Frontend Routing

In local and Docker mode, keep `NEXT_PUBLIC_API_BASE_URL` empty and let Next.js proxy
`/api/v1/*` to `API_INTERNAL_BASE_URL`.

In split-host production, set:

```text
NEXT_PUBLIC_API_BASE_URL=https://your-api.example.com
NEXT_PUBLIC_WS_BASE_URL=wss://your-api.example.com
```

This makes browser requests direct and avoids hardcoded localhost in production.

## Demo Mode

Open:

```text
/workspace?auth=demo
```

The demo account signs in as an Administrator. Fresh databases seed a portfolio meeting, report,
approval workflow, tasks, notification, templates, knowledge items, calendar review, and one
business analysis when `DEMO_CONTENT_ENABLED=true`.

Set `DEMO_CONTENT_ENABLED=false` for tenant deployments that should start empty.

## Health And Diagnostics

- `GET /health/live` - process liveness.
- `GET /health/ready` - app readiness and detected deployment target.
- `GET /api/v1/diagnostics/environment` - redacted environment readiness.
- `GET /api/v1/diagnostics/dependencies` - PostgreSQL, Redis, and Qdrant checks.
- `GET /api/v1/diagnostics/providers` - provider health and redacted secret posture.
- `GET /api/v1/diagnostics` - combined payload.

Diagnostics report presence and status only. Secret values are not returned.

## Platform Files

- `vercel.json` builds the frontend from `frontend/`.
- `railway.toml` and `fly.toml` use `Dockerfile.backend`.
- `render.yaml` defines backend and frontend Docker services.
- `docker-compose.prod.yml` runs the full production-shaped stack locally or on a VM.

## Release Gate

```powershell
cd backend
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .

cd ..\frontend
npm run typecheck
npm run lint
npm run build
npm run desktop:pack

cd ..
docker compose config
docker compose -f docker-compose.prod.yml config
docker compose build
```
