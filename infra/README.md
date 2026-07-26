# Infrastructure Notes

BoardroomAI supports local, Docker, and public cloud deployment without changing API paths.

Local development uses Docker Compose:

- PostgreSQL as the only relational database
- Redis for diagnostics, future job orchestration, and event streaming
- Qdrant for strategic memory and retrieval
- FastAPI backend
- Next.js frontend

Production scaffolding:

- `docker-compose.prod.yml` for a production-shaped VM or local validation stack
- `Dockerfile.backend` for root-context cloud Docker builders
- `vercel.json` for the frontend
- `railway.toml` for backend deployment
- `render.yaml` for backend/frontend services
- `fly.toml` for backend deployment

The service boundaries remain Kubernetes-ready:

- stateless frontend
- stateless API workers
- separate async workers in a future milestone
- managed PostgreSQL
- managed Redis
- managed or self-hosted Qdrant
