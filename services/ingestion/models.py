"""
Normalized Ingestion Event Models for FraudLens
Provides a unified internal schema decoupled from external payment gateways.
Explicitly distinguishes Razorpay Test Mode from FraudLens Synthetic Demo Mode.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid


class TransactionEvent(BaseModel):
    """Unified internal transaction event schema."""
    event_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    source_mode: str = Field(..., description="RAZORPAY_TEST_MODE or FRAUDLENS_DEMO_MODE")
    source_label: str = Field(..., description="'Razorpay Test Event' or 'FraudLens Synthetic Event'")
    event_type: str = Field(..., description="payment.authorized, payment.captured, payment.failed, etc.")
    transaction_id: str
    amount: float = Field(..., description="Amount in standard INR units (not paise)")
    currency: str = "INR"
    status: str = "authorized"  # authorized, captured, failed, blocked
    customer_id: str
    merchant_id: str = "mer_razorpay_test"
    payment_method: str = "card"  # card, upi, netbanking, wallet
    device_id: str = "dev_web_client"
    ip_hash: str = "ip_client_direct"
    payment_token_hash: str = "tok_tokenized_instrument"
    email_hash: str = ""
    phone_hash: str = ""
    billing_country: str = "IND"
    shipping_country: str = "IND"
    order_id: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PipelineProcessingResult(BaseModel):
    event_id: str
    transaction_id: str
    source_label: str
    is_duplicate: bool = False
    risk_score: float
    risk_band: str
    reason_codes: List[str] = Field(default_factory=list)
    cluster_id: Optional[str] = None
    alert_triggered: bool = False
    case_id: Optional[str] = None
    agent_recommendation: Optional[str] = None
    processed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
