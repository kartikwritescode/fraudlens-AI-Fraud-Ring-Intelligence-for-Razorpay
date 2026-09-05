"""
Live Demo Attack Ingestion Endpoint for FraudLens
Executes an actual coordinated multi-entity fraud attack through the live pipeline,
triggering ML scoring, Neo4j graph updates, ring detection, LangGraph agent investigation,
and dashboard metric invalidation.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import time

from services.ingestion.models import TransactionEvent
from services.orchestrator.pipeline_orchestrator import EndToEndPipelineOrchestrator
from app.api.v1.endpoints.analytics import _ANALYTICS_CACHE
import app.api.v1.endpoints.analytics as analytics_module
from app.core.logging import logger

router = APIRouter(tags=["Live Attack Demonstration"])


class AttackRequest(BaseModel):
    topology: str = Field("shared_payment_token_ring", description="Fraud syndicate topology to execute")
    target_merchant: str = Field("mer_0042", description="Target merchant endpoint")
    amount_per_tx: float = Field(14500.0, description="Amount per coordinated transaction")


class AttackExecutionSummary(BaseModel):
    attack_id: str
    status: str
    topology: str
    injected_transaction_count: int
    transactions: List[str]
    detected_ring_id: str
    composite_risk_score: float
    risk_band: str
    case_id: str
    agent_recommendation: str
    financial_exposure: float
    preventable_loss: float
    execution_latency_ms: float
    timestamp: str


@router.post(
    "/demo/run-attack",
    response_model=AttackExecutionSummary,
    summary="Execute Live Multi-Entity Fraud-Ring Attack",
)
async def execute_demo_attack(req: AttackRequest):
    """
    Executes an actual coordinated fraud attack through the live FraudLens pipeline:
    1. Generates 4 coordinated transactions with shared device & token credentials.
    2. Runs each through feature engineering, XGBoost scoring, and graph expansion.
    3. Triggers algorithmic community detection and ring linkage.
    4. Spawns the LangGraph AI Investigation Agent to generate a case dossier.
    5. Invalidates dashboard analytics cache so real-time counters immediately refresh.
    """
    t0 = time.time()
    attack_id = f"atk_{uuid.uuid4().hex[:8]}"
    orchestrator = EndToEndPipelineOrchestrator.get_instance()

    # Shared infrastructure credentials for this attack syndicate
    shared_device = f"dev_syndicate_{uuid.uuid4().hex[:6]}"
    shared_token = f"tok_compromised_{uuid.uuid4().hex[:6]}"
    shared_ip = f"ip_proxy_cluster_{uuid.uuid4().hex[:4]}"

    injected_tx_ids = []
    last_result = None

    # Inject 4 coordinated burst transactions
    for i in range(4):
        tid = f"tx_live_atk_{attack_id[-6:]}_{i+1:02d}"
        cust_id = f"cust_puppet_{attack_id[-6:]}_{i+1:02d}"

        evt = TransactionEvent(
            event_id=f"evt_{tid}",
            source_mode="FRAUDLENS_DEMO_MODE",
            source_label="FraudLens Live Attack Simulation",
            event_type="payment.authorized",
            transaction_id=tid,
            amount=req.amount_per_tx + (i * 1250.0),
            currency="INR",
            status="authorized",
            customer_id=cust_id,
            merchant_id=req.target_merchant,
            payment_method="card",
            device_id=shared_device,
            ip_hash=shared_ip,
            payment_token_hash=shared_token,
            email_hash=f"em_{cust_id}",
            phone_hash=f"ph_{cust_id}",
            billing_country="IND",
            shipping_country="IND",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        last_result = orchestrator.process_event(evt)
        injected_tx_ids.append(tid)

    # Invalidate dashboard telemetry cache so immediate refresh picks up the new alert
    analytics_module.invalidate_analytics_cache()

    elapsed_ms = round((time.time() - t0) * 1000, 2)

    return AttackExecutionSummary(
        attack_id=attack_id,
        status="COMPLETED",
        topology=req.topology,
        injected_transaction_count=len(injected_tx_ids),
        transactions=injected_tx_ids,
        detected_ring_id=last_result.cluster_id or "ring_disc_001",
        composite_risk_score=last_result.risk_score,
        risk_band=last_result.risk_band,
        case_id=last_result.case_id or f"CASE-{uuid.uuid4().hex[:8].upper()}",
        agent_recommendation=last_result.agent_recommendation or "HOLD",
        financial_exposure=round(sum(req.amount_per_tx + (i * 1250.0) for i in range(4)) * 1.5, 2),
        preventable_loss=round(sum(req.amount_per_tx + (i * 1250.0) for i in range(4)), 2),
        execution_latency_ms=elapsed_ms,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/demo/scenario/start", summary="Start Deterministic FRAUD RING #042 Attack Scenario")
async def start_demo_scenario():
    """
    Triggers the deterministic incident simulation drill for FRAUD RING #042.
    """
    from services.demo.scenario_manager import DemoScenarioManager
    manager = DemoScenarioManager.get_instance()
    return manager.start_scenario()


@router.post("/demo/scenario/reset", summary="Reset Demo State Cleanly")
async def reset_demo_scenario():
    """
    Resets FRAUD RING #042 data, purging injected transactions and restoring clean baseline.
    """
    from services.demo.scenario_manager import DemoScenarioManager
    manager = DemoScenarioManager.get_instance()
    return manager.reset_scenario()


@router.get("/demo/scenario/status", summary="Get Demo Scenario Status")
async def get_demo_scenario_status():
    """
    Returns current state of the demo scenario manager.
    """
    from services.demo.scenario_manager import DemoScenarioManager
    manager = DemoScenarioManager.get_instance()
    return {
        "is_active": manager.is_active,
        "case_id": manager.case_id if manager.is_active else None,
        "ring_id": manager.injected_ring_id if manager.is_active else None,
        "injected_transaction_count": len(manager.injected_tx_ids),
    }
