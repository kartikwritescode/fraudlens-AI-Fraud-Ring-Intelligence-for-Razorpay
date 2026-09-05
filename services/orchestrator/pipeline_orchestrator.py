"""
End-to-End Pipeline Orchestrator for FraudLens
Integrates every core subsystem into a unified execution flow:
Payment Event -> Ingestion -> Feature Engineering -> ML Risk -> Graph Update ->
Graph Risk -> Ring Detection -> Alert -> AI Investigation -> Financial Impact ->
Recommendation -> Human Approval Checkpoint -> Audit Log -> Dashboard State.
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import uuid

from services.ingestion.models import TransactionEvent, PipelineProcessingResult
from services.risk_engine.inference import RiskScorer
from services.graph_engine.neighbor_expander import GraphNeighborExpander
from services.graph_engine.ring_detector import AlgorithmicRingDetector
from services.agent.workflow import InvestigationAgent
from services.agent.tools import CASE_STORE
from app.core.logging import logger

# In-memory Event Store & Audit Log
EVENT_STORE: Dict[str, TransactionEvent] = {}
PROCESSED_EVENTS: Dict[str, PipelineProcessingResult] = {}
AUDIT_TRAIL: List[Dict[str, Any]] = []


class CompositeRiskConfig:
    """Configurable weights for combining transaction ML probability with graph topology signals."""
    def __init__(
        self,
        w_ml: float = 0.55,
        w_graph: float = 0.45,
        syndicate_boost: float = 0.15,
        alert_threshold: float = 0.65,
    ):
        self.w_ml = w_ml
        self.w_graph = w_graph
        self.syndicate_boost = syndicate_boost
        self.alert_threshold = alert_threshold


class EndToEndPipelineOrchestrator:
    """Central nervous system connecting Ingestion, ML, Graph, Agent, and Audit."""

    _instance: Optional["EndToEndPipelineOrchestrator"] = None

    def __init__(self, config: Optional[CompositeRiskConfig] = None):
        self.config = config or CompositeRiskConfig()
        self.scorer = RiskScorer.get_instance()
        self.expander = GraphNeighborExpander.get_instance()
        self.detector = AlgorithmicRingDetector.get_instance()

    @classmethod
    def get_instance(cls) -> "EndToEndPipelineOrchestrator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def compute_composite_risk(
        self,
        ml_score: float,
        graph_risk: float,
        is_in_ring: bool,
    ) -> Tuple[float, str]:
        """
        Combines transaction-level ML risk with graph topology risk.
        Contextually amplifies score when part of a coordinated ring.
        """
        boost = self.config.syndicate_boost if is_in_ring else 0.0
        weighted = (self.config.w_ml * ml_score) + (self.config.w_graph * graph_risk) + boost
        # Never allow network context to artificially hide an inherently anomalous transaction
        composite = min(1.0, max(ml_score, weighted))

        if composite >= 0.85:
            band = "CRITICAL"
        elif composite >= 0.65:
            band = "HIGH"
        elif composite >= 0.35:
            band = "MEDIUM"
        else:
            band = "LOW"

        return round(composite, 4), band

    def process_event(self, event: TransactionEvent) -> PipelineProcessingResult:
        """
        Executes the complete 10-step lifecycle for an incoming transaction event.
        """
        # Step 1: Idempotency & Persistence
        if event.event_id in PROCESSED_EVENTS:
            res = PROCESSED_EVENTS[event.event_id].model_copy()
            res.is_duplicate = True
            return res

        EVENT_STORE[event.event_id] = event

        # Step 2 & 3: Retrospective Feature Engineering & ML Risk Scoring
        tx_dict = {
            "transaction_id": event.transaction_id,
            "amount": event.amount,
            "currency": event.currency,
            "status": event.status,
            "customer_id": event.customer_id,
            "merchant_id": event.merchant_id,
            "payment_method": event.payment_method,
            "device_id": event.device_id,
            "ip_hash": event.ip_hash,
            "payment_token_hash": event.payment_token_hash,
            "email_hash": event.email_hash,
            "phone_hash": event.phone_hash,
            "billing_country": event.billing_country,
            "shipping_country": event.shipping_country,
            "timestamp": event.timestamp,
        }

        self.scorer.tx_lookup[event.transaction_id] = tx_dict
        ml_res = self.scorer.assess_transaction(tx_dict, update_state=True)

        # Step 4: Graph Topology Ingestion
        self.expander.tx_map[event.transaction_id] = tx_dict
        self.expander.cust_to_txs.setdefault(event.customer_id, []).append(event.transaction_id)
        self.expander.dev_to_txs.setdefault(event.device_id, []).append(event.transaction_id)
        self.expander.ip_to_txs.setdefault(event.ip_hash, []).append(event.transaction_id)
        self.expander.tok_to_txs.setdefault(event.payment_token_hash, []).append(event.transaction_id)
        self.expander.mer_to_txs.setdefault(event.merchant_id, []).append(event.transaction_id)

        # Step 5: Graph Risk & Fraud Ring Linkage
        ring = self.detector.get_ring_for_transaction(event.transaction_id)
        is_in_ring = ring is not None
        graph_risk = ring.risk_score if ring else 0.0
        cluster_id = ring.ring_id if ring else None

        # Step 6: Configurable Composite Risk Calculation
        composite_score, composite_band = self.compute_composite_risk(
            ml_score=ml_res.risk_score,
            graph_risk=graph_risk,
            is_in_ring=is_in_ring,
        )

        # Determine Alert Severity
        alert_triggered = composite_score >= self.config.alert_threshold or is_in_ring

        # Step 7 & 8: Case Creation & Autonomous AI Agent Investigation
        case_id = None
        agent_rec = None

        if alert_triggered:
            logger.info(f"[ALERT] High Composite Risk ({composite_score:.2f} {composite_band}) on {event.transaction_id}. Triggering AI Agent...")
            try:
                agent = InvestigationAgent()
                state = agent.investigate(event.transaction_id)
                case_id = state.case_id
                agent_rec = state.recommendation
            except Exception as e:
                logger.error(f"Investigation agent run failed: {e}")

        # Step 9: Audit Trail Logging
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": "EndToEndPipelineOrchestrator",
            "action": "TRANSACTION_PROCESSED",
            "case_id": case_id or "N/A",
            "details": (
                f"[{event.source_label}] Tx: {event.transaction_id} | "
                f"Composite Risk: {composite_score:.2f} ({composite_band}) | "
                f"Cluster: {cluster_id or 'None'} | Alert: {alert_triggered}"
            ),
            "result": "ALERTED" if alert_triggered else "CLEARED",
            "severity": composite_band,
        }
        AUDIT_TRAIL.append(audit_entry)

        # Step 10: Package Result
        result = PipelineProcessingResult(
            event_id=event.event_id,
            transaction_id=event.transaction_id,
            source_label=event.source_label,
            is_duplicate=False,
            risk_score=composite_score,
            risk_band=composite_band,
            reason_codes=ml_res.reason_codes,
            cluster_id=cluster_id,
            alert_triggered=alert_triggered,
            case_id=case_id,
            agent_recommendation=agent_rec,
        )

        PROCESSED_EVENTS[event.event_id] = result
        PROCESSED_EVENTS[event.transaction_id] = result

        return result
