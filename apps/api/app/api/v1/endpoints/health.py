"""
Health & Readiness Check Endpoints
Supports both shallow liveness probes and deep multi-service readiness probes.
"""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import asyncio

from app.core.config import settings
from app.db.postgres import check_postgres_health
from app.db.neo4j import check_neo4j_health

router = APIRouter(tags=["Health & Diagnostics"])


class DeepHealthResponse(BaseModel):
    status: str  # healthy, degraded, or unreachable
    timestamp: str
    app: str
    version: str
    environment: str
    services: Dict[str, Dict[str, Any]]


@router.get("/health/live", summary="Liveness Probe")
async def liveness_probe():
    """Returns HTTP 200 if FastAPI application process is alive."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health", response_model=DeepHealthResponse, summary="Deep Readiness Probe")
async def readiness_probe(response: Response):
    """
    Deep readiness probe checking PostgreSQL and Neo4j database connections concurrently.
    Mounted under /api/v1/health.
    """
    pg_task = asyncio.create_task(check_postgres_health())
    neo_task = asyncio.create_task(check_neo4j_health())

    pg_result, neo_result = await asyncio.gather(pg_task, neo_task)

    services = {
        "api": {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "port": settings.API_PORT,
        },
        "postgresql": pg_result,
        "neo4j": neo_result,
    }

    all_healthy = (
        pg_result.get("status") == "healthy" and
        neo_result.get("status") == "healthy"
    )
    any_healthy = (
        pg_result.get("status") == "healthy" or
        neo_result.get("status") == "healthy"
    )

    if all_healthy:
        overall_status = "healthy"
        response.status_code = status.HTTP_200_OK
    elif any_healthy:
        overall_status = "degraded"
        response.status_code = status.HTTP_200_OK
    else:
        overall_status = "degraded"  # Still return 200 so UI can inspect individual service diagnostics
        response.status_code = status.HTTP_200_OK

    return DeepHealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        services=services,
    )
