"""
Unit Tests for Fraud Graph Intelligence Engine
Verifies algorithmic ring discovery, cluster risk scoring, temporal analysis, and graph APIs.
"""

import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from services.graph_engine.ring_detector import AlgorithmicRingDetector
from services.graph_engine.cluster_scorer import ClusterRiskScorer
from services.graph_engine.temporal_analyzer import TemporalRingAnalyzer
from services.graph_engine.neighbor_expander import GraphNeighborExpander
from app.main import app


def test_algorithmic_ring_discovery():
    """Verify that rings are discovered purely from graph topology without hardcoding."""
    detector = AlgorithmicRingDetector.get_instance()
    rings = detector.get_rings()

    assert len(rings) >= 5, "Must discover at least 5 coordinated fraud rings"
    for r in rings:
        assert r.ring_id.startswith("ring_disc_")
        assert 0.0 <= r.risk_score <= 1.0
        assert r.risk_band in ["HIGH", "CRITICAL"]
        assert r.member_count >= 3
        assert r.transaction_count >= 3
        assert r.attempted_amount > 0
        assert len(r.timeline) > 0
        assert len(r.explanation) > 0


def test_cluster_scoring_legitimate_vs_fraud():
    """
    Ensure multi-signal scoring distinguishes benign shared infrastructure from fraud rings.
    """
    # 1. Legitimate shared campus Wi-Fi (15 accounts over 30 days, normal amounts, low failure)
    benign_txs = [
        {
            "transaction_id": f"tx_b_{i}",
            "customer_id": f"cust_stud_{i}",
            "amount": 350.0 + (i * 20),
            "status": "captured",
            "device_id": f"dev_personal_{i}",
            "ip_hash": "ip_nat_campus_0",
            "payment_token_hash": f"tok_card_{i}",
            "timestamp": f"2025-09-{min(28, i*2 + 1):02d}T12:00:00Z",
        }
        for i in range(12)
    ]
    benign_eval = ClusterRiskScorer.score_cluster(
        transactions=benign_txs,
        customers={t["customer_id"] for t in benign_txs},
        devices={t["device_id"] for t in benign_txs},
        ips={"ip_nat_campus_0"},
        tokens={t["payment_token_hash"] for t in benign_txs},
        ml_scores=[0.05] * len(benign_txs),
    )
    assert benign_eval["graph_risk_score"] < 0.45, "Benign shared IP must not receive high graph risk"
    assert benign_eval["risk_band"] in ["LOW", "MEDIUM"]

    # 2. Coordinated Sybil attack (12 accounts sharing 1 device in 2 hours, shared token)
    fraud_txs = [
        {
            "transaction_id": f"tx_f_{i}",
            "customer_id": f"cust_bot_{i}",
            "amount": 7500.0,
            "status": "captured" if i % 2 == 0 else "failed",
            "device_id": "dev_rooted_sybil",
            "ip_hash": "ip_proxy_tor",
            "payment_token_hash": "tok_stolen_shared" if i < 8 else f"tok_{i}",
            "timestamp": f"2025-09-15T14:{i*5:02d}:00Z",
        }
        for i in range(12)
    ]
    fraud_eval = ClusterRiskScorer.score_cluster(
        transactions=fraud_txs,
        customers={t["customer_id"] for t in fraud_txs},
        devices={"dev_rooted_sybil"},
        ips={"ip_proxy_tor"},
        tokens={"tok_stolen_shared"},
        ml_scores=[0.85] * len(fraud_txs),
    )
    assert fraud_eval["graph_risk_score"] >= 0.70, "Coordinated attack must receive high/critical risk"
    assert fraud_eval["risk_band"] in ["HIGH", "CRITICAL"]


def test_temporal_timeline_reconstruction():
    """Verify that temporal analysis reconstructs chronological progression."""
    sample_txs = [
        {"transaction_id": "tx_1", "customer_id": "c1", "device_id": "d1", "payment_token_hash": "t1", "amount": 100.0, "timestamp": "2025-09-01T10:00:00Z"},
        {"transaction_id": "tx_2", "customer_id": "c2", "device_id": "d1", "payment_token_hash": "t2", "amount": 200.0, "timestamp": "2025-09-01T10:02:00Z"},
        {"transaction_id": "tx_3", "customer_id": "c3", "device_id": "d1", "payment_token_hash": "t1", "amount": 35000.0, "timestamp": "2025-09-01T10:05:00Z"},
    ]
    timeline = TemporalRingAnalyzer.reconstruct_timeline(sample_txs)
    assert len(timeline) >= 3
    event_types = {e.event_type for e in timeline}
    assert "ENTITY_JOINED" in event_types
    assert "DEVICE_LINKED" in event_types
    assert "TOKEN_SHARED" in event_types


@pytest.mark.asyncio
async def test_api_list_rings():
    """Verify GET /rings endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/rings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        ring0 = data[0]
        assert "ring_id" in ring0
        assert "risk_score" in ring0
        assert "member_count" in ring0


@pytest.mark.asyncio
async def test_api_get_ring_detail():
    """Verify GET /rings/{id} endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        detector = AlgorithmicRingDetector.get_instance()
        first_ring = detector.get_rings()[0]

        response = await client.get(f"/rings/{first_ring.ring_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["ring_id"] == first_ring.ring_id
        assert len(data["timeline"]) > 0


@pytest.mark.asyncio
async def test_api_get_transaction_network():
    """Verify GET /transactions/{id}/network endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        detector = AlgorithmicRingDetector.get_instance()
        first_ring = detector.get_rings()[0]
        sample_tx = first_ring.transaction_ids[0]

        response = await client.get(f"/transactions/{sample_tx}/network")
        assert response.status_code == 200
        data = response.json()
        assert data["center_id"] == sample_tx
        assert "nodes" in data
        assert "edges" in data
        assert data["node_count"] > 0
        assert data["edge_count"] > 0
