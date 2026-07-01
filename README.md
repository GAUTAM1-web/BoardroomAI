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

Local URLs:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- Backend API docs: `http://localhost:8000/docs`
- Live board WebSocket: `ws://localhost:8000/api/v1/board-meetings/live`

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

## Engineering Notes

The current AI provider is deterministic by design. It gives repeatable tests and a fully functional offline development flow while preserving the provider abstraction for OpenAI, Claude, Gemini, Ollama, or other model-backed providers.

PostgreSQL remains the system of record for meetings, votes, confidence events, timeline turns, report sections, favorites, and exportable artifacts. Docker Compose remains the default development workflow.
