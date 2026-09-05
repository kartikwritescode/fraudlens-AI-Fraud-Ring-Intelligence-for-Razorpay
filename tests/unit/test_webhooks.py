"""
Unit Tests for Razorpay Webhook Ingestion & Pipeline Orchestration
Tests signature validation, invalid signatures, idempotency deduplication,
malformed payloads, and end-to-end pipeline execution.
"""

import pytest
from httpx import AsyncClient, ASGITransport
import hmac
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from app.core.config import settings
from app.main import app
from services.ingestion.pipeline import PipelineOrchestrator, EVENT_STORE


def generate_test_signature(body: bytes, secret: str = settings.RAZORPAY_WEBHOOK_SECRET) -> str:
    """Helper to compute valid HMAC SHA256 signature."""
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def sample_razorpay_payload(pay_id: str = "pay_test_1001", amount_paise: int = 450000) -> Dict:
    return {
        "entity": "event",
        "account_id": "acc_test_12345",
        "event": "payment.authorized",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": pay_id,
                    "entity": "payment",
                    "amount": amount_paise,
                    "currency": "INR",
                    "status": "authorized",
                    "order_id": "order_test_99",
                    "method": "card",
                    "card_id": "card_test_tok_01",
                    "email": "test.shopper@example.com",
                    "contact": "+919988776655",
                    "notes": {
                        "device_id": "dev_test_mobile_01",
                        "ip_hash": "ip_test_49_204",
                    },
                    "created_at": 1725360000,
                }
            }
        },
        "created_at": 1725360000,
    }


@pytest.mark.asyncio
async def test_valid_razorpay_webhook_signature():
    """Verify that a validly signed Razorpay webhook is accepted and processed."""
    payload = sample_razorpay_payload(pay_id="pay_test_valid_01", amount_paise=500000)
    raw_body = json.dumps(payload).encode("utf-8")
    sig = generate_test_signature(raw_body)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/webhooks/razorpay",
            content=raw_body,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_id"] == "pay_test_valid_01"
        assert data["source_label"] == "Razorpay Test Event"
        assert not data["is_duplicate"]
        assert 0.0 <= data["risk_score"] <= 1.0


@pytest.mark.asyncio
async def test_invalid_signature_rejection():
    """Verify that an invalid or forged webhook signature is rejected with HTTP 401."""
    payload = sample_razorpay_payload(pay_id="pay_test_tamper_01")
    raw_body = json.dumps(payload).encode("utf-8")
    fake_sig = "invalid_tampered_signature_hex_0123456789abcdef"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/webhooks/razorpay",
            content=raw_body,
            headers={"X-Razorpay-Signature": fake_sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 401
        data = resp.json()
        assert data["title"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_duplicate_webhook_idempotency():
    """Verify that delivering the same webhook twice returns an idempotent duplicate status."""
    payload = sample_razorpay_payload(pay_id="pay_test_idempotent_01")
    raw_body = json.dumps(payload).encode("utf-8")
    sig = generate_test_signature(raw_body)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First Delivery
        resp1 = await client.post(
            "/webhooks/razorpay",
            content=raw_body,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp1.status_code == 200
        assert not resp1.json()["is_duplicate"]

        # Duplicate Delivery
        resp2 = await client.post(
            "/webhooks/razorpay",
            content=raw_body,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["is_duplicate"]


@pytest.mark.asyncio
async def test_malformed_webhook_payload():
    """Verify that malformed JSON is rejected with HTTP 400."""
    malformed_body = b"NOT_A_VALID_JSON{abc:123"
    sig = generate_test_signature(malformed_body)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/webhooks/razorpay",
            content=malformed_body,
            headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["title"] == "VALIDATION_FAILED"


@pytest.mark.asyncio
async def test_synthetic_event_dual_mode_processing():
    """Verify that FraudLens synthetic events enter the same pipeline labeled appropriately."""
    synth_payload = {
        "transaction_id": "tx_demo_synthetic_999",
        "amount": 25000.0,
        "currency": "INR",
        "status": "captured",
        "customer_id": "cust_demo_01",
        "merchant_id": "mer_0001",
        "device_id": "dev_demo_01",
        "ip_hash": "ip_demo_01",
        "payment_token_hash": "tok_demo_01",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/events/synthetic", json=synth_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_id"] == "tx_demo_synthetic_999"
        assert data["source_label"] == "FraudLens Synthetic Event"
        assert 0.0 <= data["risk_score"] <= 1.0
