"""
LangGraph AI Investigation Agent Workflow for FraudLens
Implements the multi-step investigation state machine:
Alert -> Load -> ML Risk -> Graph Expansion -> History -> Financial Impact
-> Hypothesis Generation -> Report Synthesis -> Action Recommendation -> Audit Recording
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
from langgraph.graph import StateGraph, END

from services.agent.models import (
    InvestigationState,
    ToolTraceEntry,
    InvestigationReport,
    FinancialImpactResult,
)
from services.agent.tools import ControlledTools, CASE_STORE


def load_transaction_node(state: InvestigationState) -> Dict[str, Any]:
    """Step 1: Load transaction facts."""
    tx_id = state.transaction_id
    res = ControlledTools.get_transaction(tx_id)
    trace = state.tool_trace.copy()
    trace.append(ToolTraceEntry(tool_name="get_transaction", arguments={"transaction_id": tx_id}, result=res, status=res["status"]))

    evidence = state.evidence.copy()
    evidence["transaction"] = res.get("data")

    return {
        "tool_trace": trace,
        "evidence": evidence,
        "status": "INVESTIGATING",
    }


def get_ml_risk_node(state: InvestigationState) -> Dict[str, Any]:
    """Step 2: Get ML risk score and SHAP reason codes."""
    tx_id = state.transaction_id
    res = ControlledTools.get_model_explanation(tx_id)
    trace = state.tool_trace.copy()
    trace.append(ToolTraceEntry(tool_name="get_model_explanation", arguments={"transaction_id": tx_id}, result=res, status=res["status"]))

    risk_score = 0.5
    reasons = []
    if res["status"] == "SUCCESS" and res.get("data"):
        risk_score = res["data"].get("risk_score", 0.5)
        reasons = res["data"].get("reason_codes", [])

    evidence = state.evidence.copy()
    evidence["ml_explanation"] = res.get("data")

    return {
        "tool_trace": trace,
        "risk_score": risk_score,
        "risk_reasons": reasons,
        "evidence": evidence,
    }


def expand_graph_node(state: InvestigationState) -> Dict[str, Any]:
    """Step 3: Expand multi-entity graph neighborhood and fetch cluster if linked."""
    tx_id = state.transaction_id
    res_net = ControlledTools.get_graph_neighbors(tx_id, hops=2)
    trace = state.tool_trace.copy()
    trace.append(ToolTraceEntry(tool_name="get_graph_neighbors", arguments={"transaction_id": tx_id, "hops": 2}, result=res_net, status=res_net["status"]))

    cluster_id = None
    cluster_summary = {}

    if res_net["status"] == "SUCCESS" and res_net.get("data"):
        cluster_id = res_net["data"].get("cluster_id")

    if cluster_id:
        res_cluster = ControlledTools.get_cluster(cluster_id)
        trace.append(ToolTraceEntry(tool_name="get_cluster", arguments={"cluster_id": cluster_id}, result=res_cluster, status=res_cluster["status"]))
        if res_cluster["status"] == "SUCCESS":
            cluster_summary = res_cluster.get("data", {})

    evidence = state.evidence.copy()
    evidence["network_graph"] = res_net.get("data")
    evidence["cluster"] = cluster_summary

    return {
        "tool_trace": trace,
        "cluster_id": cluster_id,
        "cluster_summary": cluster_summary,
        "evidence": evidence,
    }


def inspect_history_node(state: InvestigationState) -> Dict[str, Any]:
    """Step 4: Inspect customer historical profile."""
    tx_data = state.evidence.get("transaction", {}) or {}
    cust_id = tx_data.get("customer_id")
    trace = state.tool_trace.copy()
    cust_hist = {}

    if cust_id:
        res = ControlledTools.get_customer_history(cust_id)
        trace.append(ToolTraceEntry(tool_name="get_customer_history", arguments={"customer_id": cust_id}, result=res, status=res["status"]))
        if res["status"] == "SUCCESS":
            cust_hist = res.get("data", {})
    else:
        trace.append(ToolTraceEntry(tool_name="get_customer_history", arguments={}, result={"message": "No customer_id available"}, status="MISSING_DATA"))

    evidence = state.evidence.copy()
    evidence["customer_history"] = cust_hist

    return {
        "tool_trace": trace,
        "evidence": evidence,
    }


def calculate_impact_node(state: InvestigationState) -> Dict[str, Any]:
    """Step 5: Deterministically compute financial exposure."""
    tx_id = state.transaction_id
    cluster_id = state.cluster_id
    res = ControlledTools.calculate_impact(tx_id, cluster_id=cluster_id)
    trace = state.tool_trace.copy()
    trace.append(ToolTraceEntry(tool_name="calculate_impact", arguments={"transaction_id": tx_id, "cluster_id": cluster_id}, result=res, status=res["status"]))

    impact = None
    if res["status"] == "SUCCESS" and res.get("data"):
        impact = FinancialImpactResult(**res["data"])

    evidence = state.evidence.copy()
    evidence["financial_impact"] = res.get("data")

    return {
        "tool_trace": trace,
        "impact": impact,
        "evidence": evidence,
    }


def generate_hypotheses_node(state: InvestigationState) -> Dict[str, Any]:
    """Step 6: Formulate evidence-grounded hypotheses."""
    cluster = state.cluster_summary
    pattern = cluster.get("pattern_type", "suspicious_transaction")
    res_similar = ControlledTools.search_similar_cases(pattern)
    trace = state.tool_trace.copy()
    trace.append(ToolTraceEntry(tool_name="search_similar_cases", arguments={"pattern_type": pattern}, result=res_similar, status=res_similar["status"]))

    hypotheses = []
    tx_evidence = state.evidence.get("transaction", {}) or {}
    amt = tx_evidence.get("amount", 0.0)

    if state.cluster_id:
        members = cluster.get("member_count", 0)
        c_risk = cluster.get("risk_score", 0.0)
        hypotheses.append(
            f"HYPOTHESIS: Transaction is part of a coordinated '{pattern}' comprising {members} accounts with graph risk {c_risk:.2f}."
        )
        if pattern == "shared_payment_token_ring":
            hypotheses.append("HYPOTHESIS: Stolen credit/debit instrument credentials have been distributed across puppet accounts.")
        elif pattern == "shared_device_ring":
            hypotheses.append("HYPOTHESIS: Organized fraudsters are operating an emulator/rooted device farm generating synthetic identities.")
    else:
        if state.risk_score >= 0.70:
            hypotheses.append(f"HYPOTHESIS: Transaction exhibits high-risk behavioral anomalies (Score: {state.risk_score:.2f}) without verified network ring linkage.")
        else:
            hypotheses.append("HYPOTHESIS: Transaction is consistent with legitimate consumer behavior despite minor heuristic flags.")

    evidence = state.evidence.copy()
    evidence["similar_cases"] = res_similar.get("data")

    return {
        "tool_trace": trace,
        "hypotheses": hypotheses,
        "evidence": evidence,
    }


def synthesize_report_node(state: InvestigationState) -> Dict[str, Any]:
    """Step 7: Synthesize report strictly separating FACT, HYPOTHESIS, and RECOMMENDATION."""
    tx_data = state.evidence.get("transaction", {}) or {}
    cust_data = state.evidence.get("customer_history", {}) or {}
    cluster_data = state.cluster_summary or {}
    impact = state.impact

    # 1. Observed Facts
    facts = []
    tid = state.transaction_id
    amt = tx_data.get("amount", 0.0)
    facts.append(f"FACT: Transaction '{tid}' requested authorization for Rs. {amt:,.2f} via {tx_data.get('payment_method', 'UPI')}.")
    facts.append(f"FACT: Transaction-level ML Risk Model assigned probability score of {state.risk_score:.4f}.")
    for r in state.risk_reasons[:3]:
        facts.append(f"FACT: ML Risk Driver: {r}")

    if state.cluster_id:
        facts.append(f"FACT: Network Engine identified link to cluster '{state.cluster_id}' with {cluster_data.get('member_count', 0)} connected accounts.")
        facts.append(f"FACT: Cluster exhibits total attempted volume of Rs. {cluster_data.get('attempted_amount', 0):,.2f} across {cluster_data.get('transaction_count', 0)} transactions.")
        facts.append(f"FACT: Infrastructure shared: {cluster_data.get('device_count', 0)} device(s), {cluster_data.get('payment_token_count', 0)} payment token(s).")
    else:
        facts.append("FACT: No multi-account coordinated fraud ring link detected for this transaction.")

    # 2. Recommendation Logic
    # Actions: ALLOW, MONITOR, STEP_UP, REVIEW, HOLD
    if state.cluster_id and state.cluster_summary.get("risk_score", 0) >= 0.85:
        rec_action = "HOLD"
        confidence = 0.95
    elif state.risk_score >= 0.80:
        rec_action = "REVIEW"
        confidence = 0.88
    elif state.risk_score >= 0.40 or (state.cluster_id and state.cluster_summary.get("risk_score", 0) >= 0.50):
        rec_action = "STEP_UP"
        confidence = 0.78
    elif state.risk_score >= 0.20:
        rec_action = "MONITOR"
        confidence = 0.85
    else:
        rec_action = "ALLOW"
        confidence = 0.96

    req_approval = rec_action in ["HOLD", "REVIEW"]

    exec_summary = (
        f"Investigation completed for transaction '{tid}'. ML risk probability is {state.risk_score:.2f}. "
        f"{'Coordinated network cluster identified (' + state.cluster_id + ' with ' + str(cluster_data.get('member_count', 0)) + ' accounts).' if state.cluster_id else 'No network cluster detected.'} "
        f"Financial exposure is estimated at Rs. {impact.estimated_exposure if impact else amt:,.2f}. "
        f"Recommended Action: {rec_action} (Confidence: {confidence*100:.0f}%)."
    )

    report = InvestigationReport(
        executive_summary=exec_summary,
        observed_facts=facts,
        transaction_evidence=tx_data,
        network_evidence=cluster_data,
        behavioral_evidence=cust_data,
        financial_impact=impact if impact else FinancialImpactCalculator.calculate(amt, state.risk_score),
        fraud_hypotheses=state.hypotheses,
        confidence=confidence,
        recommended_action=rec_action,
        requires_human_approval=req_approval,
        approval_status="PENDING_APPROVAL" if req_approval else "AUTO_RESOLVED",
    )

    return {
        "report": report,
        "recommendation": rec_action,
        "confidence": confidence,
        "status": "SYNTHESIZED",
    }


def audit_record_node(state: InvestigationState) -> Dict[str, Any]:
    """Step 8: Formally register case and append audit decision."""
    tx_data = state.evidence.get("transaction", {}) or {}
    tid = state.transaction_id
    rec_action = state.recommendation
    report = state.report

    # Create Case File
    res_case = ControlledTools.create_case(
        title=f"Investigation: {tid} ({rec_action})",
        severity="CRITICAL" if rec_action == "HOLD" else ("HIGH" if rec_action == "REVIEW" else "MEDIUM"),
        transaction_ids=[tid] + (state.cluster_summary.get("transaction_ids", [])[:10] if state.cluster_summary else []),
        entities={
            "customers": [tx_data.get("customer_id", "")] if tx_data.get("customer_id") else [],
            "devices": [tx_data.get("device_id", "")] if tx_data.get("device_id") else [],
            "ips": [tx_data.get("ip_hash", "")] if tx_data.get("ip_hash") else [],
        },
    )
    case_id = res_case["data"]["case_id"]

    # Record Decision Entry
    res_dec = ControlledTools.record_decision(
        case_id=case_id,
        action=rec_action,
        justification=report.executive_summary if report else f"Automated agent assessment: {rec_action}",
        requires_approval=report.requires_human_approval if report else True,
    )

    # Attach report to stored case
    if case_id in CASE_STORE and report:
        CASE_STORE[case_id].report = report

    trace = state.tool_trace.copy()
    trace.append(ToolTraceEntry(tool_name="create_case", arguments={"transaction_id": tid}, result=res_case, status=res_case["status"]))
    trace.append(ToolTraceEntry(tool_name="record_decision", arguments={"case_id": case_id, "action": rec_action}, result=res_dec, status=res_dec["status"]))

    return {
        "case_id": case_id,
        "tool_trace": trace,
        "status": "COMPLETED",
    }


def create_investigation_workflow() -> StateGraph:
    """Builds and compiles the LangGraph investigation workflow."""
    workflow = StateGraph(InvestigationState)

    workflow.add_node("load_transaction", load_transaction_node)
    workflow.add_node("get_ml_risk", get_ml_risk_node)
    workflow.add_node("expand_graph", expand_graph_node)
    workflow.add_node("inspect_history", inspect_history_node)
    workflow.add_node("calculate_impact", calculate_impact_node)
    workflow.add_node("generate_hypotheses", generate_hypotheses_node)
    workflow.add_node("synthesize_report", synthesize_report_node)
    workflow.add_node("audit_record", audit_record_node)

    # Define linear graph execution
    workflow.set_entry_point("load_transaction")
    workflow.add_edge("load_transaction", "get_ml_risk")
    workflow.add_edge("get_ml_risk", "expand_graph")
    workflow.add_edge("expand_graph", "inspect_history")
    workflow.add_edge("inspect_history", "calculate_impact")
    workflow.add_edge("calculate_impact", "generate_hypotheses")
    workflow.add_edge("generate_hypotheses", "synthesize_report")
    workflow.add_edge("synthesize_report", "audit_record")
    workflow.add_edge("audit_record", END)

    return workflow.compile()


class InvestigationAgent:
    """Entrypoint for executing investigations on alerts and transactions."""

    def __init__(self):
        self.app = create_investigation_workflow()

    def investigate(self, transaction_id: str) -> InvestigationState:
        initial_state = InvestigationState(transaction_id=transaction_id)
        final_state_dict = self.app.invoke(initial_state)
        return InvestigationState(**final_state_dict)
