# Enterprise Guide

Boardroom AI enterprise mode is additive. Existing single-user workflows continue to work because the backend seeds a `Default Organization` and `Workspace Owner` automatically.

Demo login is also additive. `/workspace?auth=demo` creates an Administrator session and, when
`DEMO_CONTENT_ENABLED=true`, fresh default workspaces include portfolio-ready meetings, approvals,
tasks, notifications, reports, and a business analysis.

## Workspace Model

```text
Organization
  -> Departments
  -> Teams
  -> Users
```

Default departments:

- Marketing
- Finance
- HR
- Operations
- Product

## Roles

Use the optional `X-Boardroom-Role` request header to test role behavior. Omitted headers default to `Administrator`.

- Owner, Founder, CEO, Administrator: full workspace administration and approval permissions
- Manager: meetings, comments, exports, approvals, and tasks
- Executive: meetings, comments, exports, approvals, and tasks without workspace administration
- Analyst: meetings, comments, and tasks
- Viewer: read-only meeting access
- Guest: read-only meeting access

## Collaboration

Reports support comments, replies, mentions, and resolution. Board meetings support collaborators. Approval workflows can be attached to meetings or business analyses, with ordered manager/CEO-style sign-off steps.

## Governance

The platform records audit events for material actions such as starting meetings, generating reports, creating comments, changing tasks, approval decisions, exports, and provider retries. Admin diagnostics return redacted provider status, live-data health, cache posture, and usage counts only; secrets are never returned to the browser or Electron renderer.

## Enterprise Dashboard

The Enterprise tab uses `/api/v1/enterprise/dashboard` and shows:

- organization KPIs
- pending approvals
- open tasks
- upcoming reviews and deadlines
- board activity
- executive decision signals

If the enterprise dashboard endpoint is unavailable in an older backend, the frontend falls back to
legacy dashboard and meeting-history data so the workspace remains usable.

## Intelligence Workspace

The Intelligence tab consumes `/api/v1/enterprise/intelligence-suite`. It combines:

- executive memory from stored turns, votes, recommendations, disagreements, and confidence history
- knowledge graph links across organization, users, meetings, reports, analyses, evidence, suppliers, tasks, risks, and knowledge items
- advanced analytics for meeting effectiveness, revenue targets, confidence evolution, decision outcomes, supplier rankings, and task scorecards
- assistant answers grounded in expanded enterprise search results
- document intelligence that stores supported uploads as knowledge items and labels extracted evidence as user-provided information
- workflow automation for task assignment, in-app notifications, export links, decision archive records, and dashboard refresh events
- observability for provider health, cache posture, database counts, audit events, and security posture

The frontend also has compatibility fallbacks. If the RC5 intelligence endpoint is unavailable, it derives a reduced graph and decision-memory view from `/api/v1/enterprise/dashboard`, `/api/v1/dashboard`, and meeting history rather than breaking the workspace.

## Document Intelligence

`POST /api/v1/documents/import` accepts base64 document content. Text extraction is local and deterministic for text files and common Office Open XML formats. PDF extraction is best-effort. Image OCR is not configured by default, so image uploads are indexed as metadata with a warning instead of fabricated text.

Imported documents create knowledge items, emit audit events, and can be linked to a board meeting or business analysis.

## Workflow Automation

`POST /api/v1/workflows/run` executes registered workflow actions:

- assign follow-up tasks
- notify executives in-app
- prepare export URLs
- archive decision records into the knowledge base
- mark dashboard state as refreshed from existing records

The workflow engine is additive. It uses existing tasks, notifications, knowledge items, and audit events, so no new migration is required.
