# API Contract

Base URL:

```text
http://localhost:8000
```

Version prefix:

```text
/api/v1
```

## POST /api/v1/board-meetings

Creates a board meeting from a founder brief and returns a structured report.

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
- `turns`
- `votes`
- `report`

The `report.sections` object contains every required output:

- `executive_summary`
- `business_plan`
- `market_analysis`
- `competitor_analysis`
- `swot`
- `business_model_canvas`
- `customer_personas`
- `technology_architecture`
- `database_design`
- `financial_forecast`
- `hiring_plan`
- `marketing_strategy`
- `investment_readiness`
- `risk_assessment`
- `pitch_deck_summary`
- `ninety_day_roadmap`
- `board_vote`
- `confidence_scores`

## WebSocket /api/v1/board-meetings/live

Starts a live persisted board meeting. The client connects, then sends the same founder brief JSON used by `POST /api/v1/board-meetings` as the first WebSocket message.

### Client Message

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

### Stream Event Envelope

Every server event uses the same envelope:

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

### Persistence

The live stream persists to PostgreSQL while it streams:

- raw events in `meeting_events`
- chronological statements in `meeting_turns`
- confidence changes in `confidence_events`
- provisional and changed votes in `vote_events`
- final votes in `board_votes`
- report and streamed report sections in `final_reports` and `report_sections`
