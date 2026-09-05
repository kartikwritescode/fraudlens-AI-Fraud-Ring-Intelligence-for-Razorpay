"""
Data Models for Synthetic Payment Universe & Fraud Rings
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    transaction_id: str
    timestamp: str  # ISO 8601 string
    merchant_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    payment_method: str  # upi, card, netbanking, wallet
    status: str  # authorized, captured, failed, blocked
    device_id: str
    ip_hash: str
    email_hash: str
    phone_hash: str
    payment_token_hash: str
    billing_country: str = "IND"
    shipping_country: str = "IND"
    order_id: str
    is_fraud: bool = False
    fraud_type: Optional[str] = None
    ring_id: Optional[str] = None


class Customer(BaseModel):
    id: str
    country: str = "IND"
    first_seen_at: str
    last_seen_at: str
    created_at: str
    email_hash: str
    phone_hash: str
    devices: List[str] = Field(default_factory=list)
    ips: List[str] = Field(default_factory=list)
    payment_tokens: List[str] = Field(default_factory=list)
    preferred_merchants: List[str] = Field(default_factory=list)


class Merchant(BaseModel):
    id: str
    name: str
    category: str  # ecommerce, travel, food, electronics, utilities, gaming, crypto
    created_at: str


class FraudRing(BaseModel):
    id: str
    name: str
    pattern_type: str
    risk_score: float = 0.90
    risk_band: str = "CRITICAL"
    member_count: int = 0
    attempted_amount: float = 0.0
    estimated_loss: float = 0.0
    status: str = "DISCOVERED"
    created_at: str
    updated_at: str
    customer_ids: List[str] = Field(default_factory=list)
    device_ids: List[str] = Field(default_factory=list)
    ip_hashes: List[str] = Field(default_factory=list)
    payment_token_hashes: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    description: str = ""


class PaymentUniverse(BaseModel):
    customers: List[Customer]
    merchants: List[Merchant]
    transactions: List[Transaction]
    fraud_rings: List[FraudRing]
    stats: Dict[str, Any] = Field(default_factory=dict)
