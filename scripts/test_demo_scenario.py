"""
Verification Script for Deterministic FRAUD RING #042 Hackathon Demo
Tests startScenario(), resetScenario(), verifies the 37 customers, 5 devices,
3 IPs, 2 tokens, 4 merchants, ~Rs. 8-9 Lakh volume, LangGraph case dossier,
and reliable reset.
"""

import sys
from pathlib import Path
import httpx

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

client = httpx.Client(base_url="http://localhost:8000", timeout=30.0)

print("================================================================================")
print("             FRAUDLENS PHASE 8 — FRAUD RING #042 DEMO VERIFICATION              ")
print("================================================================================")

# Run 1: Test Clean Baseline Reset
print("\n[Test 1] Executing POST /demo/scenario/reset to establish clean baseline...")
res_rst = client.post("/demo/scenario/reset")
assert res_rst.status_code == 200, f"Reset failed: {res_rst.text}"
print(f"[OK] {res_rst.json()['message']}")

# Run 1: Start Scenario
print("\n[Test 2] Executing POST /demo/scenario/start (Deterministic Wave 1 & Wave 2)...")
res_start = client.post("/demo/scenario/start")
assert res_start.status_code == 200, f"Start failed: {res_start.text}"
data = res_start.json()

print(f"[OK] Scenario Started:   {data['scenario']}")
print(f"     Ring ID:           {data['ring_id']} (Risk: {data['risk_band']})")
print(f"     Customers:         {data['customers']} (Expected 37)")
print(f"     Devices:           {data['devices']} (Expected 5)")
print(f"     IP Ranges:         {data['ips']} (Expected 3)")
print(f"     Payment Tokens:    {data['payment_tokens']} (Expected 2)")
print(f"     Merchants:         {data['merchants']} (Expected 4)")
print(f"     Attempted Volume:  Rs. {data['attempted_volume_inr']:,.2f} (Target ~8-9L)")
print(f"     Case Dossier ID:   {data['case_id']}")
print(f"     Recommendation:    {data['recommended_action']} (Confidence: {data['confidence']*100:.0f}%)")

assert data["customers"] == 37
assert data["devices"] == 5
assert data["ips"] == 3
assert data["payment_tokens"] == 2
assert data["merchants"] == 4
assert 750000.0 <= data["attempted_volume_inr"] <= 950000.0
assert data["ring_id"] == "FRAUD RING #042"
assert data["case_id"] == "CASE-0042"

# Run 1: Verify Case Dossier
print("\n[Test 3] Fetching Case Dossier GET /cases/CASE-0042...")
res_case = client.get("/cases/CASE-0042")
assert res_case.status_code == 200, f"Fetch case failed: {res_case.text}"
case_data = res_case.json()
print(f"[OK] Case Title:        {case_data['title']}")
print(f"     Severity:          {case_data['severity']}")
print(f"     Associated Txs:    {len(case_data['associated_transactions'])} transactions")
print(f"     Observed Facts:    {len(case_data['report']['observed_facts'])} facts compiled")

# Run 1: Approve Action
print("\n[Test 4] Approving Case Decision via POST /cases/CASE-0042/decision...")
res_dec = client.post(
    "/cases/CASE-0042/decision",
    json={"action": "STEP_UP", "notes": "Lead Risk Analyst approved STEP-UP challenge."},
)
assert res_dec.status_code == 200, f"Decision recording failed: {res_dec.text}"
print(f"[OK] Case Decision Recorded. Approval Status: {res_dec.json()['report']['approval_status']}")

# Run 2: Test Reset Idempotency & Repeatability
print("\n[Test 5] Testing Clean Reset & Zero Memory Ghosting via POST /demo/scenario/reset...")
res_rst2 = client.post("/demo/scenario/reset")
assert res_rst2.status_code == 200
print(f"[OK] Second Reset Completed: {res_rst2.json()['message']}")

# Verify CASE-0042 is purged
res_case_check = client.get("/cases/CASE-0042")
print(f"[OK] Post-Reset GET /cases/CASE-0042 returns: {res_case_check.status_code} (Expected 404 Entity Not Found)")
assert res_case_check.status_code == 404

# Run 3: Start Again (Confirm Repeatability without restart)
print("\n[Test 6] Re-executing POST /demo/scenario/start to confirm repeatability...")
res_start2 = client.post("/demo/scenario/start")
assert res_start2.status_code == 200
print(f"[OK] Scenario Re-executed Cleanly: {res_start2.json()['ring_id']} (Rs. {res_start2.json()['attempted_volume_inr']:,.2f})")

print("\n================================================================================")
print("             FRAUD RING #042 DEMO SCENARIO VERIFIED 100% RELIABLE               ")
print("================================================================================")
