"""
Graph Builder & Statistics Engine for FraudLens
Translates PaymentUniverse transactions and entities into the multi-entity relationship graph.
"""

from typing import Dict, Any, Set, List, Tuple
from collections import defaultdict
from services.simulator.models import PaymentUniverse, Transaction, Customer, Merchant


class GraphStructure:
    """In-memory representation of Neo4j multi-entity graph."""

    def __init__(self):
        # Node sets by label
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self.merchants: Dict[str, Dict[str, Any]] = {}
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.ips: Dict[str, Dict[str, Any]] = {}
        self.payment_tokens: Dict[str, Dict[str, Any]] = {}
        self.emails: Dict[str, Dict[str, Any]] = {}
        self.phones: Dict[str, Dict[str, Any]] = {}

        # Relationships by type: list of (source_id, target_id, props)
        self.customer_made_transaction: Set[Tuple[str, str]] = set()
        self.transaction_for_merchant: Set[Tuple[str, str]] = set()
        self.customer_uses_device: Set[Tuple[str, str]] = set()
        self.customer_uses_ip: Set[Tuple[str, str]] = set()
        self.customer_uses_payment_token: Set[Tuple[str, str]] = set()
        self.customer_has_email: Set[Tuple[str, str]] = set()
        self.customer_has_phone: Set[Tuple[str, str]] = set()
        self.transaction_from_device: Set[Tuple[str, str]] = set()
        self.transaction_from_ip: Set[Tuple[str, str]] = set()

    def get_node_counts(self) -> Dict[str, int]:
        return {
            "Customer": len(self.customers),
            "Transaction": len(self.transactions),
            "Merchant": len(self.merchants),
            "Device": len(self.devices),
            "IP": len(self.ips),
            "PaymentToken": len(self.payment_tokens),
            "Email": len(self.emails),
            "Phone": len(self.phones),
            "TotalNodes": (
                len(self.customers)
                + len(self.transactions)
                + len(self.merchants)
                + len(self.devices)
                + len(self.ips)
                + len(self.payment_tokens)
                + len(self.emails)
                + len(self.phones)
            ),
        }

    def get_relationship_counts(self) -> Dict[str, int]:
        return {
            "CUSTOMER_MADE_TRANSACTION": len(self.customer_made_transaction),
            "TRANSACTION_FOR_MERCHANT": len(self.transaction_for_merchant),
            "CUSTOMER_USES_DEVICE": len(self.customer_uses_device),
            "CUSTOMER_USES_IP": len(self.customer_uses_ip),
            "CUSTOMER_USES_PAYMENT_TOKEN": len(self.customer_uses_payment_token),
            "CUSTOMER_HAS_EMAIL": len(self.customer_has_email),
            "CUSTOMER_HAS_PHONE": len(self.customer_has_phone),
            "TRANSACTION_FROM_DEVICE": len(self.transaction_from_device),
            "TRANSACTION_FROM_IP": len(self.transaction_from_ip),
            "TotalRelationships": (
                len(self.customer_made_transaction)
                + len(self.transaction_for_merchant)
                + len(self.customer_uses_device)
                + len(self.customer_uses_ip)
                + len(self.customer_uses_payment_token)
                + len(self.customer_has_email)
                + len(self.customer_has_phone)
                + len(self.transaction_from_device)
                + len(self.transaction_from_ip)
            ),
        }


def build_graph_from_universe(universe: PaymentUniverse) -> GraphStructure:
    """Builds the complete multi-entity graph from a PaymentUniverse instance."""
    graph = GraphStructure()

    # 1. Populate Merchants
    for m in universe.merchants:
        graph.merchants[m.id] = {
            "id": m.id,
            "name": m.name,
            "category": m.category,
            "created_at": m.created_at,
        }

    # 2. Populate Customers & their direct profile attributes
    for c in universe.customers:
        graph.customers[c.id] = {
            "id": c.id,
            "country": c.country,
            "created_at": c.created_at,
            "first_seen_at": c.first_seen_at,
            "last_seen_at": c.last_seen_at,
        }

        # Email & Phone
        if c.email_hash:
            graph.emails[c.email_hash] = {"email_hash": c.email_hash}
            graph.customer_has_email.add((c.id, c.email_hash))

        if c.phone_hash:
            graph.phones[c.phone_hash] = {"phone_hash": c.phone_hash}
            graph.customer_has_phone.add((c.id, c.phone_hash))

        # Direct devices, IPs, tokens known for customer
        for dev in c.devices:
            graph.devices[dev] = {"id": dev}
            graph.customer_uses_device.add((c.id, dev))

        for ip in c.ips:
            graph.ips[ip] = {"ip_hash": ip}
            graph.customer_uses_ip.add((c.id, ip))

        for tok in c.payment_tokens:
            graph.payment_tokens[tok] = {"token_hash": tok}
            graph.customer_uses_payment_token.add((c.id, tok))

    # 3. Populate Transactions & Link to all entities
    for t in universe.transactions:
        graph.transactions[t.transaction_id] = {
            "id": t.transaction_id,
            "amount": t.amount,
            "currency": t.currency,
            "timestamp": t.timestamp,
            "status": t.status,
            "payment_method": t.payment_method,
            "is_fraud": t.is_fraud,
            "fraud_type": t.fraud_type,
            "ring_id": t.ring_id,
            "order_id": t.order_id,
        }

        # Relationships
        # CUSTOMER_MADE_TRANSACTION
        graph.customer_made_transaction.add((t.customer_id, t.transaction_id))

        # TRANSACTION_FOR_MERCHANT
        graph.transaction_for_merchant.add((t.transaction_id, t.merchant_id))

        # Devices
        if t.device_id:
            graph.devices[t.device_id] = {"id": t.device_id}
            graph.transaction_from_device.add((t.transaction_id, t.device_id))
            graph.customer_uses_device.add((t.customer_id, t.device_id))

        # IPs
        if t.ip_hash:
            graph.ips[t.ip_hash] = {"ip_hash": t.ip_hash}
            graph.transaction_from_ip.add((t.transaction_id, t.ip_hash))
            graph.customer_uses_ip.add((t.customer_id, t.ip_hash))

        # Payment Tokens
        if t.payment_token_hash:
            graph.payment_tokens[t.payment_token_hash] = {"token_hash": t.payment_token_hash}
            graph.customer_uses_payment_token.add((t.customer_id, t.payment_token_hash))

        # Emails & Phones from transaction
        if t.email_hash:
            graph.emails[t.email_hash] = {"email_hash": t.email_hash}
            graph.customer_has_email.add((t.customer_id, t.email_hash))

        if t.phone_hash:
            graph.phones[t.phone_hash] = {"phone_hash": t.phone_hash}
            graph.customer_has_phone.add((t.customer_id, t.phone_hash))

    return graph
