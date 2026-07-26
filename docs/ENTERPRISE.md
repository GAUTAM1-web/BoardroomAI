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

- Founder, CEO, Administrator: full workspace administration and approval permissions
- Manager: meetings, comments, exports, approvals, and tasks
- Analyst: meetings, comments, and tasks
- Viewer: read-only meeting access

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
