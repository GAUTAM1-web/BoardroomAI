# Boardroom AI

Boardroom AI is an AI-powered operating system for founders. It turns a startup brief into a live executive board meeting, streams the debate over WebSockets, persists the meeting to PostgreSQL, and generates investor-grade reports with PDF, Markdown, and JSON exports.

## Current Capabilities

- Premium founder dashboard with recent meetings, reports, generated ideas, board decisions, approval rate, average confidence, top industries, filters, and global search.
- AI startup idea generator with interests, industry, country, budget, business model, funding stage, and idea count controls.
- Startup idea cards with name, tagline, problem, solution, audience, revenue model, startup cost, TAM, innovation, scalability, difficulty, advantage, and success probability.
- One-click launch from a generated idea into a live board meeting.
- Manual founder brief creation remains available.
- Live boardroom with 18 executive roles, active speaker indicators, status animation, confidence changes, vote changes, timeline, risk signals, and streamed report sections.
- Smarter deterministic executive debate with challenges, agreement, disagreement, follow-up questions, pivots, partnerships, risk discovery, and references to prior discussion.
- Professional board report after every meeting, including executive summary, startup overview, executive opinions, SWOT, competitors, market analysis, financial analysis, risk matrix, action plan, VC readiness scores, vote detail, and confidence scores.
- History for previous meetings with search, filters, favorites, compare, report preview, relaunch, delete, and re-download.
- Export support for PDF, Markdown, and JSON.
- Dockerized FastAPI, Next.js, PostgreSQL, Redis, and Qdrant stack.

## Stack

Frontend:

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Framer Motion
- Zustand

Backend:

- FastAPI
- Python 3.12
- PostgreSQL
- Redis
- Qdrant
- WebSockets
- SQLAlchemy and Alembic

## Quickstart

Copy the environment file:

```powershell
Copy-Item .env.example .env
```

Start the full containerized stack:

```powershell
docker compose up -d
```

For local frontend development:

```powershell
cd frontend
npm run dev
```

For local backend development, use the same root `.env` file. The backend now reads both
`./.env` and `backend/.env`, so running from either the repo root or `backend/` uses the
same database settings.

Local URLs:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Backend API docs: `http://localhost:8000/docs`
- Live board WebSocket: `ws://localhost:8000/api/v1/board-meetings/live`

### API Routing Notes

The frontend supports two HTTP API modes:

- Default local/Docker mode: leave `NEXT_PUBLIC_API_BASE_URL` empty and let Next.js proxy
  `/api/v1/*` to `API_INTERNAL_BASE_URL`.
- Direct-browser mode: set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` if you want
  browser requests to bypass the Next.js proxy.

WebSockets use `NEXT_PUBLIC_WS_BASE_URL`, defaulting to `ws://localhost:8000`.

## Usage

1. Open the dashboard to review meeting history, approval rate, confidence, reports, and industry activity.
2. Use Startup Generator to create startup cards from a short prompt or structured inputs.
3. Launch a board meeting from a generated card, or open Boardroom and submit a manual founder brief.
4. Watch the live executive discussion, vote changes, confidence evolution, risk signals, and report stream.
5. Open History to search meetings, favorite startups, compare decisions, preview reports, relaunch a brief, delete history, or export artifacts.

## API Highlights

- `GET /health`
- `GET /api/v1/executives`
- `POST /api/v1/startup-ideas/generate`
- `POST /api/v1/board-meetings`
- `GET /api/v1/board-meetings`
- `GET /api/v1/board-meetings/{meeting_id}`
- `PATCH /api/v1/board-meetings/{meeting_id}/favorite`
- `DELETE /api/v1/board-meetings/{meeting_id}`
- `GET /api/v1/dashboard`
- `GET /api/v1/search?q=...`
- `GET /api/v1/reports/{meeting_id}/export?format=pdf`
- `GET /api/v1/reports/{meeting_id}/export?format=markdown`
- `GET /api/v1/reports/{meeting_id}/export?format=json`
- `WS /api/v1/board-meetings/live`

## Validation

Backend tests:

```powershell
cd backend
python -m pytest
```

Frontend typecheck:

```powershell
cd frontend
npm run typecheck
```

Production frontend build:

```powershell
cd frontend
npm run build
```

Frontend lint:

```powershell
cd frontend
npm run lint
```

## Engineering Notes

The current AI provider is deterministic by design. It gives repeatable tests and a fully functional offline development flow while preserving the provider abstraction for OpenAI, Claude, Gemini, Ollama, or other model-backed providers.

PostgreSQL remains the system of record for meetings, votes, confidence events, timeline turns, report sections, favorites, and exportable artifacts. Docker Compose remains the default development workflow.

## Stabilization Notes

- Fixed dashboard/history API routing ambiguity. Root cause: browser-side `/api/v1/*`
  requests could hit Next.js instead of FastAPI when the public API base URL was empty
  or misconfigured. Fix: added a Next.js rewrite proxy and centralized URL construction
  in `frontend/lib/api.ts`.
- Fixed opaque frontend API errors. Root cause: failed requests collapsed into generic
  messages such as "Failed to fetch." Fix: API helpers now include status codes and
  backend details.
- Fixed Docker frontend API wiring. Root cause: public browser env vars are build-time
  values in Next.js, while container-to-container traffic needs the internal `backend`
  hostname. Fix: Docker build args now separate `API_INTERNAL_BASE_URL` from public
  browser URLs.
- Fixed broken frontend lint gate. Root cause: `next lint` is deprecated and prompted
  interactively. Fix: added `eslint.config.mjs` and switched to `eslint . --max-warnings=0`.
- Fixed stale typecheck failures. Root cause: TypeScript incremental state could point
  at generated `.next/types` files. Fix: `npm run typecheck` disables incremental reads.
- Improved database failure handling. Root cause: asyncpg connection errors could escape
  as 500 responses. Fix: repository-backed routes return 503 with actionable setup detail.
- Improved delete reliability. Root cause: ORM relationships did not declare cascade
  behavior matching the database foreign keys. Fix: added delete-orphan cascade and
  passive deletes for meeting/report children.
- Added API contract tests for dashboard, history, favorites, delete, search, and export
  route methods.
- No new runtime dependencies were added.
