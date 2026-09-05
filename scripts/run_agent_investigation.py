import httpx
import json

client = httpx.Client(base_url="http://localhost:8000", timeout=30.0)

# Pick a transaction from an actual synthetic fraud ring
with open("data/transactions_50k.json", "r", encoding="utf-8") as f:
    txs = json.load(f)["transactions"]

target_tx = next(t for t in txs if t["fraud_type"] == "distributed_multi_entity_ring")
target_id = target_tx["transaction_id"]

print("================================================================================")
print("             FRAUDLENS AI INVESTIGATION AGENT - LIVE EXECUTION                  ")
print("================================================================================")
print(f"Target Alert: {target_id}")
print(f"Fraud Type:   {target_tx['fraud_type']}")
print(f"Amount:       Rs. {target_tx['amount']:,.2f}")
print(f"Customer:     {target_tx['customer_id']}")
print(f"Device:       {target_tx['device_id']}")
print(f"Token:        {target_tx['payment_token_hash']}")

# 1. Trigger Investigation
print("\n[*] Triggering LangGraph Autonomous Investigation via POST /cases/investigate...")
resp = client.post("/cases/investigate", json={"transaction_id": target_id})
assert resp.status_code == 200, f"Error: {resp.text}"
case = resp.json()
case_id = case["case_id"]
rep = case["report"]

print(f"[OK] Investigation Completed. Generated Case Dossier: {case_id}")

# 2. Print Tool Trace
print("\n--------------------------------------------------------------------------------")
print("                        COMPLETE AGENT TOOL TRACE                               ")
print("--------------------------------------------------------------------------------")

# We can also fetch the state tool trace directly
from services.agent.workflow import InvestigationAgent
agent = InvestigationAgent()
agent_state = agent.investigate(target_id)

for idx, entry in enumerate(agent_state.tool_trace, start=1):
    print(f"\n[Step {idx}] TOOL: {entry.tool_name}")
    print(f"  Status:    {entry.status} (at {entry.timestamp})")
    print(f"  Arguments: {json.dumps(entry.arguments)}")
    # Summarize result cleanly
    res_str = json.dumps(entry.result)
    if len(res_str) > 220:
        res_str = res_str[:220] + "... [TRUNCATED]"
    print(f"  Result:    {res_str}")

# 3. Print Final Investigation Report
print("\n================================================================================")
print("                           OFFICIAL AGENT REPORT                                ")
print("================================================================================")
print(f"\nEXECUTIVE SUMMARY:\n{rep['executive_summary']}")

print("\nOBSERVED FACTS:")
for fact in rep["observed_facts"]:
    print(f"  • {fact}")

print("\nFRAUD HYPOTHESES:")
for hyp in rep["fraud_hypotheses"]:
    print(f"  • {hyp}")

print("\nFINANCIAL IMPACT (Deterministic Arithmetic):")
imp = rep["financial_impact"]
print(f"  • Attempted Fraud Value:         Rs. {imp['attempted_fraud_value']:,.2f}")
print(f"  • Suspicious Exposure:           Rs. {imp['suspicious_value']:,.2f}")
print(f"  • Total Network Exposure:        Rs. {imp['estimated_exposure']:,.2f}")
print(f"  • Estimated False Positive Cost: Rs. {imp['estimated_false_positive_cost']:,.2f}")
print(f"  • Expected Loss by Action:")
for act, loss in imp["expected_loss_by_action"].items():
    print(f"      - {act:10}: Rs. {loss:,.2f}")
print(f"  • Optimal Action by Loss:        {imp['optimal_action_by_loss']}")

print(f"\nRECOMMENDED ACTION:")
print(f"  Action:                 {rep['recommended_action']}")
print(f"  Confidence:             {rep['confidence']*100:.0f}%")
print(f"  Requires Human Sign-off:{rep['requires_human_approval']}")
print(f"  Approval Status:        {rep['approval_status']}")

# 4. Human-in-the-loop sign-off
print("\n[*] Executing Human Approval via POST /cases/{id}/decision...")
dec_resp = client.post(
    f"/cases/{case_id}/decision",
    json={
        "action": rep["recommended_action"],
        "reviewer_id": "lead_investigator_karthik",
        "notes": "Evidence confirms shared device and token across distributed ring. Authorizing immediate HOLD.",
    },
)
assert dec_resp.status_code == 200
final_case = dec_resp.json()
print(f"[OK] Human Decision Recorded. Case Status: {final_case['status']}")
print(f"[OK] Final Approval Status: {final_case['report']['approval_status']}")
print("================================================================================\n")
