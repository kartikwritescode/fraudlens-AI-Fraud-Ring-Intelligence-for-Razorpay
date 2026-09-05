"""
Unit Tests for FraudLens AI Investigation Agent
Verifies controlled tools, deterministic financial calculations, LangGraph workflow,
and human-in-the-loop decision recording.
"""

import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from services.agent.tools import ControlledTools, CASE_STORE
from services.agent.impact_calculator import FinancialImpactCalculator
from services.agent.workflow import InvestigationAgent
from services.graph_engine.ring_detector import AlgorithmicRingDetector
from app.main import app


def test_controlled_tools_and_missing_data_handling():
    """Verify controlled tools return valid data and explicitly flag missing evidence."""
    # Known transaction
    detector = AlgorithmicRingDetector.get_instance()
    sample_tx = detector.get_rings()[0].transaction_ids[0]
    res_tx = ControlledTools.get_transaction(sample_tx)
    assert res_tx["status"] == "SUCCESS"
    assert res_tx["data"]["transaction_id"] == sample_tx

    # Missing transaction (never hallucinates)
    res_miss = ControlledTools.get_transaction("tx_does_not_exist_xyz")
    assert res_miss["status"] == "MISSING_DATA"
    assert res_miss["data"] is None

    # Missing customer history
    res_cust_miss = ControlledTools.get_customer_history("cust_imaginary_000")
    assert res_cust_miss["status"] == "MISSING_DATA"


def test_deterministic_financial_impact_calculations():
    """Verify that financial impact is calculated with pure Python arithmetic."""
    impact = FinancialImpactCalculator.calculate(
        amount=50000.0,
        risk_score=0.95,
        cluster_volume=200000.0,
        cluster_risk_score=0.90,
    )
    assert impact.attempted_fraud_value == 50000.0
    assert impact.suspicious_value > 50000.0
    assert impact.estimated_exposure > 50000.0
    assert "ALLOW" in impact.expected_loss_by_action
    assert "HOLD" in impact.expected_loss_by_action
    # High risk of 0.95 should make HOLD have lower expected loss than ALLOW
    assert impact.expected_loss_by_action["HOLD"] < impact.expected_loss_by_action["ALLOW"]


def test_langgraph_investigation_workflow_execution():
    """Verify complete LangGraph investigation workflow from Alert to Case."""
    detector = AlgorithmicRingDetector.get_instance()
    sample_tx = detector.get_rings()[0].transaction_ids[0]

    agent = InvestigationAgent()
    state = agent.investigate(sample_tx)

    assert state.status == "COMPLETED"
    assert state.case_id is not None
    assert len(state.tool_trace) >= 8
    assert state.report is not None

    # Check strict separation of FACT, HYPOTHESIS, and RECOMMENDATION
    report = state.report
    assert any(f.startswith("FACT:") for f in report.observed_facts)
    assert any(h.startswith("HYPOTHESIS:") for h in report.fraud_hypotheses)
    assert report.recommended_action in ["ALLOW", "MONITOR", "STEP_UP", "REVIEW", "HOLD"]
    assert 0.0 <= report.confidence <= 1.0


@pytest.mark.asyncio
async def test_api_investigate_and_human_decision_flow():
    """Verify HTTP API endpoint for running agent investigation and recording approval."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        detector = AlgorithmicRingDetector.get_instance()
        sample_tx = detector.get_rings()[0].transaction_ids[0]

        # 1. Trigger Investigation
        resp = await client.post("/cases/investigate", json={"transaction_id": sample_tx})
        assert resp.status_code == 200
        case_data = resp.json()
        case_id = case_data["case_id"]
        assert case_id.startswith("CASE-")
        assert case_data["status"] in ["OPEN", "UNDER_REVIEW"]
        assert case_data["report"] is not None

        # 2. Retrieve Case Dossier
        resp_get = await client.get(f"/cases/{case_id}")
        assert resp_get.status_code == 200
        assert resp_get.json()["case_id"] == case_id

        # 3. Human Analyst Decision Sign-off
        decision_payload = {
            "action": case_data["report"]["recommended_action"],
            "reviewer_id": "senior_analyst_raj",
            "notes": "Verified shared device and token across cluster; action approved.",
        }
        resp_dec = await client.post(f"/cases/{case_id}/decision", json=decision_payload)
        assert resp_dec.status_code == 200
        updated_case = resp_dec.json()
        assert updated_case["report"]["approval_status"] == "APPROVED"
        assert len(updated_case["decisions"]) >= 1
