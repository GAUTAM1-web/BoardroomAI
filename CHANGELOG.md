# Changelog

## 1.0.0-rc.1

- Added production deployment readiness with public landing page, `/workspace` shell, demo account, guest mode, email session creation, secure logout, OAuth-ready Google config, and HTTP-only session cookies.
- Added idempotent portfolio demo seed for fresh default workspaces, including a sample meeting, report, approval workflow, tasks, notification, templates, knowledge, calendar review, and business analysis.
- Added liveness/readiness checks, redacted environment diagnostics, dependency diagnostics, provider diagnostics, security headers, rate limiting, and deployment target detection.
- Added Vercel, Railway, Render, Fly.io, production Docker Compose, and root backend Dockerfile deployment scaffolding.
- Updated Docker/frontend API configuration to avoid hardcoded localhost in production while preserving same-origin proxy mode for local and Docker development.
- Updated deployment, environment, developer, API, architecture, enterprise, desktop, troubleshooting, README, and changelog documentation.
- Added a real-world intelligence layer for business analyses with optional maps, places, weather, news, currency, government/open-data, and demographics providers.
- Added provider health diagnostics, last-sync/latency/error reporting, smart in-memory live-data caching, and a retry endpoint that clears provider cache without exposing secrets.
- Added evidence panels that separate live evidence, historical evidence, AI inference, and user-provided information in API responses and the Decide workspace.
- Added live-mode location, weather, news, currency, government/open-data, and demographics sections to business decision briefs with graceful degradation when providers are unavailable.
- Added enterprise workspace support with organizations, departments, teams, users, role permissions, comments, approvals, tasks, calendar events, notifications, templates, knowledge search, admin diagnostics, analytics, and audit trail endpoints.
- Added a polished Enterprise view in the desktop/web shell with organization KPIs, pending approvals, tasks, calendar reviews, board activity, and executive signals.
- Added Ctrl+K command palette, notification center, toast history, offline status, guided help center, first-run tour, friendlier recovery errors, richer skeleton loaders, improved empty states, and live meeting progress.
- Added Executive Intelligence Engine V2 with silent internal research, staged reasoning pipeline, debate tree, confidence propagation, counterfactual analysis, scenario simulator, cognitive-bias detection, challenge questions, AI reflection, validation plan, decision explainability, and decision journal sections.
- Added dynamic specialist profiles that join only relevant meetings, including medical, compliance, cloud, AI, pricing, inventory, store operations, chef, food safety, and supply-chain specialists.
- Expanded live `meeting_started` assessment payload with internal research and executive challenge questions.
- Added Executive Intelligence Upgrade with permanent Risk Officer, role reasoning styles, dynamic meeting modes, and evidence-first meeting startup.
- Added report intelligence artifacts: evidence packet, strategic options A/B/C, decision matrix, confidence timeline, vote timeline, reasoning flow, meeting replay, executive scorecards, visual reasoning heatmap, and final decision brief.
- Added `meeting_mode` API/schema persistence with Alembic migration `0005_executive_intelligence`.
- Added frontend meeting-mode selector, dynamic executive roster display, Risk Officer seat, and section labels for the new replay/scorecard artifacts.
- Added tests for dynamic board selection, Risk Officer assumption challenges, evidence payloads, and streamed report sections.
- Added a professional Settings workspace with provider status, redacted API-key posture, theme preference, data-mode status, export defaults, and client diagnostics.
- Added Electron desktop shell with custom app icon, splash screen, native window, About dialog, production DevTools suppression, local Next server startup, and graceful shutdown.
- Added Windows release configuration for NSIS installer and portable executable targets.
- Added deterministic icon generation from the existing Boardroom AI SVG mark.
- Enabled Next.js standalone output for desktop packaging.
- Added structured JSON backend logging for startup, request completion, request failure, repository outages, and live boardroom failures without logging request bodies or secrets.
- Updated README, API docs, and architecture docs for desktop mode, settings, logging, packaging, and known release limitations.
