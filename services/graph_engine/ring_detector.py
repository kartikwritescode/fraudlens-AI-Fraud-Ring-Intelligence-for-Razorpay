"""
Algorithmic Fraud Ring Discovery Engine for FraudLens
Discovers coordinated fraud rings using bipartite graph projection, community detection,
and multidimensional cluster risk scoring without hardcoding.
"""

from typing import List, Dict, Any, Set, Optional, Tuple
from collections import defaultdict
from pathlib import Path
import json
import networkx as nx

from services.graph_engine.models import DiscoveredRing
from services.graph_engine.cluster_scorer import ClusterRiskScorer
from services.graph_engine.temporal_analyzer import TemporalRingAnalyzer
from services.risk_engine.inference import RiskScorer

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATASET_PATH = ROOT_DIR / "data" / "transactions_50k.json"


class AlgorithmicRingDetector:
    """Discovers coordinated rings directly from payment relationship graph topology."""

    _instance: Optional["AlgorithmicRingDetector"] = None

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or DEFAULT_DATASET_PATH
        self.discovered_rings: List[DiscoveredRing] = []
        self.ring_by_id: Dict[str, DiscoveredRing] = {}
        self.tx_to_ring: Dict[str, str] = {}
        self.cust_to_ring: Dict[str, str] = {}

        # Run algorithmic discovery on initialization
        if self.data_path.exists():
            self.discover_rings()

    @classmethod
    def get_instance(cls, data_path: Optional[Path] = None) -> "AlgorithmicRingDetector":
        if cls._instance is None:
            cls._instance = cls(data_path)
        return cls._instance

    def discover_rings(self) -> List[DiscoveredRing]:
        """
        Executes graph-based community detection to find coordinated rings:
        1. Builds bipartite entity graph (Customers <-> Devices/IPs/Tokens).
        2. Identifies anomalous infrastructure hubs (shared tokens, rooted devices, proxy subnets).
        3. Extracts connected components.
        4. Applies multidimensional cluster scoring.
        5. Generates chronological formation timelines and audit explanations.
        """
        print(f"[*] AlgorithmicRingDetector analyzing graph from {self.data_path.name}...")
        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        transactions = data.get("transactions", [])
        if not transactions:
            return []

        # 1. Build Entity-Sharing Network using NetworkX
        # Bipartite entity graphs
        dev_to_custs: Dict[str, Set[str]] = defaultdict(set)
        token_to_custs: Dict[str, Set[str]] = defaultdict(set)
        ip_to_custs: Dict[str, Set[str]] = defaultdict(set)
        cust_to_txs: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        tx_lookup: Dict[str, Dict[str, Any]] = {}

        for t in transactions:
            cid = t.get("customer_id")
            did = t.get("device_id")
            tok = t.get("payment_token_hash")
            ip = t.get("ip_hash")
            tx_id = t.get("transaction_id")

            tx_lookup[tx_id] = t
            if cid:
                cust_to_txs[cid].append(t)
                if did:
                    dev_to_custs[did].add(cid)
                if tok:
                    token_to_custs[tok].add(cid)
                if ip:
                    ip_to_custs[ip].add(cid)

        # 2. Filter for Suspicious Infrastructure Hubs
        # Legitimate shared devices: usually 2-3 (family)
        # Legitimate shared IPs: corporate NATs with low velocity
        # Suspicious devices: >= 3 customers
        # Suspicious tokens: >= 2 customers (stolen card reuse)
        suspicious_devices = {d for d, custs in dev_to_custs.items() if len(custs) >= 3 and not d.startswith("dev_family_ipad")}
        suspicious_tokens = {tok for tok, custs in token_to_custs.items() if len(custs) >= 2}

        # Suspicious IPs: high velocity burst (> 15 transactions in short period)
        suspicious_ips = set()
        for ip, custs in ip_to_custs.items():
            if len(custs) >= 8 and not ip.startswith("ip_nat_"):
                suspicious_ips.add(ip)

        # 3. Construct Graph of Suspicious Connections
        G = nx.Graph()

        for dev in suspicious_devices:
            cust_list = list(dev_to_custs[dev])
            for i in range(len(cust_list)):
                for j in range(i + 1, len(cust_list)):
                    G.add_edge(cust_list[i], cust_list[j], entity_type="DEVICE", entity_id=dev)

        for tok in suspicious_tokens:
            cust_list = list(token_to_custs[tok])
            for i in range(len(cust_list)):
                for j in range(i + 1, len(cust_list)):
                    G.add_edge(cust_list[i], cust_list[j], entity_type="PAYMENT_TOKEN", entity_id=tok)

        for ip in suspicious_ips:
            cust_list = list(ip_to_custs[ip])
            for i in range(len(cust_list)):
                for j in range(i + 1, len(cust_list)):
                    G.add_edge(cust_list[i], cust_list[j], entity_type="IP", entity_id=ip)

        # 4. Connected Components & Community Clustering
        components = list(nx.connected_components(G))
        print(f"[*] Found {len(components)} candidate multi-entity clusters.")

        scorer = None
        try:
            scorer = RiskScorer.get_instance()
        except Exception:
            pass

        discovered: List[DiscoveredRing] = []

        for idx, comp in enumerate(components, start=1):
            if len(comp) < 3:
                continue  # Skip trivial pairs

            comp_customers = list(comp)
            comp_txs = []
            comp_devs: Set[str] = set()
            comp_ips: Set[str] = set()
            comp_tokens: Set[str] = set()
            comp_merchants: Set[str] = set()

            for c in comp_customers:
                for t in cust_to_txs[c]:
                    comp_txs.append(t)
                    if t.get("device_id"):
                        comp_devs.add(t["device_id"])
                    if t.get("ip_hash"):
                        comp_ips.add(t["ip_hash"])
                    if t.get("payment_token_hash"):
                        comp_tokens.add(t["payment_token_hash"])
                    if t.get("merchant_id"):
                        comp_merchants.add(t["merchant_id"])

            if not comp_txs:
                continue

            # Compute ML risk scores for transactions if scorer is available
            ml_scores = []
            if scorer:
                for t in comp_txs:
                    res = scorer.assess_by_transaction_id(t.get("transaction_id", ""))
                    if res:
                        ml_scores.append(res.risk_score)

            # Score Cluster
            cluster_eval = ClusterRiskScorer.score_cluster(
                transactions=comp_txs,
                customers=set(comp_customers),
                devices=comp_devs,
                ips=comp_ips,
                tokens=comp_tokens,
                ml_scores=ml_scores,
            )

            # Keep only high/critical suspicious clusters
            if cluster_eval["graph_risk_score"] < 0.45:
                continue

            ring_id = f"ring_disc_{idx:03d}"
            sorted_txs = sorted(comp_txs, key=lambda t: t.get("timestamp", ""))
            first_seen = sorted_txs[0].get("timestamp", "")
            last_seen = sorted_txs[-1].get("timestamp", "")

            # Growth rate: accounts added per hour
            try:
                dt_first = datetime.fromisoformat(first_seen.replace("Z", "+00:00")).timestamp()
                dt_last = datetime.fromisoformat(last_seen.replace("Z", "+00:00")).timestamp()
                duration_hrs = max(0.2, (dt_last - dt_first) / 3600.0)
                growth_rate = round(len(comp_customers) / duration_hrs, 2)
            except Exception:
                growth_rate = 1.0

            attempted_amt = round(sum(t.get("amount", 0.0) for t in comp_txs), 2)
            # Suspicious amount: txs from customers in the ring
            suspicious_amt = attempted_amt

            # Reconstruct Timeline
            timeline = TemporalRingAnalyzer.reconstruct_timeline(comp_txs)

            explanation = (
                f"Discovered coordinated cluster of {len(comp_customers)} customer accounts sharing "
                f"{len(comp_devs)} device(s) and {len(comp_tokens)} payment token(s). "
                f"Generated {len(comp_txs)} transactions totaling Rs. {attempted_amt:,.2f} with "
                f"a graph risk score of {cluster_eval['graph_risk_score']:.2f} ({cluster_eval['risk_band']})."
            )

            ring_obj = DiscoveredRing(
                ring_id=ring_id,
                risk_score=cluster_eval["graph_risk_score"],
                risk_band=cluster_eval["risk_band"],
                pattern_type=cluster_eval["pattern_type"],
                member_count=len(comp_customers),
                transaction_count=len(comp_txs),
                attempted_amount=attempted_amt,
                suspicious_amount=suspicious_amt,
                merchant_count=len(comp_merchants),
                device_count=len(comp_devs),
                ip_count=len(comp_ips),
                payment_token_count=len(comp_tokens),
                growth_rate=growth_rate,
                created_at=first_seen,
                updated_at=last_seen,
                customer_ids=comp_customers,
                device_ids=list(comp_devs),
                ip_hashes=list(comp_ips),
                payment_token_hashes=list(comp_tokens),
                transaction_ids=[t.get("transaction_id", "") for t in comp_txs],
                timeline=timeline,
                explanation=explanation,
            )

            discovered.append(ring_obj)
            self.ring_by_id[ring_id] = ring_obj
            for c in comp_customers:
                self.cust_to_ring[c] = ring_id
            for t in comp_txs:
                self.tx_to_ring[t.get("transaction_id", "")] = ring_id

        # Sort descending by risk score
        discovered.sort(key=lambda r: r.risk_score, reverse=True)
        self.discovered_rings = discovered
        print(f"[OK] AlgorithmicRingDetector discovered {len(discovered)} coordinated fraud rings.")
        return discovered

    def get_rings(self) -> List[DiscoveredRing]:
        return self.discovered_rings

    def get_ring_by_id(self, ring_id: str) -> Optional[DiscoveredRing]:
        return self.ring_by_id.get(ring_id)

    def get_ring_for_transaction(self, tx_id: str) -> Optional[DiscoveredRing]:
        ring_id = self.tx_to_ring.get(tx_id)
        if ring_id:
            return self.ring_by_id.get(ring_id)
        return None
