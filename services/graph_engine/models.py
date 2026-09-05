"""
Graph Models for FraudLens Fraud Graph Intelligence Engine
Defines UI-ready network schemas, ring objects, and timeline event models.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str  # Display name or truncated hash
    type: str   # Customer, Transaction, Merchant, Device, IP, PaymentToken, Email, Phone
    risk_score: float = 0.0
    risk_band: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str  # CUSTOMER_MADE_TRANSACTION, CUSTOMER_USES_DEVICE, etc.
    label: str
    timestamp: Optional[str] = None
    is_suspicious: bool = False
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphNetworkResponse(BaseModel):
    center_id: str
    center_type: str
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    node_count: int
    edge_count: int
    cluster_id: Optional[str] = None
    cluster_risk_score: Optional[float] = None


class TimelineEvent(BaseModel):
    timestamp: str
    event_type: str  # ENTITY_JOINED, DEVICE_LINKED, TOKEN_SHARED, BURST_DETECTED, RISK_ESCALATED
    title: str
    description: str
    severity: str  # info, warning, critical
    entities_involved: List[str] = Field(default_factory=list)


class DiscoveredRing(BaseModel):
    ring_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_band: str  # LOW, MEDIUM, HIGH, CRITICAL
    pattern_type: str
    member_count: int
    transaction_count: int
    attempted_amount: float
    suspicious_amount: float
    merchant_count: int
    device_count: int
    ip_count: int
    payment_token_count: int
    growth_rate: float = Field(default=1.0, description="Entities added per hour during attack")
    created_at: str
    updated_at: str
    customer_ids: List[str] = Field(default_factory=list)
    device_ids: List[str] = Field(default_factory=list)
    ip_hashes: List[str] = Field(default_factory=list)
    payment_token_hashes: List[str] = Field(default_factory=list)
    transaction_ids: List[str] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    explanation: str = ""
