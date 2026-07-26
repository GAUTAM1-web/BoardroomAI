# Troubleshooting

## Backend unavailable

Symptoms:

- Dashboard shows a friendly workspace error
- Live meetings fail to connect
- Exports do not open

Recovery:

```powershell
docker compose ps
docker compose up -d
```

Then retry from the app. The UI also offers a copyable diagnostics block.

## Database unavailable or not migrated

Symptoms:

- API returns `503`
- Message mentions database schema or Alembic migrations

Recovery:

```powershell
cd backend
..\.venv\Scripts\python -m alembic upgrade head
```

If running through Docker, rebuild and restart the stack.

## Provider unavailable

Business intelligence works in demo and manual modes without provider keys. Live mode attempts enabled public providers and configured backend providers, then continues with warnings when a source is disabled, slow, or unavailable.

Recovery:

- Open Settings and check Provider Health for status, latency, cache hits, and redacted errors.
- Use Retry providers to clear the in-memory live-data cache and refresh diagnostics.
- Set a provider variable to `none` to disable a connector cleanly.
- Confirm `PROVIDER_USER_AGENT`, `LIVE_DATA_TIMEOUT_SECONDS`, and provider-specific keys are set in the backend environment when required.

Provider secrets are never returned to the browser or Electron renderer.

## Desktop shell opens but data does not load

The Electron package runs the frontend, not PostgreSQL, Redis, Qdrant, or FastAPI. Start the backend stack locally or configure the desktop environment to point at a reachable backend.

## Production API points at localhost

Symptoms:

- Public frontend loads but API calls fail in the browser
- Network panel shows `localhost:8000` from a hosted site

Recovery:

- Set `NEXT_PUBLIC_API_BASE_URL` to the public backend URL for split-host production.
- Set `NEXT_PUBLIC_WS_BASE_URL` to the matching `wss://` backend URL.
- Keep `API_INTERNAL_BASE_URL` set for same-origin proxy builds or Docker.
- Check `/api/v1/diagnostics/environment` for detected deployment target and public URLs.

## Demo workspace is empty

Fresh workspaces seed portfolio demo content only when `DEMO_CONTENT_ENABLED=true`. Confirm the
backend environment and run migrations. Existing workspaces are not duplicated; the seed is
idempotent.

## Login or logout fails

Check `GET /api/v1/auth/config` to confirm enabled modes. In production, set a long
`SESSION_SECRET` and serve the API over HTTPS so secure cookies can round-trip.

## Offline mode

The app detects browser or desktop offline state and surfaces a notification. Read-only UI remains visible; backend actions should be retried after connectivity returns.
