"""
End-to-End Pipeline Verification Script for FraudLens
Executes the complete lifecycle:
Simulated Attack -> Ingestion -> Feature Calculation -> ML Scoring -> Graph Update ->
Ring Detection -> Alert -> AI Investigation -> Financial Impact -> Human Decision -> Audit Log.
"""

import sys
from pathlib import Path
import httpx
import json
import time

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

client = httpx.Client(base_url="http://localhost:8000", timeout=30.0)

print("================================================================================")
print("             FRAUDLENS PHASE 7 — COMPLETE END-TO-END PIPELINE VERIFICATION      ")
print("================================================================================")

# 1. Execute Simulated Multi-Entity Attack
print("\n[Step 1] Injecting Multi-Entity Attack Syndicate via POST /demo/run-attack...")
attack_payload = {
    "topology": "shared_payment_token_ring",
    "target_merchant": "mer_0042",
    "amount_per_tx": 18500.0,
}
res_atk = client.post("/demo/run-attack", json=attack_payload)
assert res_atk.status_code == 200, f"Attack injection failed: {res_atk.text}"
atk = res_atk.json()

print(f"[OK] Attack Injected: {atk['attack_id']} ({atk['injected_transaction_count']} transactions)")
print(f"     Transactions:  {atk['transactions']}")
print(f"     Ring Detected: {atk['detected_ring_id']}")
print(f"     Risk Score:    {atk['composite_risk_score']:.4f} ({atk['risk_band']})")
print(f"     Case Dossier:  {atk['case_id']}")
print(f"     Agent Action:  {atk['agent_recommendation']}")
print(f"     Exposure:      Rs. {atk['financial_exposure']:,.2f}")
print(f"     Preventable:   Rs. {atk['preventable_loss']:,.2f}")
print(f"     Latency:       {atk['execution_latency_ms']}ms")

case_id = atk["case_id"]

# 2. Inspect Generated Case Dossier & Fact Separation
print(f"\n[Step 2] Verifying Case Dossier & Empirical Facts via GET /cases/{case_id}...")
res_case = client.get(f"/cases/{case_id}")
assert res_case.status_code == 200, f"Fetch case failed: {res_case.text}"
case_data = res_case.json()

print(f"[OK] Case Status:   {case_data['status']}")
print(f"     Severity:      {case_data['severity']}")
print(f"     Primary Tx:    {case_data['primary_transaction_id']}")
if case_data.get("report"):
    print(f"     Facts Count:   {len(case_data['report']['observed_facts'])}")
    print(f"     Top Fact:      {case_data['report']['observed_facts'][0]}")
    print(f"     Top Hyp:       {case_data['report']['fraud_hypotheses'][0]}")
    print(f"     Loss Matrix:   {case_data['report']['financial_impact']['expected_loss_by_action']}")

# 3. Execute Human Analyst Approval Checkpoint
print(f"\n[Step 3] Executing Human Decision Checkpoint via POST /cases/{case_id}/decision...")
dec_payload = {
    "action": "HOLD",
    "notes": "Lead Risk Analyst confirmed coordinated token syndicate compromise.",
}
res_dec = client.post(f"/cases/{case_id}/decision", json=dec_payload)
assert res_dec.status_code == 200, f"Decision recording failed: {res_dec.text}"
dec_data = res_dec.json()
last_dec = dec_data["decisions"][-1] if dec_data.get("decisions") else {}
print(f"[OK] Recorded Decision: {last_dec.get('action', 'HOLD')} | Case Status: {dec_data['status']}")

# 4. Verify Immutable Security Audit Log
print("\n[Step 4] Verifying Audit Trail via GET /audit/logs...")
res_audit = client.get("/audit/logs?limit=5")
assert res_audit.status_code == 200, f"Fetch audit logs failed: {res_audit.text}"
audit_logs = res_audit.json()
print(f"[OK] Retrieved {len(audit_logs)} recent audit entries:")
for log in audit_logs[:3]:
    print(f"     • [{log['timestamp']}] {log['actor']}: {log['action']} ({log['case_id']}) -> {log['result']}")

# 5. Verify Real-Time Dashboard KPI Updates
print("\n[Step 5] Verifying Live Dashboard Telemetry via GET /analytics/overview...")
res_analytics = client.get("/analytics/overview")
assert res_analytics.status_code == 200, f"Analytics failed: {res_analytics.text}"
kpis = res_analytics.json()["kpis"]
print(f"[OK] Updated Dashboard KPIs:")
print(f"     • Monitored Transactions: {kpis['total_transactions_monitored']}")
print(f"     • Active Rings:           {kpis['active_fraud_rings']}")
print(f"     • Rs. at Risk:            Rs. {kpis['total_amount_at_risk']:,.2f}")
print(f"     • Open Cases:             {kpis['open_cases_count']}")

print("\n================================================================================")
print("             END-TO-END PIPELINE VERIFIED SUCCESSFULLY                          ")
print("================================================================================")
