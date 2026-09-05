"""
Agent State & Data Models for FraudLens AI Investigation Agent
Defines Pydantic models for agent state, tool traces, financial impact, and audit reports.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ToolTraceEntry(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    status: str = "SUCCESS"  # SUCCESS, MISSING_DATA, ERROR
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FinancialImpactResult(BaseModel):
    attempted_fraud_value: float
    suspicious_value: float
    estimated_exposure: float
    estimated_false_positive_cost: float
    expected_loss_by_action: Dict[str, float]  # ALLOW, MONITOR, STEP_UP, REVIEW, HOLD
    optimal_action_by_loss: str


class InvestigationReport(BaseModel):
    executive_summary: str
    observed_facts: List[str]
    transaction_evidence: Dict[str, Any]
    network_evidence: Dict[str, Any]
    behavioral_evidence: Dict[str, Any]
    financial_impact: FinancialImpactResult
    fraud_hypotheses: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommended_action: str  # ALLOW, MONITOR, STEP_UP, REVIEW, HOLD
    requires_human_approval: bool = True
    approval_status: str = "PENDING_APPROVAL"  # PENDING_APPROVAL, APPROVED, OVERRIDDEN, REJECTED
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CaseRecord(BaseModel):
    case_id: str
    title: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    status: str = "OPEN"  # OPEN, UNDER_REVIEW, RESOLVED, CLOSED
    primary_transaction_id: str
    associated_transactions: List[str] = Field(default_factory=list)
    associated_entities: Dict[str, List[str]] = Field(default_factory=dict)
    report: Optional[InvestigationReport] = None
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InvestigationState(BaseModel):
    """Pydantic state container passed across LangGraph nodes."""
    transaction_id: str
    risk_score: float = 0.0
    risk_reasons: List[str] = Field(default_factory=list)
    cluster_id: Optional[str] = None
    cluster_summary: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    impact: Optional[FinancialImpactResult] = None
    hypotheses: List[str] = Field(default_factory=list)
    recommendation: str = "REVIEW"
    confidence: float = 0.5
    tool_trace: List[ToolTraceEntry] = Field(default_factory=list)
    status: str = "INITIALIZING"
    case_id: Optional[str] = None
    report: Optional[InvestigationReport] = None
