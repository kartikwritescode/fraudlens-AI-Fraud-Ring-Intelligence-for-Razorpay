"""
Phase 9 Reliability & Security Hardening Test Suite for FraudLens
Tests resilience across failure modes:
1. Webhook duplicates & signature failures
2. Database & Neo4j graceful degradation
3. Cypher injection defense
4. Agent tool error handling & missing data resilience
5. Empty graph & zero fraud ring handling
6. False-positive benign transaction evaluation
7. Analyst route authentication
"""

import pytest
import hmac
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from services.ingestion.razorpay_adapter import RazorpayEventAdapter
from services.ingestion.pipeline import PipelineOrchestrator
from services.ingestion.models import TransactionEvent
from services.graph_engine.ring_detector import AlgorithmicRingDetector
from services.risk_engine.inference import RiskScorer
from services.agent.tools import ControlledTools
from services.agent.workflow import InvestigationAgent
from app.db.neo4j import check_neo4j_health
from app.db.postgres import check_postgres_health
from app.core.auth import verify_analyst_auth
from app.core.errors import AuthenticationFailedError


def test_webhook_duplicate_idempotency():
    """Verify that repeat webhook events with same event_id are deduplicated."""
    orchestrator = PipelineOrchestrator.get_instance()
    evt = TransactionEvent(
        event_id="evt_test_idempotent_01",
        source_mode="RAZORPAY_TEST_MODE",
        source_label="Razorpay Webhook",
        event_type="payment.authorized",
        transaction_id="pay_test_idemp_01",
        amount=1250.0,
        currency="INR",
        status="authorized",
        customer_id="cust_idemp_01",
        merchant_id="mer_0001",
        payment_method="card",
        device_id="dev_idemp_01",
        ip_hash="ip_idemp_01",
        payment_token_hash="tok_idemp_01",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    # First attempt
    res1 = orchestrator.process_event(evt)
    assert res1.is_duplicate is False

    # Second attempt with same event_id
    res2 = orchestrator.process_event(evt)
    assert res2.is_duplicate is True


def test_webhook_signature_failure():
    """Verify that tampering with body or signature fails verification."""
    raw_body = '{"event":"payment.authorized"}'
    fake_sig = "deadbeef0000111122223333444455556666777788889999aaaabbbbccccdddd"
    secret = "rzp_test_sec_42"

    is_valid = RazorpayEventAdapter.verify_webhook_signature(raw_body.encode("utf-8"), fake_sig, secret)
    assert is_valid is False


def test_cypher_injection_defense():
    """Verify that malicious Cypher injection strings are safely treated as literal strings."""
    malicious_id = "cust_001' OR '1'='1' RETURN * //"
    res = ControlledTools.get_graph_neighbors(malicious_id)
    assert res["status"] in ["OK", "EMPTY", "MISSING_DATA"]
    # Ensure it didn't return all nodes in database
    data = res.get("data") or []
    assert len(data) <= 10


def test_database_graceful_degradation_probe():
    """Verify health probes report unreachable/degraded cleanly without unhandled exceptions."""
    import asyncio
    neo4j_health = asyncio.run(check_neo4j_health())
    assert "status" in neo4j_health
    assert neo4j_health["status"] in ["healthy", "unreachable", "degraded"]

    pg_health = asyncio.run(check_postgres_health())
    assert "status" in pg_health
    assert pg_health["status"] in ["healthy", "unreachable", "degraded"]


def test_agent_tool_missing_entity_resilience():
    """Verify controlled tools gracefully handle missing entity IDs without throwing."""
    res_tx = ControlledTools.get_transaction("tx_does_not_exist_999")
    assert res_tx["status"] in ["NOT_FOUND", "MISSING_DATA"]

    res_cust = ControlledTools.get_customer_history("cust_ghost_000")
    assert res_cust["status"] in ["NOT_FOUND", "EMPTY", "MISSING_DATA"]

    res_cluster = ControlledTools.get_cluster("ring_does_not_exist")
    assert res_cluster["status"] in ["NOT_FOUND", "MISSING_DATA"]


def test_agent_investigation_graceful_fallback():
    """Verify that LangGraph workflow completes cleanly even on non-existent transaction."""
    agent = InvestigationAgent()
    state = agent.investigate("tx_missing_sample_01")
    assert state.case_id is not None
    assert state.recommendation in ["ALLOW", "MONITOR", "STEP_UP", "REVIEW", "HOLD"]
    assert state.confidence > 0.0


def test_benign_customer_false_positive_evaluation():
    """Verify that a legitimate customer transaction produces LOW risk and ALLOW recommendation."""
    scorer = RiskScorer.get_instance()
    benign_tx = {
        "transaction_id": "tx_benign_sample_01",
        "amount": 450.0,
        "currency": "INR",
        "status": "authorized",
        "customer_id": "cust_legit_repeat_01",
        "merchant_id": "mer_0001",
        "payment_method": "upi",
        "device_id": "dev_trusted_personal_01",
        "ip_hash": "ip_trusted_home_01",
        "payment_token_hash": "tok_personal_upi_01",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    res = scorer.assess_transaction(benign_tx, update_state=False)
    assert res.risk_score < 0.35
    assert res.risk_band == "LOW"


def test_analyst_auth_validation():
    """Verify analyst authentication dependency enforces credentials."""
    import asyncio

    # Valid key
    auth_valid = asyncio.run(verify_analyst_auth(x_analyst_key="fraudlens_demo_analyst_2026"))
    assert auth_valid["role"] == "LEAD_RISK_ANALYST"

    # Invalid key
    with pytest.raises(AuthenticationFailedError):
        asyncio.run(verify_analyst_auth(x_analyst_key="invalid_bad_key_123"))
