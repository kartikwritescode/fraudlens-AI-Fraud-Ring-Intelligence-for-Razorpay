"""
Case Management & AI Agent Investigation Endpoints for FraudLens
Allows triggering automated investigations, retrieving case dossiers,
and recording human decision sign-offs.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from services.agent.models import CaseRecord, InvestigationReport
from services.agent.workflow import InvestigationAgent
from services.agent.tools import CASE_STORE, ControlledTools
from app.core.errors import EntityNotFoundError
from app.core.auth import verify_analyst_auth

router = APIRouter(tags=["AI Investigation Agent"])


class InvestigateRequest(BaseModel):
    transaction_id: str = Field(..., description="Transaction ID to trigger autonomous investigation")


class DecisionRequest(BaseModel):
    action: str = Field(..., description="Action: ALLOW, MONITOR, STEP_UP, REVIEW, HOLD")
    reviewer_id: str = Field("analyst_01", description="Identifier of the risk analyst")
    notes: Optional[str] = Field(None, description="Justification notes for audit record")
    justification: Optional[str] = Field(None, description="Alternative field name for justification")


@router.post("/cases/investigate", response_model=CaseRecord, summary="Trigger Autonomous AI Agent Investigation")
async def trigger_investigation(request: InvestigateRequest):
    """
    Spawns the LangGraph AI Fraud Investigator to:
    1. Query controlled data tools
    2. Expand graph neighborhood & cluster linkages
    3. Run deterministic financial calculations
    4. Synthesize facts, hypotheses, and recommendations
    5. Register an official audit case record
    """
    agent = InvestigationAgent()
    state = agent.investigate(request.transaction_id)
    if not state.case_id or state.case_id not in CASE_STORE:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register case record during investigation.",
        )
    return CASE_STORE[state.case_id]


@router.get("/cases/{case_id}", response_model=CaseRecord, summary="Get Case Details & Audit Trail")
async def get_case(case_id: str):
    """
    Retrieves complete case dossier including executive report, tool traces,
    and decision history.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise EntityNotFoundError("Case", case_id)
    return case


@router.post("/cases/{case_id}/decision", response_model=CaseRecord, summary="Record Human Analyst Decision")
async def record_human_decision(
    case_id: str,
    request: DecisionRequest,
    auth_ctx: dict = Depends(verify_analyst_auth),
):
    """
    Human-in-the-loop checkpoint: human analyst approves or overrides
    the AI agent's recommended action.
    """
    case = CASE_STORE.get(case_id)
    if not case:
        raise EntityNotFoundError("Case", case_id)

    note_text = request.notes or request.justification or "Analyst decision recorded"
    res = ControlledTools.record_decision(
        case_id=case_id,
        action=request.action,
        justification=f"[{request.reviewer_id}] {note_text}",
        requires_approval=False,
    )
    if case.report:
        case.report.approval_status = "APPROVED" if request.action == case.report.recommended_action else "OVERRIDDEN"

    return case
