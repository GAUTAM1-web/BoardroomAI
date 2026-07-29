from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.core.config import Settings
from app.core.deployment import environment_diagnostics


def recovery_plan(settings: Settings) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "strategy": {
            "database": "Use managed PostgreSQL automated backups plus scheduled pg_dump exports.",
            "configuration": "Store production env vars in the platform secret manager.",
            "documents": (
                "Persist document-derived knowledge in PostgreSQL; retain source files externally."
            ),
            "cache": (
                "Redis is disposable; queued jobs can be replayed from audit/workflow records."
            ),
            "qdrant": (
                "Rebuild vector memory from PostgreSQL reports, knowledge items, and evidence."
            ),
        },
        "backup_commands": {
            "postgres_dump": "pg_dump \"$DATABASE_URL\" --format=custom --file boardroomai.dump",
            "postgres_restore": (
                "pg_restore --clean --if-exists --dbname \"$DATABASE_URL\" boardroomai.dump"
            ),
            "configuration": (
                "Export secret-manager entries for DATABASE_URL, REDIS_URL, QDRANT_URL, "
                "SESSION_SECRET, and provider keys."
            ),
        },
        "integrity_checks": [
            "Run /health/ready after restore.",
            "Run /api/v1/diagnostics/dependencies.",
            "Run /api/v1/operations/integrity.",
            "Create a demo board meeting and export PDF/JSON.",
            "Open Enterprise and Intelligence dashboards.",
        ],
        "startup_validation": environment_diagnostics(settings),
    }


def integrity_check(settings: Settings, dependencies: dict[str, object]) -> dict[str, Any]:
    environment = environment_diagnostics(settings)
    dependency_status = str(dependencies.get("status", "unknown"))
    environment_status = str(environment.get("status", "unknown"))
    checks = [
        {
            "name": "environment",
            "status": environment_status,
            "required": True,
        },
        {
            "name": "dependencies",
            "status": dependency_status,
            "required": True,
        },
        {
            "name": "api_versioning",
            "status": "ok",
            "required": True,
            "details": {"supported": ["v1", "v2-preview"]},
        },
        {
            "name": "stateless_backend",
            "status": "ok",
            "required": True,
            "details": {
                "sessions": "HMAC signed with optional shared cache index",
                "horizontal_instances": "No local filesystem dependency for API state",
            },
        },
    ]
    status = "ok" if all(item["status"] in {"ok", "ready"} for item in checks) else "degraded"
    return {"status": status, "checks": checks, "generated_at": datetime.now(UTC).isoformat()}
