# BoardroomAI v1.0 RC5 Release Report

## Scope

RC5 extends the existing BoardroomAI architecture into a global enterprise SaaS workspace without
removing or renaming existing APIs.

Added:

- executive memory derived from stored turns, votes, recommendations, disagreements, and confidence
- knowledge graph derived from organizations, users, meetings, reports, analyses, evidence,
  suppliers, tasks, risks, and knowledge items
- advanced analytics for meeting effectiveness, revenue targets, confidence evolution, decision
  outcomes, task scorecards, and supplier rankings
- enterprise assistant grounded in expanded enterprise search and stored records
- document intelligence with local text extraction, classification, knowledge-item storage, and
  audit logging
- workflow automation using existing tasks, notifications, knowledge items, and audit events
- collaboration presence and observability endpoints
- Intelligence workspace tab in the Next.js/Electron shell
- Kubernetes deployment scaffold that references Kubernetes Secret keys instead of storing secrets

## API Additions

- `GET /api/v1/enterprise/intelligence-suite`
- `GET /api/v1/enterprise/executive-memory`
- `GET /api/v1/enterprise/knowledge-graph`
- `GET /api/v1/enterprise/advanced-analytics`
- `POST /api/v1/enterprise/assistant`
- `GET /api/v1/search/global`
- `POST /api/v1/documents/import`
- `GET /api/v1/collaboration/presence`
- `POST /api/v1/workflows/run`
- `GET /api/v1/observability`

Existing routes, including `/api/v1/enterprise/dashboard`, `/api/v1/dashboard`,
`/api/v1/board-meetings`, `/api/v1/business-data/providers`, and legacy `/api/v1/search`, remain
available.

## Configuration

RC5 does not require new provider secrets. It uses existing database, auth, provider, and deployment
settings.

Kubernetes deployments require a `boardroomai-secrets` Secret with:

- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_URL`
- `SESSION_SECRET`
- optional provider keys such as `MAPS_API_KEY`, `PLACES_API_KEY`, and `GDELT_API_KEY`

## Validation

Passed:

- `backend/.venv/Scripts/python -m pytest` - 32 passed
- `backend/.venv/Scripts/python -m ruff check .` - all checks passed
- `frontend/npm run typecheck` - passed
- `frontend/npm run lint` - passed
- `frontend/npm run build` - passed
- `docker compose config` - valid Compose output; Docker client warned that
  `C:\Users\Lenovo\.docker\config.json` was not readable
- `docker compose -f docker-compose.prod.yml config` - valid Compose output; same Docker client
  config warning
- `frontend/npm run desktop:pack` - passed; generated Windows NSIS and portable artifacts

Blocked:

- `docker compose build` could not run because the Docker Desktop Linux engine was unavailable:
  `npipe:////./pipe/dockerDesktopLinuxEngine` did not exist on this machine.

## Notes

- Document import does not fabricate unavailable evidence. Images are stored as metadata unless OCR
  is configured in a future provider.
- The Intelligence tab falls back to existing enterprise dashboard and meeting-history data if the
  RC5 intelligence endpoint is unavailable in an older backend.
- Enterprise role handling now includes Owner, Executive, and Guest while preserving the existing
  Founder, CEO, Administrator, Manager, Analyst, and Viewer roles.
