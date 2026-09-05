"""
Graph Neighbor Expansion & Subgraph Visualizer for FraudLens
Traverses multi-hop entity neighborhoods and formats interactive graph payloads
suitable for React Flow, Cytoscape.js, and command center graph UI.
"""

from typing import Dict, Any, List, Set, Optional, Tuple
from pathlib import Path
import json

from services.graph_engine.models import (
    GraphNode,
    GraphEdge,
    GraphNetworkResponse,
)
from services.graph_engine.ring_detector import AlgorithmicRingDetector
from services.risk_engine.inference import RiskScorer

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET_PATH = ROOT_DIR / "data" / "transactions_50k.json"


class GraphNeighborExpander:
    """Performs k-hop neighborhood expansion around transactions and entities."""

    _instance: Optional["GraphNeighborExpander"] = None

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or DEFAULT_DATASET_PATH
        self.tx_map: Dict[str, Dict[str, Any]] = {}
        self.cust_to_txs: Dict[str, List[str]] = {}
        self.dev_to_txs: Dict[str, List[str]] = {}
        self.ip_to_txs: Dict[str, List[str]] = {}
        self.tok_to_txs: Dict[str, List[str]] = {}
        self.mer_to_txs: Dict[str, List[str]] = {}

        if self.data_path.exists():
            self._build_index()

    def _build_index(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for t in data.get("transactions", []):
            tid = t.get("transaction_id")
            self.tx_map[tid] = t

            cid = t.get("customer_id")
            did = t.get("device_id")
            ip = t.get("ip_hash")
            tok = t.get("payment_token_hash")
            mid = t.get("merchant_id")

            if cid: self.cust_to_txs.setdefault(cid, []).append(tid)
            if did: self.dev_to_txs.setdefault(did, []).append(tid)
            if ip: self.ip_to_txs.setdefault(ip, []).append(tid)
            if tok: self.tok_to_txs.setdefault(tok, []).append(tid)
            if mid: self.mer_to_txs.setdefault(mid, []).append(tid)

    @classmethod
    def get_instance(cls, data_path: Optional[Path] = None) -> "GraphNeighborExpander":
        if cls._instance is None:
            cls._instance = cls(data_path)
        return cls._instance

    def expand_transaction_subgraph(
        self, transaction_id: str, hops: int = 2, max_nodes: int = 50
    ) -> Optional[GraphNetworkResponse]:
        """Expands a 1-2 hop neighborhood around a transaction."""
        tx = self.tx_map.get(transaction_id)
        if not tx:
            return None

        detector = AlgorithmicRingDetector.get_instance()
        associated_ring = detector.get_ring_for_transaction(transaction_id)

        nodes: Dict[str, GraphNode] = {}
        edges: Dict[str, GraphEdge] = {}

        scorer = None
        try:
            scorer = RiskScorer.get_instance()
        except Exception:
            pass

        # 1. Center Transaction Node
        tx_score = 0.95 if tx.get("is_fraud") else 0.05
        tx_band = "CRITICAL" if tx.get("is_fraud") else "LOW"
        if scorer:
            res = scorer.assess_by_transaction_id(transaction_id)
            if res:
                tx_score = res.risk_score
                tx_band = res.risk_band

        nodes[transaction_id] = GraphNode(
            id=transaction_id,
            label=f"Tx: {transaction_id[-8:]}",
            type="Transaction",
            risk_score=tx_score,
            risk_band=tx_band,
            properties={
                "amount": tx.get("amount"),
                "currency": tx.get("currency", "INR"),
                "status": tx.get("status"),
                "timestamp": tx.get("timestamp"),
                "is_fraud": tx.get("is_fraud"),
            },
        )

        # 2. Direct 1-hop entities from transaction
        cid = tx.get("customer_id")
        mid = tx.get("merchant_id")
        did = tx.get("device_id")
        ip = tx.get("ip_hash")
        tok = tx.get("payment_token_hash")

        # Customer
        if cid:
            nodes[cid] = GraphNode(
                id=cid,
                label=f"Cust: {cid[-6:]}",
                type="Customer",
                risk_score=tx_score,
                risk_band=tx_band,
            )
            edges[f"{cid}->{transaction_id}"] = GraphEdge(
                id=f"e_{cid}_{transaction_id}",
                source=cid,
                target=transaction_id,
                type="CUSTOMER_MADE_TRANSACTION",
                label="MADE",
                timestamp=tx.get("timestamp"),
            )

        # Merchant
        if mid:
            nodes[mid] = GraphNode(
                id=mid,
                label=f"Mer: {mid[-6:]}",
                type="Merchant",
                risk_score=0.1,
                risk_band="LOW",
            )
            edges[f"{transaction_id}->{mid}"] = GraphEdge(
                id=f"e_{transaction_id}_{mid}",
                source=transaction_id,
                target=mid,
                type="TRANSACTION_FOR_MERCHANT",
                label="FOR",
            )

        # Device
        if did:
            dev_custs = len([t for t in self.dev_to_txs.get(did, [])])
            is_sus = dev_custs >= 3
            nodes[did] = GraphNode(
                id=did,
                label=f"Dev: {did[-8:]}",
                type="Device",
                risk_score=0.90 if is_sus else 0.10,
                risk_band="CRITICAL" if is_sus else "LOW",
                properties={"reuse_count": dev_custs},
            )
            edges[f"{transaction_id}->{did}"] = GraphEdge(
                id=f"e_{transaction_id}_{did}",
                source=transaction_id,
                target=did,
                type="TRANSACTION_FROM_DEVICE",
                label="FROM_DEVICE",
                is_suspicious=is_sus,
            )
            if cid:
                edges[f"{cid}->{did}"] = GraphEdge(
                    id=f"e_{cid}_{did}",
                    source=cid,
                    target=did,
                    type="CUSTOMER_USES_DEVICE",
                    label="USES_DEVICE",
                    is_suspicious=is_sus,
                )

        # IP
        if ip:
            nodes[ip] = GraphNode(
                id=ip,
                label=f"IP: {ip[-8:]}",
                type="IP",
                risk_score=0.20,
                risk_band="LOW",
            )
            edges[f"{transaction_id}->{ip}"] = GraphEdge(
                id=f"e_{transaction_id}_{ip}",
                source=transaction_id,
                target=ip,
                type="TRANSACTION_FROM_IP",
                label="FROM_IP",
            )
            if cid:
                edges[f"{cid}->{ip}"] = GraphEdge(
                    id=f"e_{cid}_{ip}",
                    source=cid,
                    target=ip,
                    type="CUSTOMER_USES_IP",
                    label="USES_IP",
                )

        # Payment Token
        if tok:
            tok_custs = len(self.tok_to_txs.get(tok, []))
            is_tok_sus = tok_custs >= 2
            nodes[tok] = GraphNode(
                id=tok,
                label=f"Card: {tok[-6:]}",
                type="PaymentToken",
                risk_score=0.92 if is_tok_sus else 0.10,
                risk_band="CRITICAL" if is_tok_sus else "LOW",
            )
            if cid:
                edges[f"{cid}->{tok}"] = GraphEdge(
                    id=f"e_{cid}_{tok}",
                    source=cid,
                    target=tok,
                    type="CUSTOMER_USES_PAYMENT_TOKEN",
                    label="USES_TOKEN",
                    is_suspicious=is_tok_sus,
                )

        # 3. 2-hop expansion (Neighboring accounts on shared device / token)
        if hops >= 2 and len(nodes) < max_nodes:
            neighbor_tx_ids = set()
            if did:
                neighbor_tx_ids.update(self.dev_to_txs.get(did, [])[:8])
            if tok:
                neighbor_tx_ids.update(self.tok_to_txs.get(tok, [])[:8])

            for n_tid in neighbor_tx_ids:
                if len(nodes) >= max_nodes:
                    break
                if n_tid == transaction_id:
                    continue

                n_tx = self.tx_map.get(n_tid)
                if not n_tx:
                    continue

                n_cid = n_tx.get("customer_id")
                n_is_fraud = n_tx.get("is_fraud", False)

                nodes[n_tid] = GraphNode(
                    id=n_tid,
                    label=f"Tx: {n_tid[-8:]}",
                    type="Transaction",
                    risk_score=0.90 if n_is_fraud else 0.10,
                    risk_band="CRITICAL" if n_is_fraud else "LOW",
                    properties={"amount": n_tx.get("amount")},
                )

                if did and n_tx.get("device_id") == did:
                    edges[f"{n_tid}->{did}"] = GraphEdge(
                        id=f"e_{n_tid}_{did}",
                        source=n_tid,
                        target=did,
                        type="TRANSACTION_FROM_DEVICE",
                        label="FROM_DEVICE",
                        is_suspicious=True,
                    )

                if n_cid and n_cid not in nodes:
                    nodes[n_cid] = GraphNode(
                        id=n_cid,
                        label=f"Cust: {n_cid[-6:]}",
                        type="Customer",
                        risk_score=0.90 if n_is_fraud else 0.10,
                        risk_band="CRITICAL" if n_is_fraud else "LOW",
                    )
                    edges[f"{n_cid}->{n_tid}"] = GraphEdge(
                        id=f"e_{n_cid}_{n_tid}",
                        source=n_cid,
                        target=n_tid,
                        type="CUSTOMER_MADE_TRANSACTION",
                        label="MADE",
                    )

        return GraphNetworkResponse(
            center_id=transaction_id,
            center_type="Transaction",
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            node_count=len(nodes),
            edge_count=len(edges),
            cluster_id=associated_ring.ring_id if associated_ring else None,
            cluster_risk_score=associated_ring.risk_score if associated_ring else None,
        )

    def expand_entity_neighbors(
        self, entity_id: str, hops: int = 1, max_nodes: int = 30
    ) -> GraphNetworkResponse:
        """Expands neighbors around any entity (customer, device, IP, token)."""
        nodes: Dict[str, GraphNode] = {}
        edges: Dict[str, GraphEdge] = {}

        # Determine entity type from prefix
        if entity_id.startswith("cust_"):
            e_type = "Customer"
            related_txs = self.cust_to_txs.get(entity_id, [])[:15]
        elif entity_id.startswith("dev_"):
            e_type = "Device"
            related_txs = self.dev_to_txs.get(entity_id, [])[:15]
        elif entity_id.startswith("ip_"):
            e_type = "IP"
            related_txs = self.ip_to_txs.get(entity_id, [])[:15]
        elif entity_id.startswith("tok_"):
            e_type = "PaymentToken"
            related_txs = self.tok_to_txs.get(entity_id, [])[:15]
        elif entity_id.startswith("mer_"):
            e_type = "Merchant"
            related_txs = self.mer_to_txs.get(entity_id, [])[:15]
        else:
            e_type = "Entity"
            related_txs = []

        nodes[entity_id] = GraphNode(
            id=entity_id,
            label=f"{e_type}: {entity_id[-8:]}",
            type=e_type,
            risk_score=0.5,
            risk_band="MEDIUM",
        )

        for tid in related_txs:
            if len(nodes) >= max_nodes:
                break
            tx = self.tx_map.get(tid)
            if not tx:
                continue

            nodes[tid] = GraphNode(
                id=tid,
                label=f"Tx: {tid[-8:]}",
                type="Transaction",
                risk_score=0.9 if tx.get("is_fraud") else 0.1,
                risk_band="CRITICAL" if tx.get("is_fraud") else "LOW",
            )
            edges[f"{entity_id}_{tid}"] = GraphEdge(
                id=f"e_{entity_id}_{tid}",
                source=entity_id,
                target=tid,
                type="CONNECTED_TO",
                label="LINKED",
            )

        return GraphNetworkResponse(
            center_id=entity_id,
            center_type=e_type,
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            node_count=len(nodes),
            edge_count=len(edges),
        )
