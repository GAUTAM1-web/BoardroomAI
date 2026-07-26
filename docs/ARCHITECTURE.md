# Boardroom AI Architecture

## Product Intent

Boardroom AI turns a founder's startup brief into an executive board meeting. The system should feel like an operating system for founders: focused, fast, serious, visually premium, and useful beyond a chat transcript.

Milestone 5 extends that intent beyond startup reports into evidence-based business decisions: discover, compare, validate, plan, launch, track, improve, and decide whether to expand, pivot, or exit.

Milestone 6 upgrades the boardroom layer itself: meetings now begin from explicit evidence packets, route through dynamic meeting modes, include a permanent Risk Officer devil's advocate, and generate replayable decision artifacts instead of a static report snapshot. Executive Intelligence Engine V2 deepens that layer with silent internal research, staged reasoning, debate trees, confidence propagation, counterfactuals, scenario simulation, cognitive-bias detection, AI reflection, and an append-only decision journal.

Milestone 8 extends the same architecture into an enterprise workspace. Organizations, departments, teams, users, roles, comments, approvals, tasks, calendar events, notifications, templates, knowledge items, analytics, admin diagnostics, and audit events are additive modules around the existing boardroom and business-analysis records.

Milestone 10 is a product-quality pass. It improves the shell with a command palette, notification center, guided help, better loading and empty states, friendly recovery errors, offline awareness, live meeting progress, and a polished enterprise dashboard. It does not introduce a new backend architecture.

Milestone 11 extends the business-intelligence domain with optional real-world providers. Maps, places, weather, news, currency, government/open-data, and demographics adapters add evidence when available, record provider health, use short-lived caching, and degrade with warnings instead of blocking the base analysis.

Milestone 12 adds a production shell around the existing architecture. The public landing page,
auth/session layer, demo workspace seed, deployment manifests, diagnostics routes, security
headers, and environment detection are additive; boardroom, business intelligence, enterprise,
desktop, and Docker APIs remain stable.

## System Boundaries

```text
Founder UI
  -> Next.js application
  -> FastAPI API gateway
  -> Boardroom domain orchestration
  -> Business intelligence domain services
  -> Optional real-world data providers
  -> Enterprise collaboration services
  -> AI provider abstraction
  -> PostgreSQL system of record
  -> Redis event/cache layer
  -> Qdrant strategic memory and retrieval layer
```

## Production Shell

The frontend now has two public entry points:

- `/` - public landing page for portfolio, recruiter, investor, and demo traffic.
- `/workspace` - authenticated BoardroomAI workspace used by browser and Electron.

`/meeting` remains a compatibility alias to the workspace. Electron loads `/workspace` from the
local standalone Next.js server.

The backend adds stateless HMAC sessions, auth capability discovery, liveness/readiness checks,
redacted environment diagnostics, dependency diagnostics, lightweight rate limiting, and security
headers. These routes do not replace existing APIs or require sessions for legacy single-user
flows.

Fresh default workspaces can seed portfolio demo records when `DEMO_CONTENT_ENABLED=true`, using
normal PostgreSQL tables so dashboards, history, enterprise workflows, reports, search, approvals,
tasks, notifications, and business analyses all exercise the real API surface.

## Monorepo Structure

```text
backend/
  app/
    api/                  HTTP routes and dependency wiring
    core/                 configuration, logging, app lifecycle
    domain/boardroom/     clean domain model and orchestration
    domain/business_intelligence/
                          evidence, location, supplier, finance, and validation services
    domain/enterprise/    role and permission policy
    infrastructure/       database and provider adapters
    schemas/              request and response DTOs
  alembic/                PostgreSQL migrations
  tests/                  unit and contract tests

frontend/
  app/                    Next.js App Router
  components/             boardroom experience and UI primitives
  electron/               Electron main process, preload bridge, splash, icons
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
- select the right executive roster for full board, quick review, emergency, investor, expansion, pivot, acquisition, or crisis meetings
- invite relevant dynamic specialists for the meeting, without adding them to every permanent board
- run proposal, assumption challenge, critique, revision, vote, and consensus phases
- produce a structured board report
- produce internal research packets, reasoning pipelines, evidence packets, strategic options, decision matrices, debate trees, confidence propagation, counterfactuals, scenario simulators, bias detection, challenge questions, boardroom timelines, meeting replay, executive scorecards, performance tracking, explainability, validation plans, AI reflection, decision journals, and final decision briefs
- produce local-business decision briefs from evidence, user inputs, and labeled assumptions
- calculate Opportunity Score, procurement needs, setup cost, daily-sales targets, and validation tasks
- distinguish verified facts, user-provided information, configurable benchmarks, assumptions, unknowns, and demo-only scaffolding
- enrich live-mode business analyses with provider-sourced location, weather, news, currency, government/open-data, and demographics evidence
- expose evidence panels that separate live evidence, historical evidence, AI inference, and user-provided information

Application/API responsibilities:

- validate HTTP input
- convert DTOs into domain objects
- call the orchestrator
- return structured JSON
- later persist meetings, turns, votes, report sections, and artifacts
- enforce additive enterprise role checks through explicit permission policy
- expose organization, approval, task, calendar, notification, template, knowledge, analytics, admin, and audit endpoints

Infrastructure responsibilities:

- PostgreSQL sessions and models
- Alembic migrations
- Redis-backed event streaming and job coordination
- Qdrant strategic memory
- AI provider adapters
- live data provider adapters, in-memory response cache, and provider health state
- structured production logging
- Windows desktop packaging and local frontend server startup

## AI Architecture

Boardroom AI uses an `ExecutiveIntelligenceProvider` abstraction. The orchestrator asks the provider to evaluate one executive at a time, which allows local deterministic inference, OpenAI, Claude, Gemini, and Ollama to share the same domain contract.

Milestone 1 ships with a deterministic local provider because it gives repeatable tests and a fully functional offline experience. The provider performs real heuristic analysis over budget, timeline, industry, funding stage, business model, competitor pressure, audience complexity, and country-specific risk. It intentionally creates dissent when risk thresholds are crossed.

Milestone 2 adds a live streaming orchestrator beside the synchronous orchestrator. It emits typed boardroom events over WebSockets, records every event to PostgreSQL, and maintains meeting-scoped executive memory so executives can reference earlier arguments while the discussion unfolds.

Milestone 3 adds the founder operating workspace on top of the same contracts: deterministic startup idea generation, dashboard metrics, meeting history, global search, favorites, compare, delete, and report exports. These features reuse persisted meetings and report sections instead of introducing a separate artifact store.

Milestone 6 adds executive intelligence without changing the provider contract. Profiles now carry permanent reasoning styles, the orchestrator selects an executive subset from the requested meeting mode, the Risk Officer challenges unsupported assumptions before functional critiques, and the report builder assembles evidence-first decision artifacts from the same deterministic meeting state.

Executive Intelligence Engine V2 keeps the same API surface but changes the decision product. Before discussion starts, the system creates an internal research packet from founder-provided facts, assumptions, unknowns, contradictions, and confidence. The report then records the full reasoning pipeline: objectives, constraints, hypotheses, evidence quality, alternative strategies, challenges, revisions, votes, validation steps, and reflection. The engine never invents suppliers, market sources, customers, or live evidence; unavailable facts remain explicit unknowns.

Future provider routing:

- local provider for tests, demos, and fallback
- OpenAI for high-quality strategic synthesis
- Claude for long-context report generation and legal-style critique
- Gemini for research-assisted market analysis
- Ollama for private local deployments

Business-data provider routing:

- `demo` mode for labeled benchmark scaffolding; it must never be shown as live evidence
- `manual` mode for user-entered competitors, suppliers, quotations, observations, costs, and properties
- `live` mode for enabled public or configured providers through backend-only settings
- maps and places can use public OpenStreetMap/Nominatim when selected
- weather uses Open-Meteo, news uses GDELT DOC, currency uses Frankfurter, and government/open-data plus demographics use World Bank indicators by default
- provider responses are cached for `LIVE_DATA_CACHE_TTL_SECONDS`
- provider failures return actionable warnings, are visible in provider health, and do not block manual analysis

## Settings Workspace

The Settings workspace is a frontend configuration surface. It shows backend provider status through `/api/v1/business-data/providers`, can clear live-data cache through `/api/v1/business-data/providers/retry`, stores non-secret theme and export preferences locally, and displays client diagnostics such as public API routing and WebSocket base configuration.

Secrets are intentionally one-way:

- API keys remain backend environment variables.
- The browser and Electron renderer never receive provider key values.
- Settings displays redacted status only.
- Production logs avoid request bodies and secret-bearing headers.

## Enterprise Workspace

Enterprise collaboration extends existing records instead of replacing them. Single-user workflows still create and use a seeded `Default Organization` with a `Workspace Owner` administrator. Existing API clients do not need to send organization identifiers.

Enterprise responsibilities:

- maintain organization, department, team, user, and membership records
- attach board meetings and business analyses to an organization where available
- apply role permissions for create, edit, export, comment, approve, task management, and administration
- support report comments, replies, mentions, and resolution
- support approval workflows with ordered steps
- support tasks, due dates, board reviews, notifications, knowledge items, and report templates
- record audit events for material workspace actions
- expose analytics and executive dashboards from persisted meetings, decisions, approvals, evidence, and audit records

The frontend enterprise view consumes `/api/v1/enterprise/dashboard` and uses the same design primitives as the rest of the product. The command palette and notification center are client-side shell improvements that sit above the unchanged route structure.

## Desktop Shell

The Windows desktop build uses Electron rather than a separate frontend rewrite. Electron starts a local Next.js standalone server on `127.0.0.1:3010`, shows `electron/splash.html` while the server becomes reachable, then loads the same Boardroom AI workspace in a native window.

Desktop responsibilities:

- native double-click launch
- product window title and icon
- splash screen
- About dialog with version metadata
- production DevTools disabled by default
- graceful shutdown of the local Next server
- installer and portable executable targets through Electron Builder

The desktop package does not embed PostgreSQL, Redis, Qdrant, or FastAPI. It expects the backend stack to run locally or be configured as a reachable backend endpoint.

## Executive Agents

The board includes:

- CEO
- Risk Officer
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

Meeting modes select a subset of that board when speed or context matters. `full_board` invites every permanent executive; other modes always include the CEO and Risk Officer, then add the most relevant finance, operations, market, legal, security, investor, product, or data voices based on the mode and startup brief. Domain-specific specialists can also join only when relevant, including Chef, Food Safety Specialist, Supply Chain Specialist, Cloud Architect, AI Engineer, Inventory Specialist, Store Operations Specialist, Pricing Analyst, Medical Advisor, and Compliance Specialist.

## Database Design

PostgreSQL is the only relational database target.

Core tables:

- `startup_briefs` - immutable founder input snapshots, including selected meeting mode
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
- `enterprise_organizations` - organization workspace roots
- `enterprise_departments` - departments such as Marketing, Finance, HR, Operations, and Product
- `enterprise_teams` - teams within departments
- `enterprise_users` - enterprise user identities
- `enterprise_memberships` - organization roles and permission snapshots
- `meeting_collaborators` - shared board meeting participation
- `report_comments` - report comments, replies, mentions, and resolution state
- `approval_workflows` and `approval_steps` - ordered approval and sign-off workflows
- `enterprise_tasks` - recommendation follow-ups and assigned work
- `calendar_events` - board reviews, deadlines, and related events
- `enterprise_notifications` - in-app and email-ready notification records
- `knowledge_items` - reports, lessons, templates, meeting history, and best practices
- `report_templates` - report templates by category and locale
- `audit_events` - append-only audit trail for workspace actions

Important relationships:

- one `startup_brief` has many `board_meetings`
- one `board_meeting` has many `meeting_turns`, `board_votes`, and `final_reports`
- one `final_report` has many `report_sections`
- one `business_analysis` has many evidence records, saved suppliers, validation tasks, and performance entries
- one `enterprise_organization` owns departments, teams, memberships, tasks, calendar events, notifications, knowledge items, templates, and audit events
- one `board_meeting` can have collaborators, comments, approval workflows, tasks, and audit events

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
- `POST /api/v1/business-data/providers/retry` - clear provider cache and refresh status
- `POST /api/v1/business-analyses` - create an evidence-based decision brief
- `GET /api/v1/business-analyses` - list saved decision briefs
- `GET /api/v1/business-analyses/{id}` - read a decision brief
- `GET /api/v1/business-analyses/{id}/export` - export PDF, Markdown, or JSON
- `POST /api/v1/business-analyses/{id}/performance-entries` - record actual business performance
- `POST /api/v1/business-analyses/{id}/board-review` - summarize forecast-versus-actual performance
- `GET /api/v1/organizations` - list enterprise organizations
- `POST /api/v1/organizations` - create an organization workspace
- `GET /api/v1/enterprise/dashboard` - enterprise dashboard
- `GET /api/v1/enterprise/analytics` - enterprise analytics and executive signals
- `GET /api/v1/enterprise/admin` - admin panel payload
- `GET /api/v1/enterprise/audit` - audit trail
- `GET /api/v1/report-templates` - report templates
- `GET /api/v1/knowledge/search` - knowledge base search
- `GET /api/v1/tasks`, `POST /api/v1/tasks`, `PATCH /api/v1/tasks/{id}` - tasks
- `GET /api/v1/calendar` - calendar events
- `GET /api/v1/notifications` - in-app notifications
- `POST /api/v1/board-meetings/{id}/collaborators` - shared meeting participation
- `GET /api/v1/reports/{id}/comments`, `POST /api/v1/reports/{id}/comments`, `PATCH /api/v1/reports/{id}/comments/{comment_id}` - report comments
- `POST /api/v1/board-meetings/{id}/approvals`, `POST /api/v1/business-analyses/{id}/approvals`, `POST /api/v1/approvals/{workflow_id}/steps/{step_id}/decision` - approval workflows

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
