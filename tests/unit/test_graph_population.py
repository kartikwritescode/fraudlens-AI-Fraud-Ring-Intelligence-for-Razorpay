"""
Unit Tests for Neo4j Multi-Entity Relationship Graph Structure
"""

import pytest
from services.simulator.generator import SyntheticUniverseGenerator
from services.graph_engine.graph_builder import build_graph_from_universe


@pytest.fixture(scope="module")
def graph_data():
    gen = SyntheticUniverseGenerator(
        target_transactions=2000,
        customer_count=400,
        merchant_count=30,
        ring_count=7,
        seed=42,
    )
    universe = gen.generate_universe()
    return build_graph_from_universe(universe)


def test_all_node_types_populated(graph_data):
    """Verify all 8 node types are populated."""
    counts = graph_data.get_node_counts()
    required_nodes = [
        "Customer",
        "Transaction",
        "Merchant",
        "Device",
        "IP",
        "PaymentToken",
        "Email",
        "Phone",
    ]
    for n in required_nodes:
        assert counts[n] > 0, f"Node type {n} has 0 instances"
    assert counts["TotalNodes"] > 3000


def test_all_relationship_types_populated(graph_data):
    """Verify all 9 relationship types are populated."""
    counts = graph_data.get_relationship_counts()
    required_rels = [
        "CUSTOMER_MADE_TRANSACTION",
        "TRANSACTION_FOR_MERCHANT",
        "CUSTOMER_USES_DEVICE",
        "CUSTOMER_USES_IP",
        "CUSTOMER_USES_PAYMENT_TOKEN",
        "CUSTOMER_HAS_EMAIL",
        "CUSTOMER_HAS_PHONE",
        "TRANSACTION_FROM_DEVICE",
        "TRANSACTION_FROM_IP",
    ]
    for r in required_rels:
        assert counts[r] > 0, f"Relationship type {r} has 0 instances"
    assert counts["TotalRelationships"] > 5000


def test_transaction_graph_integrity(graph_data):
    """Every transaction must be made by a customer and directed to a merchant."""
    assert len(graph_data.customer_made_transaction) == len(graph_data.transactions)
    assert len(graph_data.transaction_for_merchant) == len(graph_data.transactions)
    assert len(graph_data.transaction_from_device) == len(graph_data.transactions)
    assert len(graph_data.transaction_from_ip) == len(graph_data.transactions)
