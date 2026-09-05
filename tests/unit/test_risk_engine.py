"""
Unit Tests for ML Risk Engine & SHAP Explainability
"""

import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

# Add project root and apps/api to path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from ml.features.engineer import StreamingFeatureExtractor, FEATURE_NAMES
from services.risk_engine.inference import RiskScorer
from app.main import app


def test_feature_engineering_no_future_leakage():
    """Verify that feature calculation is strictly retrospective."""
    extractor = StreamingFeatureExtractor()

    tx1 = {
        "transaction_id": "tx_001",
        "timestamp": "2025-09-01T10:00:00Z",
        "customer_id": "c1",
        "merchant_id": "m1",
        "device_id": "d1",
        "ip_hash": "ip1",
        "payment_token_hash": "tok1",
        "amount": 1000.0,
        "status": "captured",
    }
    tx2 = {
        "transaction_id": "tx_002",
        "timestamp": "2025-09-01T10:02:00Z",
        "customer_id": "c1",
        "merchant_id": "m1",
        "device_id": "d1",
        "ip_hash": "ip1",
        "payment_token_hash": "tok1",
        "amount": 2000.0,
        "status": "captured",
    }

    f1 = extractor.extract_features_for_transaction(tx1, update_state=True)
    assert f1["cust_tx_count_5m"] == 0.0  # tx1 has 0 prior transactions
    assert f1["is_new_device"] == 1.0     # first time seeing d1

    f2 = extractor.extract_features_for_transaction(tx2, update_state=True)
    assert f2["cust_tx_count_5m"] == 1.0  # tx2 sees tx1 in prior 5m
    assert f2["is_new_device"] == 0.0     # d1 is now known for c1
    assert f2["amount_to_customer_median"] == 2.0  # 2000 / median(1000)


def test_model_artifact_loaded():
    """Verify that RiskScorer loads the trained artifact with expected attributes."""
    scorer = RiskScorer.get_instance()
    assert scorer.model is not None
    assert scorer.explainer is not None
    assert scorer.model_version == "v1.0.0-xgb"
    assert len(scorer.feature_names) == len(FEATURE_NAMES)
    assert "pr_auc" in scorer.metrics
    assert scorer.metrics["pr_auc"] > 0.40


def test_inference_and_shap_explainability():
    """Verify scoring and SHAP explanation generation."""
    scorer = RiskScorer.get_instance()

    suspicious_payload = {
        "transaction_id": "tx_test_suspicious",
        "timestamp": "2025-09-01T12:00:00Z",
        "customer_id": "c_sus",
        "merchant_id": "m_elec",
        "device_id": "d_test",
        "ip_hash": "ip_test",
        "payment_token_hash": "tok_test",
        "amount": 45000.0,
        "status": "captured",
        "billing_country": "IND",
        "shipping_country": "IND",
    }

    # Custom features simulating high velocity and hardware reuse
    custom_feats = {
        "amount": 45000.0,
        "amount_to_customer_median": 8.5,
        "amount_deviation": 39000.0,
        "cust_tx_count_5m": 4.0,
        "cust_tx_count_1h": 7.0,
        "cust_tx_count_24h": 12.0,
        "merchant_tx_count_1h": 45.0,
        "device_reuse_count": 8.0,
        "ip_reuse_count": 5.0,
        "payment_token_reuse_count": 6.0,
        "account_age_days": 0.0,
        "failed_payment_ratio": 0.50,
        "geographic_mismatch": 0.0,
        "unusual_transaction_hour": 1.0,
        "is_new_device": 1.0,
        "is_new_ip": 1.0,
        "has_previous_suspicious_activity": 1.0,
        "dev_distinct_cust_1h": 4.0,
        "is_card": 1.0,
        "is_high_ticket": 1.0,
    }

    result = scorer.assess_transaction(suspicious_payload, custom_features=custom_feats)
    assert 0.0 <= result.risk_score <= 1.0
    assert result.risk_score >= 0.40
    assert result.risk_band in ["MEDIUM", "HIGH", "CRITICAL"]
    assert len(result.reason_codes) > 0
    assert len(result.top_shap_contributions) > 0

    # Also verify ground truth fraud from index
    fraud_tx = next(t for t in scorer.tx_lookup.values() if t.get("is_fraud"))
    res_ftx = scorer.assess_by_transaction_id(fraud_tx["transaction_id"])
    assert res_ftx is not None
    assert 0.0 <= res_ftx.risk_score <= 1.0
    assert len(res_ftx.reason_codes) > 0


@pytest.mark.asyncio
async def test_api_get_transaction_risk():
    """Verify GET /transactions/{id}/risk endpoint returns RFC-compliant response."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Score a known transaction from index
        scorer = RiskScorer.get_instance()
        sample_id = next(iter(scorer.tx_lookup.keys()))

        response = await client.get(f"/transactions/{sample_id}/risk")
        assert response.status_code == 200
        data = response.json()
        assert data["transaction_id"] == sample_id
        assert "risk_score" in data
        assert "risk_band" in data
        assert "reason_codes" in data
        assert len(data["reason_codes"]) > 0


@pytest.mark.asyncio
async def test_api_get_transaction_risk_not_found():
    """Verify 404 response for unknown transaction ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/transactions/tx_non_existent_999999/risk")
        assert response.status_code == 404
        data = response.json()
        assert data["title"] == "ENTITY_NOT_FOUND"
