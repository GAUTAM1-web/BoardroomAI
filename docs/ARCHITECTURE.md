# Boardroom AI Architecture

## Product Intent

Boardroom AI turns a founder's startup brief into an executive board meeting. The system should feel like an operating system for founders: focused, fast, serious, visually premium, and useful beyond a chat transcript.

## System Boundaries

```text
Founder UI
  -> Next.js application
  -> FastAPI API gateway
  -> Boardroom domain orchestration
  -> AI provider abstraction
  -> PostgreSQL system of record
  -> Redis event/cache layer
  -> Qdrant strategic memory and retrieval layer
```

## Monorepo Structure

```text
backend/
  app/
    api/                  HTTP routes and dependency wiring
    core/                 configuration, logging, app lifecycle
    domain/boardroom/     clean domain model and orchestration
    infrastructure/       database and provider adapters
    schemas/              request and response DTOs
  alembic/                PostgreSQL migrations
  tests/                  unit and contract tests

frontend/
  app/                    Next.js App Router
  components/             boardroom experience and UI primitives
  lib/                    API client, utilities, shared types
  store/                  client-side state

docs/                     architecture, API, roadmap
infra/                    deployment notes and future manifests
```

## Clean Architecture

The board meeting orchestration lives in `backend/app/domain/boardroom` and has no FastAPI, SQLAlchemy, Redis, or Qdrant dependency. Delivery and persistence are adapters around the domain. This keeps the core meeting logic testable and ready for asynchronous execution.

Domain responsibilities:

- normalize founder briefs
- load executive role definitions
- score market, financial, operational, legal, growth, and technology risk
- run proposal, critique, revision, and consensus phases
- produce a structured board report

Application/API responsibilities:

- validate HTTP input
- convert DTOs into domain objects
- call the orchestrator
- return structured JSON
- later persist meetings, turns, votes, report sections, and artifacts

Infrastructure responsibilities:

- PostgreSQL sessions and models
- Alembic migrations
- Redis-backed event streaming and job coordination
- Qdrant strategic memory
- AI provider adapters

## AI Architecture

Boardroom AI uses an `ExecutiveIntelligenceProvider` abstraction. The orchestrator asks the provider to evaluate one executive at a time, which allows local deterministic inference, OpenAI, Claude, Gemini, and Ollama to share the same domain contract.

Milestone 1 ships with a deterministic local provider because it gives repeatable tests and a fully functional offline experience. The provider performs real heuristic analysis over budget, timeline, industry, funding stage, business model, competitor pressure, audience complexity, and country-specific risk. It intentionally creates dissent when risk thresholds are crossed.

Milestone 2 adds a live streaming orchestrator beside the synchronous orchestrator. It emits typed boardroom events over WebSockets, records every event to PostgreSQL, and maintains meeting-scoped executive memory so executives can reference earlier arguments while the discussion unfolds.

Future provider routing:

- local provider for tests, demos, and fallback
- OpenAI for high-quality strategic synthesis
- Claude for long-context report generation and legal-style critique
- Gemini for research-assisted market analysis
- Ollama for private local deployments

## Executive Agents

The first board includes:

- CEO
- CTO
- CFO
- COO
- CMO
- Product Manager
- Investor
- VC Partner
- Market Research Analyst
- Competitive Intelligence Analyst
- Legal Advisor
- Cybersecurity Expert
- Economist
- Growth Strategist
- UX Designer
- Data Scientist
- Operations Advisor
- AI Ethics Advisor

Each role has independent goals, personality, decision lens, confidence behavior, disagreement thresholds, and vote semantics.

## Database Design

PostgreSQL is the only relational database target.

Core tables:

- `startup_briefs` - immutable founder input snapshots
- `board_meetings` - meeting lifecycle, consensus state, aggregate confidence
- `executive_agents` - role definitions attached to a meeting version
- `meeting_turns` - proposal, critique, revision, and consensus turns
- `meeting_events` - raw WebSocket event log for replay and audit
- `confidence_events` - confidence history and rationale per executive
- `vote_events` - provisional vote history and vote changes
- `board_votes` - final vote per executive
- `final_reports` - report metadata and final consensus
- `report_sections` - normalized report sections for export, retrieval, and revision

Important relationships:

- one `startup_brief` has many `board_meetings`
- one `board_meeting` has many `meeting_turns`, `board_votes`, and `final_reports`
- one `final_report` has many `report_sections`

## API Design

Versioned API prefix: `/api/v1`.

Milestone 1 routes:

- `GET /health` - service health
- `GET /api/v1/executives` - executive role catalog
- `POST /api/v1/board-meetings` - generate a board meeting and structured report
- `WS /api/v1/board-meetings/live` - stream a persisted live board meeting

Future routes:

- `GET /api/v1/board-meetings/{id}`
- `GET /api/v1/board-meetings/{id}/events`
- `POST /api/v1/board-meetings/{id}/revise`
- `POST /api/v1/reports/{id}/export`
- `POST /api/v1/research/jobs`

## Milestone Roadmap

1. **Working Board Meeting Vertical Slice**
   - deterministic board orchestration
   - structured report generation
   - FastAPI route
   - polished Next.js intake and meeting view
   - PostgreSQL schema and Docker Compose

2. **Persistent Meetings and WebSocket Events**
   - persist briefs, turns, votes, and reports
   - stream meeting progress over WebSockets
   - async job execution with Redis-backed queues

3. **LLM Provider Router**
   - OpenAI, Claude, Gemini, and Ollama adapters
   - provider fallback strategy
   - token/cost telemetry
   - prompt versioning and evaluation fixtures

4. **Strategic Memory and Research**
   - Qdrant collections for market memory, competitor dossiers, and founder history
   - retrieval-augmented market analysis
   - source attribution and confidence calibration

5. **Investor-Grade Artifact Suite**
   - PDF report export
   - pitch deck outline and slide generation
   - financial forecast modeling
   - board decision history

6. **Production Platform**
   - organization accounts
   - audit logs
   - billing boundaries
   - observability
   - Kubernetes manifests
