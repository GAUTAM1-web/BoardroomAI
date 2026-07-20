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

Business intelligence works in demo and manual modes without provider keys. Live mode requires backend environment credentials. The Settings workspace shows redacted provider status and never exposes API keys.

## Desktop shell opens but data does not load

The Electron package runs the frontend, not PostgreSQL, Redis, Qdrant, or FastAPI. Start the backend stack locally or configure the desktop environment to point at a reachable backend.

## Offline mode

The app detects browser or desktop offline state and surfaces a notification. Read-only UI remains visible; backend actions should be retried after connectivity returns.

