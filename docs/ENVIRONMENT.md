# Environment Reference

The backend reads `.env` from the repo root and `backend/.env`. The frontend reads standard Next.js
environment variables during build/runtime.

## Deployment

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `development`, `staging`, or `production`. Enables secure cookies in production. |
| `DEPLOYMENT_TARGET` | `auto`, `local`, `docker`, `vercel`, `railway`, `render`, or `fly.io`. |
| `PUBLIC_FRONTEND_URL` | Browser-facing frontend origin for CORS and diagnostics. |
| `PUBLIC_API_URL` | Browser-facing API origin for diagnostics and docs. |
| `FRONTEND_BASE_URL` | Compatibility frontend origin used by CORS. |
| `API_INTERNAL_BASE_URL` | Server-side Next.js proxy target for `/api/v1/*`. |
| `NEXT_PUBLIC_API_BASE_URL` | Browser-visible API origin. Leave blank for same-origin proxy mode. |
| `NEXT_PUBLIC_WS_BASE_URL` | Browser-visible WebSocket origin. |
| `NEXT_PUBLIC_GITHUB_URL` | Optional portfolio repository link on the landing page. |

## Auth

| Variable | Purpose |
| --- | --- |
| `SESSION_SECRET` | HMAC secret for stateless sessions. Use a long random value in production. |
| `SESSION_COOKIE_NAME` | Cookie name, default `boardroom_session`. |
| `SESSION_TTL_SECONDS` | Session lifetime, default seven days. |
| `AUTH_EMAIL_ENABLED` | Enables passwordless email-style demo login endpoint. |
| `AUTH_DEMO_ENABLED` | Enables demo account login. |
| `AUTH_GUEST_ENABLED` | Enables read-only guest mode. |
| `OAUTH_GOOGLE_ENABLED` | Exposes Google as OAuth-ready when configured. |
| `GOOGLE_CLIENT_ID` | Google OAuth client id placeholder. |
| `DEMO_CONTENT_ENABLED` | Seeds portfolio demo records in the default workspace. |

## Security And Data

| Variable | Purpose |
| --- | --- |
| `RATE_LIMIT_PER_MINUTE` | Lightweight per-client API throttle. Set `0` to disable. |
| `SECURITY_HEADERS_ENABLED` | Adds browser security headers when true. |
| `DATABASE_URL` | Async SQLAlchemy PostgreSQL URL. |
| `REDIS_URL` | Redis URL for dependency diagnostics and future queues/cache. |
| `QDRANT_URL` | Qdrant URL for dependency diagnostics and memory layer. |

## Providers

Provider variables remain backend-only. The browser receives provider names, health, and boolean
configuration status, never secret values.

See `.env.example` and `.env.production.example` for the full provider list.
