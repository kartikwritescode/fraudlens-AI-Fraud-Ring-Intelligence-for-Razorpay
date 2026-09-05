"""
System Status & Capabilities Endpoints
Provides runtime architecture telemetry for the FraudLens Command Center.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from datetime import datetime, timezone
import platform
import sys

from app.core.config import settings

router = APIRouter(prefix="/system", tags=["System Telemetry"])


@router.get("/status", summary="System Architecture Status")
async def get_system_status() -> Dict[str, Any]:
    """Returns architecture overview, phase completion state, and active modules."""
    return {
        "product": {
            "name": settings.APP_NAME,
            "title": settings.APP_TITLE,
            "tagline": settings.APP_TAGLINE,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
        },
        "runtime": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "phases": [
            {
                "phase": 0,
                "name": "Foundation & Core Infrastructure",
                "status": "COMPLETED",
                "description": "Monorepo, Docker Compose, PostgreSQL & Neo4j schemas, FastAPI, Next.js Command Center shell.",
            },
            {
                "phase": 1,
                "name": "Synthetic Data & ML Risk Engine",
                "status": "NEXT",
                "description": "Transaction generator, 5 fraud ring patterns, XGBoost model, velocity features, SHAP reason codes.",
            },
            {
                "phase": 2,
                "name": "Fraud Graph Engine",
                "status": "PLANNED",
                "description": "Neo4j entity graph, multi-entity relationships, Louvain community detection, ring risk scoring.",
            },
            {
                "phase": 3,
                "name": "AI Investigation Agent",
                "status": "PLANNED",
                "description": "LangGraph investigation workflow, read-only tools, hypothesis testing, financial impact engine.",
            },
            {
                "phase": 4,
                "name": "Razorpay Integration & Simulation",
                "status": "PLANNED",
                "description": "Razorpay Test Mode webhooks, HMAC signature verification, live attack stream replay.",
            },
            {
                "phase": 5,
                "name": "Hardening & Demo Orchestration",
                "status": "PLANNED",
                "description": "Audit trail immutability, human-in-the-loop approvals, pitch scenario runner.",
            },
        ],
        "architecture_layers": [
            {"layer": "Ingestion Gateway", "tech": "FastAPI Webhooks / Replay", "status": "ONLINE"},
            {"layer": "Relational Storage", "tech": "PostgreSQL 16", "status": "INITIALIZED"},
            {"layer": "Graph Intelligence", "tech": "Neo4j 5.20 Bolt", "status": "INITIALIZED"},
            {"layer": "Risk Inference", "tech": "XGBoost + SHAP (Phase 1)", "status": "STANDBY"},
            {"layer": "Agent Orchestration", "tech": "LangGraph (Phase 3)", "status": "STANDBY"},
            {"layer": "Command Center UI", "tech": "Next.js 14 + Tailwind", "status": "ONLINE"},
        ],
    }
