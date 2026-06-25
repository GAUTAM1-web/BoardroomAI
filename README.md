<<<<<<< HEAD
# Boardroom AI

Boardroom AI is an AI-powered executive operating system for founders. A founder submits a startup brief, and the system convenes an AI board meeting where executive agents debate, revise, vote, and produce an investor-grade operating report.

This repository is organized as a production-oriented monorepo:

- `backend/` - FastAPI, domain orchestration, PostgreSQL models, Alembic migrations.
- `frontend/` - Next.js, TypeScript, Tailwind CSS, shadcn-style primitives, Framer Motion, TanStack Query, Zustand.
- `docs/` - architecture, data model, API contract, AI system design, and milestone roadmap.
- `infra/` - infrastructure notes and future Kubernetes-ready boundaries.

## Milestone 1

Milestone 1 delivers a runnable vertical slice:

- founder brief intake contract
- deterministic executive board orchestration
- 18 executive roles with independent goals, personalities, confidence, dissent, revisions, and votes
- structured report containing every required Boardroom AI output section
- FastAPI routes for health, roles, and board meeting generation
- premium dark-mode Next.js experience wired to the backend API
- PostgreSQL-only schema design and Alembic migration
- Docker Compose for PostgreSQL, Redis, Qdrant, backend, and frontend
- unit tests for board orchestration behavior

## Milestone 2

Milestone 2 turns the board from a static simulation into a live meeting:

- WebSocket streaming board meetings at `/api/v1/board-meetings/live`
- executive status events such as thinking, researching, calculating, and reviewing
- meeting-scoped executive memory with natural references to earlier arguments
- provisional votes, final votes, and visible vote changes
- confidence history with reasons for each change
- chronological timeline statements with speaker, time, topic, role, confidence, reasoning, and memory references
- streamed report sections that appear one at a time
- PostgreSQL persistence for meetings, timeline turns, raw stream events, vote history, confidence history, reports, and reasoning
- futuristic boardroom UI with executive seats, active speaker animation, live transcript, vote changes, confidence evolution, and streaming report panels

## Quickstart

Copy the environment file:

```powershell
Copy-Item .env.example .env
```

Start the full stack:

```powershell
docker compose up --build
```

Or use the local helper:

```powershell
.\scripts\dev.ps1
```

Backend:

```text
http://localhost:8000
```

Frontend:

```text
http://localhost:3000
```

Run backend tests from `backend/`:

```powershell
python -m pytest
```

The local development URLs are:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Backend API docs: `http://localhost:8000/docs`
- Live board WebSocket: `ws://localhost:8000/api/v1/board-meetings/live`

## Engineering Decisions

The first implementation uses a deterministic local AI provider for repeatable offline development and tests. The provider is not mock logic: it evaluates the founder brief through role-specific strategic heuristics, generates disagreement, produces revisions, and computes consensus. The provider abstraction is designed so OpenAI, Claude, Gemini, and Ollama implementations can be added without changing the domain orchestration.

PostgreSQL is the only relational database target. SQLite is intentionally not used in runtime or tests.

