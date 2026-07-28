# API Contract

Base URL:

```text
http://localhost:8000
```

Version prefix:

```text
/api/v1
```

Enterprise role checks use the optional `X-Boardroom-Role` header. When the header is omitted, the API defaults to `Administrator` so existing single-user and desktop flows continue to work unchanged.

## Health And Diagnostics

- `GET /health` - compatibility health check.
- `GET /health/live` - process liveness.
- `GET /health/ready` - readiness and deployment target.
- `GET /api/v1/diagnostics/environment` - redacted environment readiness.
- `GET /api/v1/diagnostics/providers` - provider health and redacted secret posture.
- `GET /api/v1/diagnostics/dependencies` - PostgreSQL, Redis, and Qdrant checks.
- `GET /api/v1/diagnostics` - combined diagnostics payload.

## Auth Endpoints

Authentication is additive. Existing APIs still work when no session is sent.

- `GET /api/v1/auth/config` - enabled auth modes and OAuth readiness.
- `GET /api/v1/auth/session` - current cookie or bearer session status.
- `POST /api/v1/auth/session` - creates an email, demo, or guest session.
- `POST /api/v1/auth/logout` - clears the session cookie.

Session cookies are HTTP-only. Production mode marks them secure.

## GET /api/v1/executives

Returns the 19 executive profiles used by the boardroom, including the permanent Risk Officer.

## POST /api/v1/startup-ideas/generate

Generates startup idea cards and board-ready meeting briefs.

### Request

```json
{
  "prompt": "Generate 20 startup ideas",
  "interests": "AI workflow automation, founder tools",
  "industry": "AI productivity",
  "country": "United States",
  "budget": 150000,
  "business_model": "B2B SaaS",
  "funding_stage": "pre-seed",
  "number_of_ideas": 20
}
```

### Response

```json
{
  "ideas": [
    {
      "startup_name": "Signal OS",
      "tagline": "Workflow Automation for founder-led companies.",
      "problem": "...",
      "solution": "...",
      "target_audience": "...",
      "revenue_model": "B2B SaaS",
      "estimated_startup_cost": 150000,
      "estimated_tam": "$4.6B serviceable global opportunity",
      "innovation_score": 86,
      "scalability_score": 82,
      "difficulty": "Moderate",
      "competitive_advantage": "...",
      "success_probability": 74,
      "meeting_brief": {}
    }
  ]
}
```

## POST /api/v1/board-meetings

Creates and persists a completed board meeting from a founder brief.

### Request

```json
{
  "startup_idea": "AI finance copilot for independent clinics",
  "industry": "healthcare fintech",
  "country": "United States",
  "budget": 150000,
  "timeline_months": 6,
  "competitors": ["Ramp", "Brex", "QuickBooks"],
  "target_audience": "clinic owners with 5-50 employees",
  "funding_stage": "pre-seed",
  "business_model": "B2B SaaS",
  "meeting_mode": "full_board"
}
```

Supported `meeting_mode` values:

- `full_board`
- `quick_review`
- `emergency_meeting`
- `investor_pitch`
- `expansion_review`
- `pivot_review`
- `acquisition_review`
- `crisis_meeting`

### Response

The response includes:

- `meeting_id`
- `consensus_reached`
- `aggregate_confidence`
- `assessment`
- `turns`
- `votes`
- `report`

The report includes internal research, reasoning pipeline, evidence packet, strategic options A/B/C, decision matrix, counterfactual analysis, scenario simulator, cognitive-bias detection, executive challenge questions, dynamic expert roster, executive summary, startup overview, executive opinions, market analysis, competitor analysis, SWOT, financial analysis, risk matrix, action plan, VC readiness score, board vote, confidence scores, confidence timeline, confidence propagation, vote timeline, reasoning flow, debate tree, boardroom timeline, meeting replay, executive scorecards, executive performance tracking, visual reasoning heatmap, decision explainability, validation plan, AI reflection, decision journal, final decision brief, and the original Milestone 1 operating sections.

The legacy startup idea field `success_probability` is kept for backward compatibility. Treat it as a heuristic score, not a guarantee of business success.

## WebSocket /api/v1/board-meetings/live

Starts a live persisted board meeting. The client connects, then sends the same founder brief JSON used by `POST /api/v1/board-meetings` as the first WebSocket message.

The first `meeting_started` event includes the selected `meeting_mode`, invited `executives`, risk `assessment`, evidence packet, internal research packet, and executive challenge questions. Report sections then stream one artifact at a time, including replay, confidence propagation, debate tree, scenario simulator, reflection, and journal sections.

### Event Envelope

```json
{
  "event_id": "uuid",
  "meeting_id": "uuid",
  "sequence": 12,
  "event_type": "timeline_statement",
  "role": "CFO",
  "timestamp": "2026-06-25T12:00:00+00:00",
  "payload": {}
}
```

### Event Types

- `meeting_started`
- `executive_status`
- `confidence_changed`
- `timeline_statement`
- `vote_cast`
- `vote_changed`
- `vote_confirmed`
- `report_section`
- `consensus_reached`
- `error`

## GET /api/v1/dashboard

Returns dashboard statistics:

- total meetings
- reports generated
- approval rate
- average confidence
- top industries
- recent meetings
- recent reports
- recent board decisions

## Enterprise Workspace Endpoints

These endpoints are additive and preserve all original boardroom and business-analysis APIs.

- `GET /api/v1/organizations` - list organizations, including the seeded default workspace.
- `POST /api/v1/organizations` - create an organization with default departments, teams, templates, knowledge, and review calendar.
- `GET /api/v1/enterprise/dashboard` - organization dashboard with departments, teams, users, recent meetings, pending approvals, tasks, board activity, upcoming reviews, analytics, and executive signals.
- `GET /api/v1/enterprise/analytics` - organization metrics for meetings, decisions, approval time, active executives, success rate, evidence quality, confidence trends, risk trends, and recommendation outcomes.
- `GET /api/v1/enterprise/intelligence-suite` - combined executive memory, knowledge graph, advanced analytics, assistant suggestions, collaboration, workflow catalog, and observability snapshot.
- `GET /api/v1/enterprise/executive-memory` - role-aware memory derived from stored votes, turns, recommendations, disagreements, confidence history, and decision outcomes.
- `GET /api/v1/enterprise/knowledge-graph` - graph nodes and edges derived from organizations, users, meetings, reports, analyses, evidence, suppliers, tasks, risks, and knowledge items.
- `GET /api/v1/enterprise/advanced-analytics` - revenue projections, risk trends, meeting effectiveness, executive performance, confidence evolution, opportunity tracking, decision accuracy, and supplier rankings.
- `POST /api/v1/enterprise/assistant` - answers questions using stored enterprise search results, memory, and analytics.
- `GET /api/v1/search/global?q=...` - expanded search across meetings, reports, executives, tasks, business analyses, evidence, suppliers, knowledge, and users.
- `POST /api/v1/documents/import` - imports a base64 document, extracts supported text, classifies risks/opportunities, stores a knowledge item, and records audit history.
- `GET /api/v1/collaboration/presence` - active workspace users, meeting collaborators, recent comments, and notifications.
- `POST /api/v1/workflows/run` - runs registered enterprise automation actions such as assigning tasks, notifying executives, preparing export links, archiving decisions, and refreshing dashboard state.
- `GET /api/v1/observability` - admin-only operational snapshot with database counts, recent audit/error events, provider health, cache posture, and security posture.
- `GET /api/v1/enterprise/admin` - users, organizations, redacted API-key posture, providers, feature flags, diagnostics, and usage statistics.
- `GET /api/v1/enterprise/audit` - audit events such as meeting started, report generated, comment created, task updated, export-ready activity, and approval decisions.
- `GET /api/v1/report-templates` - seeded templates for restaurant, retail, manufacturing, healthcare, technology, franchise, and export reports.
- `GET /api/v1/knowledge/search?q=...` - natural-language-ready knowledge search across reports, lessons, templates, meeting history, and best-practice seeds.
- `GET /api/v1/tasks` - list enterprise tasks, optionally filtered by status.
- `POST /api/v1/tasks` - create a task from a recommendation or manual action.
- `PATCH /api/v1/tasks/{task_id}` - update task title, description, status, or due date.
- `GET /api/v1/calendar` - list board reviews, follow-ups, deadlines, and related events.
- `GET /api/v1/notifications` - list in-app notification records.

## Collaboration and Approval Endpoints

- `POST /api/v1/board-meetings/{meeting_id}/collaborators` - join or update a meeting collaborator.
- `GET /api/v1/reports/{meeting_id}/comments` - list report comments and replies.
- `POST /api/v1/reports/{meeting_id}/comments` - create a comment with optional section key, parent comment, and mentions.
- `PATCH /api/v1/reports/{meeting_id}/comments/{comment_id}` - resolve or reopen a comment.
- `POST /api/v1/board-meetings/{meeting_id}/approvals` - create a meeting approval workflow.
- `POST /api/v1/business-analyses/{analysis_id}/approvals` - create a business-analysis approval workflow.
- `POST /api/v1/approvals/{workflow_id}/steps/{step_id}/decision` - approve or reject a workflow step.

Role permissions:

- Owner, Founder, CEO, Administrator: full workspace administration and approvals.
- Manager: create/edit meetings, comment, export, approve, and manage tasks.
- Executive: create/edit meetings, comment, export, approve, and manage tasks without workspace administration.
- Analyst: create meetings, view meetings, comment, and manage tasks.
- Viewer: view-only access.
- Guest: view-only meeting access.

### POST /api/v1/enterprise/assistant

Request:

```json
{
  "question": "Find rejected restaurant recommendations and unresolved risks."
}
```

Response:

```json
{
  "answer": {
    "question": "Find rejected restaurant recommendations and unresolved risks.",
    "answer": "I found stored records related to the question...",
    "source_count": 4,
    "sources": [],
    "recommended_actions": [],
    "limitations": [],
    "generated_at": "2026-07-28T00:00:00+00:00"
  }
}
```

### POST /api/v1/documents/import

Request:

```json
{
  "filename": "supplier-summary.txt",
  "content_base64": "U3VwcGxpZXIgcmlzayBzdW1tYXJ5...",
  "mime_type": "text/plain",
  "meeting_id": null,
  "business_analysis_id": null,
  "tags": ["supplier", "risk"]
}
```

Supported local extraction: `.txt`, `.md`, `.csv`, `.json`, `.docx`, `.pptx`, `.xlsx`, and best-effort PDF text. Images are stored as metadata unless an OCR provider is added later. The response labels evidence as user-provided information and returns warnings when text extraction is unavailable.

## GET /api/v1/business-data/providers

Returns configured provider mode, map provider name, whether live map/place sources are configured, provider health, cache status, and the supported data modes.

This endpoint is safe for the Settings workspace. It returns provider names and boolean configuration status only; API keys and provider secrets are never returned.

Supported modes:

- `demo`: labeled benchmark scaffolding only; no live local evidence.
- `manual`: user-entered competitors, suppliers, quotations, observations, costs, and locations.
- `live`: attempts enabled public and configured providers. Missing or failed providers return actionable warnings.

Provider health records include:

- provider type and configured name
- `ready`, `ok`, `disabled`, or `error` status
- last sync time
- latency in milliseconds
- cache hit flag
- redacted error text when a connector fails

## POST /api/v1/business-data/providers/retry

Clears the in-memory live-data cache and returns the same redacted provider-status payload as `GET /api/v1/business-data/providers`.

## POST /api/v1/business-analyses

Creates and persists an evidence-based business decision brief for local businesses, services, shop/property evaluation, existing businesses, or technology startup concepts.

### Request

```json
{
  "workflow_type": "existing_idea",
  "business_idea": "Mobile-repair shop",
  "business_category": "Local repair service",
  "location": {
    "country": "United States",
    "city": "Austin",
    "locality": "Downtown",
    "radius_km": 3,
    "source": "manual"
  },
  "budget": 25000,
  "priorities": ["Full analysis", "Supplier discovery", "Required daily sales"],
  "data_mode": "manual",
  "target_customers": "office workers and residents needing quick repairs",
  "manual_competitors": [
    {
      "name": "Downtown Phone Repair",
      "category": "mobile repair",
      "distance_km": 1.1,
      "notes": "User observed weekend queues."
    }
  ],
  "manual_suppliers": [
    {
      "name": "Parts Wholesale Counter",
      "category": "screen and battery supplier",
      "distance_km": 8,
      "product_categories": ["screens", "batteries"]
    }
  ],
  "financial_assumptions": {
    "expected_rent": 1800,
    "security_deposit": 3600,
    "working_capital_months": 3,
    "average_transaction_value": 45,
    "gross_margin_percent": 45,
    "working_days_per_month": 26
  }
}
```

### Response

The response includes:

- `analysis_id`
- provider mode and demo notice
- disclaimer
- recommendation
- explainable Opportunity Score
- evidence records
- `evidence_panel` with counts for live evidence, historical evidence, AI inference, and user-provided information
- `live_intelligence` with available location, weather, news, currency, government/open-data, demographics, and provider-health sections
- competitors and suppliers
- candidate areas and property analysis
- customer segments
- procurement and opening inventory plan
- financial assumptions and scenarios
- daily-sales targets
- validation plan
- performance-tracking scaffold
- `board_brief` for launching the existing animated boardroom
- exportable `report`

Opportunity Score is not a success probability and should never be presented as a guarantee.

## GET /api/v1/business-analyses

Returns saved business-analysis summaries.

Query parameters:

- `limit`: 1 to 100

## GET /api/v1/business-analyses/{analysis_id}

Returns a persisted business decision brief.

## GET /api/v1/business-analyses/{analysis_id}/export

Exports a business decision brief.

Query parameter:

- `format`: `pdf`, `markdown`, or `json`

## POST /api/v1/business-analyses/{analysis_id}/performance-entries

Adds actual operating performance for forecast-versus-actual review.

```json
{
  "period_label": "Week 1",
  "revenue": 500,
  "expenses": 900,
  "customers": 18,
  "transactions": 20,
  "complaints": 1
}
```

## POST /api/v1/business-analyses/{analysis_id}/board-review

Generates a simple board review from recorded actuals:

- performance summary
- top issue
- top opportunity
- financial warning
- customer insight
- inventory insight
- recommended experiments
- next-week priorities

## GET /api/v1/board-meetings

Returns previous meetings.

Query parameters:

- `q`: optional search term
- `limit`: 1 to 100
- `favorite_only`: boolean

## GET /api/v1/board-meetings/{meeting_id}

Returns a persisted meeting with startup brief, meeting mode, turns, votes, report sections, favorite state, status, and timestamps.

## PATCH /api/v1/board-meetings/{meeting_id}/favorite

Updates favorite state.

```json
{
  "is_favorite": true
}
```

## DELETE /api/v1/board-meetings/{meeting_id}

Deletes a meeting and cascades its persisted turns, events, votes, confidence events, and report rows.

## GET /api/v1/search

Global search across meetings, reports, report sections, and executive profiles.

Query parameters:

- `q`: search term
- `limit`: 1 to 30

## GET /api/v1/reports/{meeting_id}/export

Exports a report.

Query parameter:

- `format`: `pdf`, `markdown`, or `json`

Examples:

```text
/api/v1/reports/{meeting_id}/export?format=pdf
/api/v1/reports/{meeting_id}/export?format=markdown
/api/v1/reports/{meeting_id}/export?format=json
```

## Persistence

Live and synchronous meetings persist to PostgreSQL:

- raw events in `meeting_events`
- chronological statements in `meeting_turns`
- confidence changes in `confidence_events`
- provisional and changed votes in `vote_events`
- final votes in `board_votes`
- report and streamed report sections in `final_reports` and `report_sections`
- selected founder brief meeting mode in `startup_briefs.meeting_mode`
- favorite state in `board_meetings`
- business analyses in `business_analyses`
- reusable evidence records in `business_evidence_records`
- saved suppliers in `saved_suppliers`
- validation tasks in `business_validation_tasks`
- actual performance entries in `business_performance_entries`
