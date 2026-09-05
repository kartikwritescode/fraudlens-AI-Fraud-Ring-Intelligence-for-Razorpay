import httpx
import json

client = httpx.Client(base_url="http://localhost:8000", timeout=10.0)

with open("data/transactions_50k.json", "r", encoding="utf-8") as f:
    txs = json.load(f)["transactions"]

samples = [
    ("Account Takeover", next(t for t in txs if t["fraud_type"] == "account_takeover")),
    ("Shared Device Ring", next(t for t in txs if t["fraud_type"] == "shared_device_ring")),
    ("Velocity Attack", next(t for t in txs if t["fraud_type"] == "velocity_attack")),
    ("Card Testing Hit", next(t for t in txs if t["fraud_type"] == "testing_and_hit_attack")),
    ("Legitimate User", next(t for t in txs if not t["is_fraud"])),
]

print("========================================================")
print("       LIVE API TRANSACTION RISK SCORING & SHAP          ")
print("========================================================")

for category, tx in samples:
    tx_id = tx["transaction_id"]
    res = client.get(f"/transactions/{tx_id}/risk")
    assert res.status_code == 200, f"Failed {res.status_code}: {res.text}"
    data = res.json()
    print(f"\n>>> [{category.upper()}] ID: {tx_id}")
    print(f"    Risk Score:     {data['risk_score']} (Band: {data['risk_band']})")
    print(f"    Model Version:  {data['model_version']}")
    print(f"    Reason Codes:   {data['reason_codes']}")
    print(f"    Top SHAP:       {data['top_shap_contributions']}")

print("\n========================================================")
print("       TESTING POST /api/v1/transactions/score (Ad-hoc)  ")
print("========================================================")
adhoc_payload = {
    "transaction_id": "tx_adhoc_probe_2026",
    "merchant_id": "mer_0001",
    "customer_id": "cust_000001",
    "amount": 75000.0,
    "currency": "INR",
    "payment_method": "card",
    "status": "authorized",
    "device_id": "dev_rooted_9999",
    "ip_hash": "ip_tor_proxy_001",
    "email_hash": "em_adhoc_01",
    "phone_hash": "ph_adhoc_01",
    "payment_token_hash": "tok_stolen_01",
    "billing_country": "IND",
    "shipping_country": "ARE",
    "order_id": "ord_adhoc_01",
}
res_adhoc = client.post("/api/v1/transactions/score", json=adhoc_payload)
assert res_adhoc.status_code == 200
print(json.dumps(res_adhoc.json(), indent=2))
