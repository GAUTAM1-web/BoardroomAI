# Infrastructure Notes

Milestone 1 uses Docker Compose for local development:

- PostgreSQL as the only relational database
- Redis for future job orchestration and event streaming
- Qdrant for future strategic memory and retrieval
- FastAPI backend
- Next.js frontend

The service boundaries are Kubernetes-ready:

- stateless frontend
- stateless API workers
- separate async workers in a future milestone
- managed PostgreSQL
- managed Redis
- managed or self-hosted Qdrant

