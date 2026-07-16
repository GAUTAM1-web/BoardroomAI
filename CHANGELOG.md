# Changelog

## 1.0.0-rc.1

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
