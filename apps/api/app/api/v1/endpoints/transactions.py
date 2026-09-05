"""
Transaction Risk Scoring & SHAP Reason Code Endpoints
Provides real-time ML risk predictions and explainable risk factors.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from services.risk_engine.inference import RiskScorer, RiskAssessmentResult
from app.core.errors import EntityNotFoundError

router = APIRouter(tags=["Transaction Risk ML"])


class TransactionScoreRequest(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction ID")
    merchant_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    payment_method: str = "upi"
    status: str = "authorized"
    device_id: str
    ip_hash: str
    email_hash: str
    phone_hash: str
    payment_token_hash: str
    billing_country: str = "IND"
    shipping_country: str = "IND"
    order_id: Optional[str] = None


@router.get("/transactions/{transaction_id}/risk", response_model=RiskAssessmentResult, summary="Get Transaction Risk Score & SHAP Reasons")
async def get_transaction_risk(transaction_id: str):
    """
    Evaluates risk score, decision band, and top SHAP explainability reason codes
    for a transaction by ID.
    """
    scorer = RiskScorer.get_instance()
    result = scorer.assess_by_transaction_id(transaction_id)
    if result is None:
        raise EntityNotFoundError("Transaction", transaction_id)
    return result


@router.post("/transactions/score", response_model=RiskAssessmentResult, summary="Score Ad-hoc Transaction Payload")
async def score_adhoc_transaction(payload: TransactionScoreRequest):
    """
    Scores an incoming ad-hoc transaction payload in real time with the trained XGBoost model
    and computes TreeSHAP explainability drivers.
    """
    scorer = RiskScorer.get_instance()
    result = scorer.assess_transaction(payload.model_dump())
    return result
