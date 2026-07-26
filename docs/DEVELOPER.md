# Developer Guide

## Local Setup

```powershell
Copy-Item .env.example .env
docker compose up -d
```

Backend:

```powershell
cd backend
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
```

Frontend:

```powershell
cd frontend
npm run dev
npm run typecheck
npm run lint
npm run build
```

## App Entry Points

- `/` is the public landing page.
- `/workspace` is the authenticated workspace.
- `/workspace?auth=demo` opens the recruiter demo.
- `/meeting` remains a compatibility route and loads the same workspace.
- Electron loads `/workspace` from the local Next.js server.

## Compatibility Rules

- Keep all existing `/api/v1/*` paths stable.
- Additive auth and diagnostics routes must not gate existing single-user APIs.
- Desktop mode must work with either the local Docker backend or a configured remote backend.
- Provider failures should return warnings and diagnostics, not crashes or fabricated evidence.

## Demo Data

Default workspaces seed portfolio content when `DEMO_CONTENT_ENABLED=true`. The seed is idempotent
and uses normal database records, so dashboard, enterprise, history, reports, approvals, tasks, and
business-analysis screens all consume the same APIs as user-created data.
