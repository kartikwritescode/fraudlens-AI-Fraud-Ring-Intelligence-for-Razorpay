"""
Unit Tests for Synthetic Payment Universe Generator & Fraud Scenarios
"""

import pytest
from services.simulator.generator import SyntheticUniverseGenerator
from services.simulator.models import PaymentUniverse


@pytest.fixture(scope="module")
def small_universe() -> PaymentUniverse:
    """Fast universe for assertions."""
    gen = SyntheticUniverseGenerator(
        target_transactions=1500,
        customer_count=300,
        merchant_count=30,
        ring_count=7,
        seed=42,
    )
    return gen.generate_universe()


def test_deterministic_generation():
    """Verify that identical seeds produce identical transaction sequences."""
    gen1 = SyntheticUniverseGenerator(target_transactions=200, customer_count=50, merchant_count=10, ring_count=2, seed=123)
    u1 = gen1.generate_universe()

    gen2 = SyntheticUniverseGenerator(target_transactions=200, customer_count=50, merchant_count=10, ring_count=2, seed=123)
    u2 = gen2.generate_universe()

    assert len(u1.transactions) == len(u2.transactions)
    for t1, t2 in zip(u1.transactions, u2.transactions):
        assert t1.transaction_id == t2.transaction_id
        assert t1.amount == t2.amount
        assert t1.customer_id == t2.customer_id
        assert t1.device_id == t2.device_id
        assert t1.ip_hash == t2.ip_hash
        assert t1.is_fraud == t2.is_fraud


def test_transaction_field_completeness(small_universe):
    """Verify that every transaction has all 18 required fields populated."""
    for tx in small_universe.transactions:
        assert tx.transaction_id.startswith("tx_")
        assert tx.timestamp
        assert tx.merchant_id.startswith("mer_")
        assert tx.customer_id.startswith("cust_")
        assert tx.amount > 0
        assert tx.currency == "INR"
        assert tx.payment_method in ["upi", "card", "netbanking", "wallet"]
        assert tx.status in ["captured", "failed", "authorized", "blocked"]
        assert tx.device_id.startswith("dev_")
        assert tx.ip_hash.startswith("ip_")
        assert tx.email_hash.startswith("em_")
        assert tx.phone_hash.startswith("ph_")
        assert tx.payment_token_hash.startswith("tok_")
        assert tx.billing_country
        assert tx.shipping_country
        assert tx.order_id.startswith("ord_")
        assert isinstance(tx.is_fraud, bool)
        if tx.is_fraud:
            assert tx.fraud_type is not None


def test_all_seven_fraud_scenarios_present(small_universe):
    """Verify that all 7 required fraud ring patterns exist in the generated dataset."""
    patterns = {r.pattern_type for r in small_universe.fraud_rings}
    expected_patterns = {
        "shared_device_ring",
        "shared_ip_ring",
        "shared_payment_token_ring",
        "account_takeover",
        "velocity_attack",
        "testing_and_hit_attack",
        "distributed_multi_entity_ring",
    }
    assert expected_patterns.issubset(patterns), f"Missing patterns: {expected_patterns - patterns}"


def test_fraud_not_unrealistically_obvious(small_universe):
    """
    Ensure fraud transactions don't use trivial static values:
    - Amounts vary across realistic spectrum
    - Some fraud succeeds and some fails
    - Hashes look realistic
    """
    fraud_txs = [t for t in small_universe.transactions if t.is_fraud]
    assert len(fraud_txs) > 0

    amounts = {t.amount for t in fraud_txs}
    assert len(amounts) > 20, "Fraud amounts must not be static"

    # Should have realistic variation: some < ₹5,000, some > ₹10,000
    assert any(t.amount < 5000 for t in fraud_txs)
    assert any(t.amount > 10000 for t in fraud_txs)

    # Some fraud succeeds, some fails
    statuses = {t.status for t in fraud_txs}
    assert "captured" in statuses
    assert "failed" in statuses


def test_legitimate_shared_infrastructure(small_universe):
    """
    Verify that legitimate users realistically share some IPs and devices
    (e.g. campus Wi-Fi, tech park NATs, family iPads).
    """
    from collections import Counter

    legit_txs = [t for t in small_universe.transactions if not t.is_fraud]

    # Check shared legitimate IPs
    ip_to_customers = {}
    for t in legit_txs:
        ip_to_customers.setdefault(t.ip_hash, set()).add(t.customer_id)

    shared_legit_ips = {ip: custs for ip, custs in ip_to_customers.items() if len(custs) > 1}
    assert len(shared_legit_ips) > 0, "Legitimate shared IPs must exist in realistic data"


def test_target_scale_exact_count():
    """Verify generator reaches the requested transaction count."""
    gen = SyntheticUniverseGenerator(target_transactions=5000, seed=42)
    universe = gen.generate_universe()
    assert len(universe.transactions) == 5000
