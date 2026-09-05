"""
Graph Intelligence Endpoints for FraudLens
Exposes ring intelligence, network neighborhoods, and multi-entity subgraphs.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any

from services.graph_engine.models import (
    DiscoveredRing,
    GraphNetworkResponse,
    TimelineEvent,
)
from services.graph_engine.ring_detector import AlgorithmicRingDetector
from services.graph_engine.neighbor_expander import GraphNeighborExpander
from app.core.errors import EntityNotFoundError

router = APIRouter(tags=["Fraud Graph Intelligence"])


@router.get("/rings", response_model=List[DiscoveredRing], summary="List All Discovered Fraud Rings")
async def list_fraud_rings(min_risk: float = Query(0.40, ge=0.0, le=1.0)):
    """
    Returns all algorithmically discovered fraud rings sorted descending by risk score.
    """
    detector = AlgorithmicRingDetector.get_instance()
    rings = detector.get_rings()
    if min_risk > 0:
        rings = [r for r in rings if r.risk_score >= min_risk]
    return rings


@router.get("/rings/{ring_id}", response_model=DiscoveredRing, summary="Get Fraud Ring Detail & Timeline")
async def get_fraud_ring(ring_id: str):
    """
    Returns comprehensive profile of a discovered fraud ring, including members,
    financial metrics, and formation timeline.
    """
    detector = AlgorithmicRingDetector.get_instance()
    ring = detector.get_ring_by_id(ring_id)
    if not ring:
        raise EntityNotFoundError("FraudRing", ring_id)
    return ring


@router.get("/transactions/{transaction_id}/network", response_model=GraphNetworkResponse, summary="Get Transaction Neighborhood Network")
async def get_transaction_network(
    transaction_id: str,
    hops: int = Query(2, ge=1, le=3, description="Expansion hops"),
    max_nodes: int = Query(50, ge=5, le=150, description="Max nodes to return"),
):
    """
    Returns the multi-entity subgraph surrounding a transaction, formatted for interactive UI rendering
    (React Flow / Cytoscape) with risk severity node colors and relationship edges.
    """
    expander = GraphNeighborExpander.get_instance()
    network = expander.expand_transaction_subgraph(transaction_id, hops=hops, max_nodes=max_nodes)
    if not network:
        raise EntityNotFoundError("Transaction", transaction_id)
    return network


@router.get("/entities/{entity_id}/neighbors", response_model=GraphNetworkResponse, summary="Get Entity Neighbors Network")
async def get_entity_neighbors(
    entity_id: str,
    hops: int = Query(1, ge=1, le=2),
    max_nodes: int = Query(30, ge=5, le=100),
):
    """
    Expands 1-2 hops around any entity identifier (customer_id, device_id, ip_hash, payment_token_hash).
    """
    expander = GraphNeighborExpander.get_instance()
    return expander.expand_entity_neighbors(entity_id, hops=hops, max_nodes=max_nodes)
