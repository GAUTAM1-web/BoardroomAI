# Boardroom AI Architecture

## Product Intent

Boardroom AI turns a founder's startup brief into an executive board meeting. The system should feel like an operating system for founders: focused, fast, serious, visually premium, and useful beyond a chat transcript.

Milestone 5 extends that intent beyond startup reports into evidence-based business decisions: discover, compare, validate, plan, launch, track, improve, and decide whether to expand, pivot, or exit.

## System Boundaries

```text
Founder UI
  -> Next.js application
  -> FastAPI API gateway
  -> Boardroom domain orchestration
  -> Business intelligence domain services
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
    domain/business_intelligence/
                          evidence, location, supplier, finance, and validation services
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
- produce local-business decision briefs from evidence, user inputs, and labeled assumptions
- calculate Opportunity Score, procurement needs, setup cost, daily-sales targets, and validation tasks
- distinguish verified facts, user-provided information, configurable benchmarks, assumptions, unknowns, and demo-only scaffolding

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

Milestone 3 adds the founder operating workspace on top of the same contracts: deterministic startup idea generation, dashboard metrics, meeting history, global search, favorites, compare, delete, and report exports. These features reuse persisted meetings and report sections instead of introducing a separate artifact store.

Future provider routing:

- local provider for tests, demos, and fallback
- OpenAI for high-quality strategic synthesis
- Claude for long-context report generation and legal-style critique
- Gemini for research-assisted market analysis
- Ollama for private local deployments

Business-data provider routing:

- `demo` mode for labeled benchmark scaffolding; it must never be shown as live evidence
- `manual` mode for user-entered competitors, suppliers, quotations, observations, costs, and properties
- `live` mode for future map/place/search providers through backend-only credentials
- provider failures return actionable warnings and do not block manual analysis

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
- `business_analyses` - persisted decision briefs, request payloads, and calculated results
- `business_evidence_records` - reusable evidence records with source, retrieval time, confidence, and verification status
- `saved_suppliers` - saved/manual suppliers and supplier comparison data
- `business_validation_tasks` - pre-launch validation tasks and outcomes
- `business_performance_entries` - actual operating performance for forecast-versus-actual review

Important relationships:

- one `startup_brief` has many `board_meetings`
- one `board_meeting` has many `meeting_turns`, `board_votes`, and `final_reports`
- one `final_report` has many `report_sections`
- one `business_analysis` has many evidence records, saved suppliers, validation tasks, and performance entries

## API Design

Versioned API prefix: `/api/v1`.

Milestone 1 routes:

- `GET /health` - service health
- `GET /api/v1/executives` - executive role catalog
- `POST /api/v1/startup-ideas/generate` - generate startup ideas with launch-ready briefs
- `POST /api/v1/board-meetings` - generate a board meeting and structured report
- `WS /api/v1/board-meetings/live` - stream a persisted live board meeting
- `GET /api/v1/dashboard` - dashboard statistics and recent activity
- `GET /api/v1/board-meetings` - searchable meeting history
- `GET /api/v1/board-meetings/{id}` - full persisted meeting and report
- `PATCH /api/v1/board-meetings/{id}/favorite` - favorite a startup or meeting
- `DELETE /api/v1/board-meetings/{id}` - delete a meeting history item
- `GET /api/v1/search` - global search across meetings, reports, and executives
- `GET /api/v1/reports/{id}/export` - export PDF, Markdown, or JSON
- `GET /api/v1/business-data/providers` - business data/provider status
- `POST /api/v1/business-analyses` - create an evidence-based decision brief
- `GET /api/v1/business-analyses` - list saved decision briefs
- `GET /api/v1/business-analyses/{id}` - read a decision brief
- `GET /api/v1/business-analyses/{id}/export` - export PDF, Markdown, or JSON
- `POST /api/v1/business-analyses/{id}/performance-entries` - record actual business performance
- `POST /api/v1/business-analyses/{id}/board-review` - summarize forecast-versus-actual performance

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

3. **Founder Operating Workspace**
   - premium dashboard, responsive boardroom, idea generator, history, search, compare
   - professional report sections, VC readiness scoring, and PDF/Markdown/JSON exports
   - favorites and delete history

4. **Evidence-Based Business Intelligence**
   - simple guided intake for ordinary business owners
   - optional location permission and manual/map-pin location selection
   - evidence records, competitors, suppliers, procurement, finance, daily-sales targets
   - validation tasks, business analysis persistence, exports, and board-ready briefs

5. **LLM Provider Router**
   - OpenAI, Claude, Gemini, and Ollama adapters
   - provider fallback strategy
   - token/cost telemetry
   - prompt versioning and evaluation fixtures

6. **Strategic Memory and Research**
   - Qdrant collections for market memory, competitor dossiers, and founder history
   - retrieval-augmented market analysis
   - source attribution and confidence calibration

7. **Investor-Grade Artifact Suite**
   - pitch deck outline and slide generation
   - financial forecast modeling
   - deeper board decision history

8. **Production Platform**
   - organization accounts
   - audit logs
   - billing boundaries
   - observability
   - Kubernetes manifests
