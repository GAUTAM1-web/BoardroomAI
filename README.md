# Boardroom AI

Boardroom AI is an AI-powered operating system for founders. It turns a startup brief into a live executive board meeting, streams the debate over WebSockets, persists the meeting to PostgreSQL, and generates investor-grade reports with PDF, Markdown, and JSON exports.

Milestone 5 expands the product into an evidence-based business decision platform for technology startups, local businesses, service businesses, shop/location evaluation, supplier planning, validation, and post-launch performance review.

Milestone 6 upgrades the board itself into an evidence-first executive intelligence layer with permanent executive personalities, dynamic meeting modes, devil's advocate review, confidence timelines, replayable decisions, and final decision briefs. Executive Intelligence Engine V2 adds silent internal research, a staged reasoning pipeline, debate trees, confidence propagation, counterfactuals, scenario simulation, cognitive-bias detection, AI reflection, and a decision journal.

## Current Capabilities

- Premium founder dashboard with recent meetings, reports, generated ideas, board decisions, approval rate, average confidence, top industries, filters, and global search.
- AI startup idea generator with interests, industry, country, budget, business model, funding stage, and idea count controls.
- Startup idea cards with name, tagline, problem, solution, audience, revenue model, startup cost, TAM, innovation, scalability, difficulty, advantage, and a legacy heuristic score that is not a guarantee.
- One-click launch from a generated idea into a live board meeting.
- Manual founder brief creation remains available.
- Live boardroom with 19 executive roles, including a permanent Risk Officer devil's advocate, active speaker indicators, status animation, confidence changes, vote changes, timeline, risk signals, and streamed report sections.
- Dynamic meeting modes: full board, quick review, emergency meeting, investor pitch, expansion review, pivot review, acquisition review, and crisis meeting.
- Relevant specialist seats can join a meeting when the brief calls for them, such as medical, compliance, cloud, AI, pricing, inventory, store operations, chef, food safety, and supply-chain specialists.
- Smarter deterministic executive debate with role personalities, reasoning styles, challenges, agreement, disagreement, follow-up questions, pivots, partnerships, risk discovery, memory references, and non-repetitive critique.
- Professional board report after every meeting, including internal research, reasoning pipeline, evidence packet, strategic options A/B/C, decision matrix, counterfactual analysis, scenario simulator, cognitive-bias detection, executive challenge questions, dynamic expert roster, confidence propagation, debate tree, boardroom timeline, meeting replay, executive scorecards, executive performance tracking, decision explainability, validation plan, AI reflection, decision journal, and final decision brief.
- History for previous meetings with search, filters, favorites, compare, report preview, relaunch, delete, and re-download.
- Export support for PDF, Markdown, and JSON.
- Professional Settings workspace with provider status, maps status, redacted API-key posture, theme preference, data-mode status, export defaults, and client diagnostics.
- Evidence-based "Decide" workspace for local shops, service businesses, existing businesses, candidate properties, and startup concepts.
- Optional location flow with manual entry, current-location permission only after user action, map-pin coordinate support, and no background tracking.
- Manual/demo/live provider modes for competitors, suppliers, locations, and evidence. Demo mode is labeled `Demo data - not live local evidence`.
- Explainable Opportunity Score, supplier/procurement plan, opening inventory, editable finance assumptions, daily-sales targets, validation plan, and board-ready brief.
- Business analysis history, evidence records, saved suppliers, validation tasks, performance entries, and weekly board-review scaffolding.
- Dockerized FastAPI, Next.js, PostgreSQL, Redis, and Qdrant stack.
- Windows desktop shell powered by Electron with custom icon, splash screen, About dialog, production window, installer target, and portable executable target.

## Stack

Frontend:

- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- Framer Motion
- Zustand
- Electron and Electron Builder for Windows desktop packaging

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

### Business Evidence Provider Notes

The business-intelligence workflow supports three data modes:

- `demo`: uses labeled benchmark scaffolding only and returns `Demo data - not live local evidence`.
- `manual`: uses competitors, suppliers, quotations, observations, locations, and costs entered by the user.
- `live`: reserved for configured provider credentials; if credentials are missing, the API returns actionable warnings instead of fake listings.

Environment variables:

```text
BUSINESS_DATA_MODE=demo
MAPS_PROVIDER=none
MAPS_API_KEY=
PLACES_API_KEY=
```

Provider secrets stay on the backend. The frontend never needs map or place-search API keys.

## Usage

1. Open the dashboard to review meeting history, approval rate, confidence, reports, and industry activity.
2. Use Startup Generator to create startup cards from a short prompt or structured inputs.
3. Open Decide to analyze a local business, shop/property, service business, operating business, or technology startup using evidence and assumptions.
4. Launch a board meeting from a generated card or evidence brief, or open Boardroom, choose a meeting mode, and submit a manual founder brief.
5. Watch the live executive discussion, vote changes, confidence evolution, risk signals, and report stream.
6. Open History to search meetings, favorite startups, compare decisions, preview reports, relaunch a brief, delete history, or export artifacts.

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
- `GET /api/v1/business-data/providers`
- `POST /api/v1/business-analyses`
- `GET /api/v1/business-analyses`
- `GET /api/v1/business-analyses/{analysis_id}`
- `GET /api/v1/business-analyses/{analysis_id}/export?format=pdf`
- `POST /api/v1/business-analyses/{analysis_id}/performance-entries`
- `POST /api/v1/business-analyses/{analysis_id}/board-review`
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

## Desktop Mode

The desktop application packages the existing Next.js frontend in an Electron shell. It starts a local Next server on `127.0.0.1:3010`, shows a branded splash screen while the server becomes reachable, opens Boardroom AI in a native window, and disables DevTools shortcuts in packaged production builds.

Desktop packaging does not bundle PostgreSQL, Redis, Qdrant, or the FastAPI backend. Run the backend stack locally or configure the desktop environment to point at a reachable backend before using live board meetings, history, exports, or business intelligence.

Build the Windows installer and portable executable:

```powershell
cd frontend
npm run desktop:pack
```

Expected release artifacts:

```text
frontend/release/Boardroom AI-Setup-1.0.0-rc.1.exe
frontend/release/Boardroom AI-Portable-1.0.0-rc.1.exe
```

Generate an unpacked app directory for smoke testing:

```powershell
cd frontend
npm run desktop:dir
```

Development desktop shell:

```powershell
cd frontend
npm run desktop:dev
```

Desktop release metadata:

- Product name: `Boardroom AI`
- App ID: `com.boardroomai.desktop`
- Executable name: `BoardroomAI`
- Version: `1.0.0-rc.1`
- Build config: `frontend/electron-builder.yml`
- Icon source: `frontend/public/boardroom-mark.svg`
- Generated icons: `frontend/electron/build/icon.png` and `frontend/electron/build/icon.ico`

## Engineering Notes

The current AI provider is deterministic by design. It gives repeatable tests and a fully functional offline development flow while preserving the provider abstraction for OpenAI, Claude, Gemini, Ollama, or other model-backed providers.

Business intelligence follows the same offline-first rule. Demo mode is clearly labeled, manual mode uses user-entered evidence, and live-provider mode requires backend environment credentials. No provider API keys are exposed in frontend code.

PostgreSQL remains the system of record for meeting modes, meetings, votes, confidence events, timeline turns, report sections, favorites, business analyses, evidence records, suppliers, validation tasks, performance entries, and exportable artifacts. Docker Compose remains the default development workflow.

Production logs are structured JSON through `structlog`. Request logs include method, path, status code, and duration. Startup logs include environment, configured provider names, and data mode. Request bodies, API keys, and provider secrets are not logged.

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
