"""
FraudLens FastAPI Main Application
Entrypoint for the API Gateway and Orchestrator.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path for services and ml imports
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone

from app.core.config import settings
from app.core.logging import logger
from app.core.errors import (
    FraudLensException,
    fraudlens_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.db.postgres import init_postgres, close_postgres
from app.db.neo4j import init_neo4j, close_neo4j
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events: initialize and tear down database pools gracefully."""
    logger.info(f"Starting {settings.APP_TITLE} (Env: {settings.APP_ENV})")

    # Non-blocking connection attempts on startup
    await init_postgres()
    await init_neo4j()

    # Pre-load ML Risk Model artifact and explainer
    try:
        from services.risk_engine.inference import RiskScorer
        scorer = RiskScorer.get_instance()
        scorer.prewarm_cache(limit=400)
        logger.info("ML Risk Engine, TreeSHAP explainer, and assessment cache loaded successfully.")
    except Exception as e:
        logger.warning(f"ML Risk Engine pre-loading deferred: {e}")

    # Pre-load Graph Intelligence Engine and Multi-Entity Index
    try:
        from services.graph_engine.ring_detector import AlgorithmicRingDetector
        from services.graph_engine.neighbor_expander import GraphNeighborExpander
        detector = AlgorithmicRingDetector.get_instance()
        GraphNeighborExpander.get_instance()
        logger.info("Graph Intelligence Engine & Subgraph Expander pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"Graph Intelligence Engine pre-loading deferred: {e}")

    # Pre-warm Analytics Overview and Transaction Feed Caches
    try:
        from app.api.v1.endpoints.analytics import get_analytics_overview, _build_feed_cache
        await get_analytics_overview()
        from services.risk_engine.inference import RiskScorer
        from services.graph_engine.ring_detector import AlgorithmicRingDetector
        _build_feed_cache(RiskScorer.get_instance(), AlgorithmicRingDetector.get_instance())
        logger.info("Command Center Analytics & Transaction Feed caches pre-warmed for instant (<1ms) response.")
    except Exception as e:
        logger.warning(f"Analytics pre-warming deferred: {e}")

    yield

    logger.info("Shutting down FraudLens API Gateway...")
    await close_postgres()
    await close_neo4j()
    logger.info("Graceful shutdown complete.")


app = FastAPI(
    title=settings.APP_TITLE,
    description="Enterprise AI Fraud-Ring Intelligence Platform for Razorpay — See the fraud behind the transaction.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Global Exception Handlers
app.add_exception_handler(FraudLensException, fraudlens_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Include v1 API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
# Also include health directly at root /health for convenience
from app.api.v1.endpoints.health import liveness_probe
from app.api.v1.endpoints.transactions import get_transaction_risk
from app.api.v1.endpoints.graph import list_fraud_rings, get_fraud_ring, get_transaction_network, get_entity_neighbors
from app.api.v1.endpoints.agent import trigger_investigation, get_case, record_human_decision
from app.api.v1.endpoints.webhooks import handle_razorpay_webhook
from app.api.v1.endpoints.analytics import get_analytics_overview, get_transactions_feed, get_audit_logs
from app.api.v1.endpoints.demo import execute_demo_attack
app.add_api_route("/health", liveness_probe, methods=["GET"], tags=["Health & Diagnostics"])
app.add_api_route("/transactions/{transaction_id}/risk", get_transaction_risk, methods=["GET"], tags=["Transaction Risk ML"])
app.add_api_route("/rings", list_fraud_rings, methods=["GET"], tags=["Fraud Graph Intelligence"])
app.add_api_route("/rings/{ring_id}", get_fraud_ring, methods=["GET"], tags=["Fraud Graph Intelligence"])
app.add_api_route("/transactions/{transaction_id}/network", get_transaction_network, methods=["GET"], tags=["Fraud Graph Intelligence"])
app.add_api_route("/entities/{entity_id}/neighbors", get_entity_neighbors, methods=["GET"], tags=["Fraud Graph Intelligence"])
app.add_api_route("/cases/investigate", trigger_investigation, methods=["POST"], tags=["AI Investigation Agent"])
app.add_api_route("/cases/{case_id}", get_case, methods=["GET"], tags=["AI Investigation Agent"])
app.add_api_route("/cases/{case_id}/decision", record_human_decision, methods=["POST"], tags=["AI Investigation Agent"])
app.add_api_route("/webhooks/razorpay", handle_razorpay_webhook, methods=["POST"], tags=["Payment Webhooks & Ingestion"])
app.add_api_route("/analytics/overview", get_analytics_overview, methods=["GET"], tags=["Analytics & Command Center Telemetry"])
app.add_api_route("/transactions/feed", get_transactions_feed, methods=["GET"], tags=["Analytics & Command Center Telemetry"])
app.add_api_route("/audit/logs", get_audit_logs, methods=["GET"], tags=["Analytics & Command Center Telemetry"])
from app.api.v1.endpoints.demo import execute_demo_attack, start_demo_scenario, reset_demo_scenario, get_demo_scenario_status
app.add_api_route("/demo/run-attack", execute_demo_attack, methods=["POST"], tags=["Live Attack Demonstration"])
app.add_api_route("/demo/scenario/start", start_demo_scenario, methods=["POST"], tags=["Live Attack Demonstration"])
app.add_api_route("/demo/scenario/reset", reset_demo_scenario, methods=["POST"], tags=["Live Attack Demonstration"])
app.add_api_route("/demo/scenario/status", get_demo_scenario_status, methods=["GET"], tags=["Live Attack Demonstration"])


@app.get("/", tags=["Root"])
async def root():
    """Root metadata response."""
    return {
        "brand": settings.APP_NAME,
        "title": settings.APP_TITLE,
        "tagline": settings.APP_TAGLINE,
        "version": settings.APP_VERSION,
        "status": "ONLINE",
        "docs": "/docs",
        "health": "/api/v1/health",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
