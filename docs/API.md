# API Contract

Base URL:

```text
http://localhost:8000
```

Version prefix:

```text
/api/v1
```

## GET /api/v1/executives

Returns the 18 executive profiles used by the boardroom.

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
  "business_model": "B2B SaaS"
}
```

### Response

The response includes:

- `meeting_id`
- `consensus_reached`
- `aggregate_confidence`
- `assessment`
- `turns`
- `votes`
- `report`

The report includes executive summary, startup overview, executive opinions, market analysis, competitor analysis, SWOT, financial analysis, risk matrix, action plan, VC readiness score, board vote, confidence scores, and the original Milestone 1 operating sections.

## WebSocket /api/v1/board-meetings/live

Starts a live persisted board meeting. The client connects, then sends the same founder brief JSON used by `POST /api/v1/board-meetings` as the first WebSocket message.

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

## GET /api/v1/board-meetings

Returns previous meetings.

Query parameters:

- `q`: optional search term
- `limit`: 1 to 100
- `favorite_only`: boolean

## GET /api/v1/board-meetings/{meeting_id}

Returns a persisted meeting with startup brief, turns, votes, report sections, favorite state, status, and timestamps.

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
- favorite state in `board_meetings`
