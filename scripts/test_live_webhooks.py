import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / 'apps' / 'api'))
import httpx
import hmac
import hashlib
import json

from app.core.config import settings

client = httpx.Client(base_url="http://localhost:8000", timeout=15.0)

print("================================================================================")
print("             FRAUDLENS PHASE 5 — RAZORPAY TEST MODE WEBHOOK VERIFICATION        ")
print("================================================================================")

def sign(payload_bytes: bytes, secret: str = settings.RAZORPAY_WEBHOOK_SECRET) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

# 1. Valid Webhook Test (Razorpay Test Mode)
print("\n[Test 1] POST /webhooks/razorpay with Valid HMAC Signature...")
payload1 = {
    "entity": "event",
    "account_id": "acc_rzp_test_54321",
    "event": "payment.authorized",
    "contains": ["payment"],
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_test_rzp_live_001",
                "entity": "payment",
                "amount": 7500000,  # Rs. 75,000.00
                "currency": "INR",
                "status": "authorized",
                "order_id": "order_rzp_live_01",
                "method": "card",
                "card_id": "card_test_visa_01",
                "email": "priya.sharma@example.com",
                "contact": "+919876543210",
                "notes": {
                    "device_id": "dev_test_macbook_01",
                    "ip_hash": "ip_test_nat_01",
                },
                "created_at": 1725365000,
            }
        }
    },
    "created_at": 1725365000,
}
body1 = json.dumps(payload1).encode("utf-8")
sig1 = sign(body1)

res1 = client.post(
    "/webhooks/razorpay",
    content=body1,
    headers={"X-Razorpay-Signature": sig1, "Content-Type": "application/json"},
)
assert res1.status_code == 200, f"Error: {res1.text}"
d1 = res1.json()
print(f"[OK] Status: 200 OK | Transaction: {d1['transaction_id']}")
print(f"     Source Label:  {d1['source_label']}")
print(f"     Risk Score:    {d1['risk_score']:.4f} (Band: {d1['risk_band']})")
print(f"     Alert Trigger: {d1['alert_triggered']} (Case ID: {d1.get('case_id')})")
print(f"     Reason Codes:  {d1['reason_codes']}")

# 2. Invalid Signature Test (Rejection)
print("\n[Test 2] POST /webhooks/razorpay with Tampered Signature...")
fake_sig = "tampered_fake_signature_99999999999999999999"
res2 = client.post(
    "/webhooks/razorpay",
    content=body1,
    headers={"X-Razorpay-Signature": fake_sig, "Content-Type": "application/json"},
)
print(f"[OK] Response: {res2.status_code} (Expected 401)")
print(f"     Error Title:  {res2.json()['title']}")
print(f"     Error Detail: {res2.json()['detail']}")
assert res2.status_code == 401

# 3. Duplicate Webhook Test (Idempotency)
print("\n[Test 3] POST /webhooks/razorpay Duplicate Delivery (Idempotency)...")
res3 = client.post(
    "/webhooks/razorpay",
    content=body1,
    headers={"X-Razorpay-Signature": sig1, "Content-Type": "application/json"},
)
assert res3.status_code == 200
d3 = res3.json()
print(f"[OK] Response: {res3.status_code} 200 OK")
print(f"     Is Duplicate:  {d3['is_duplicate']}")
print(f"     Notice:        {d3['reason_codes']}")
assert d3["is_duplicate"] == True

# 4. Malformed Payload Test (Validation)
print("\n[Test 4] POST /webhooks/razorpay with Malformed Payload...")
malformed_body = b"NOT_JSON_BODY{xyz"
sig_mal = sign(malformed_body)
res4 = client.post(
    "/webhooks/razorpay",
    content=malformed_body,
    headers={"X-Razorpay-Signature": sig_mal, "Content-Type": "application/json"},
)
print(f"[OK] Response: {res4.status_code} (Expected 400)")
print(f"     Error Title:  {res4.json()['title']}")
print(f"     Error Detail: {res4.json()['detail']}")
assert res4.status_code == 400

# 5. Dual Mode Test: Synthetic Universe Event Processing
print("\n[Test 5] POST /api/v1/events/synthetic Dual-Mode Pipeline Ingestion...")
synth_payload = {
    "transaction_id": "tx_synth_dual_mode_777",
    "amount": 42000.0,
    "currency": "INR",
    "status": "captured",
    "customer_id": "cust_demo_888",
    "merchant_id": "mer_0005",
    "device_id": "dev_rooted_demo",
    "ip_hash": "ip_proxy_demo",
    "payment_token_hash": "tok_stolen_demo",
}
res5 = client.post("/api/v1/events/synthetic", json=synth_payload)
assert res5.status_code == 200
d5 = res5.json()
print(f"[OK] Status: 200 OK | Transaction: {d5['transaction_id']}")
print(f"     Source Label:  {d5['source_label']}")
print(f"     Risk Score:    {d5['risk_score']:.4f} (Band: {d5['risk_band']})")
print(f"     Alert Trigger: {d5['alert_triggered']}")
print(f"     Reason Codes:  {d5['reason_codes']}")
print("================================================================================\n")
