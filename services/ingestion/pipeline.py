"""
Unified Ingestion Pipeline Orchestrator for FraudLens
Coordinates event idempotency, persistence, ML risk scoring, graph updates,
and autonomous AI investigation triggering.
Handles both Razorpay Test Mode and FraudLens Synthetic Demo Mode through the same pipeline.
"""

from typing import Dict, Any, Optional, Set, List
from datetime import datetime, timezone
import json

from services.ingestion.models import TransactionEvent, PipelineProcessingResult
from services.risk_engine.inference import RiskScorer
from services.graph_engine.neighbor_expander import GraphNeighborExpander
from services.graph_engine.ring_detector import AlgorithmicRingDetector
from services.agent.workflow import InvestigationAgent
from app.core.logging import logger

# In-memory Event Store & Idempotency Cache
EVENT_STORE: Dict[str, TransactionEvent] = {}
PROCESSED_EVENTS: Dict[str, PipelineProcessingResult] = {}


class PipelineOrchestrator:
    """Central processing pipeline for payment events."""

    _instance: Optional["PipelineOrchestrator"] = None

    def __init__(self):
        self.seen_events: Set[str] = set()
        self.seen_transactions: Set[str] = set()

    @classmethod
    def get_instance(cls) -> "PipelineOrchestrator":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def process_event(self, event: TransactionEvent) -> PipelineProcessingResult:
        """
        Processes a normalized TransactionEvent:
        1. Idempotency validation (deduplicates repeated webhooks).
        2. Event persistence.
        3. Real-time ML Risk Scoring (XGBoost + SHAP).
        4. Graph Engine topology update.
        5. Ring linkage & Autonomous Investigation trigger.
        """
        # 1. Idempotency Check
        if event.event_id in self.seen_events or event.transaction_id in self.seen_transactions:
            logger.info(f"Duplicate event/transaction detected: {event.event_id} ({event.transaction_id}). Returning cached result.")
            existing = PROCESSED_EVENTS.get(event.event_id) or PROCESSED_EVENTS.get(event.transaction_id)
            if existing:
                res = existing.model_copy()
                res.is_duplicate = True
                return res
            # Fallback duplicate response
            return PipelineProcessingResult(
                event_id=event.event_id,
                transaction_id=event.transaction_id,
                source_label=event.source_label,
                is_duplicate=True,
                risk_score=0.0,
                risk_band="LOW",
                reason_codes=["Duplicate event acknowledged without re-processing"],
            )

        # 2. Persist event into store
        EVENT_STORE[event.event_id] = event
        self.seen_events.add(event.event_id)
        self.seen_transactions.add(event.transaction_id)

        # 3. ML Risk Scoring
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

        scorer = RiskScorer.get_instance()
        # Add to index and evaluate
        scorer.tx_lookup[event.transaction_id] = tx_dict
        ml_res = scorer.assess_transaction(tx_dict, update_state=True)

        # 4. Update Graph Expander Index
        expander = GraphNeighborExpander.get_instance()
        expander.tx_map[event.transaction_id] = tx_dict
        expander.cust_to_txs.setdefault(event.customer_id, []).append(event.transaction_id)
        expander.dev_to_txs.setdefault(event.device_id, []).append(event.transaction_id)
        expander.ip_to_txs.setdefault(event.ip_hash, []).append(event.transaction_id)
        expander.tok_to_txs.setdefault(event.payment_token_hash, []).append(event.transaction_id)
        expander.mer_to_txs.setdefault(event.merchant_id, []).append(event.transaction_id)

        # Check for ring cluster linkage
        detector = AlgorithmicRingDetector.get_instance()
        ring = detector.get_ring_for_transaction(event.transaction_id)
        cluster_id = ring.ring_id if ring else None

        # 5. Alert & Autonomous Investigation
        alert_triggered = False
        case_id = None
        agent_rec = None

        if ml_res.risk_score >= 0.70 or ml_res.risk_band in ["HIGH", "CRITICAL"] or cluster_id is not None:
            alert_triggered = True
            logger.info(f"High risk ({ml_res.risk_score:.2f}) or cluster link on {event.transaction_id}. Spawning Investigation Agent...")
            try:
                agent = InvestigationAgent()
                state = agent.investigate(event.transaction_id)
                case_id = state.case_id
                agent_rec = state.recommendation
            except Exception as e:
                logger.error(f"Investigation Agent execution encountered error: {e}")

        result = PipelineProcessingResult(
            event_id=event.event_id,
            transaction_id=event.transaction_id,
            source_label=event.source_label,
            is_duplicate=False,
            risk_score=ml_res.risk_score,
            risk_band=ml_res.risk_band,
            reason_codes=ml_res.reason_codes,
            cluster_id=cluster_id,
            alert_triggered=alert_triggered,
            case_id=case_id,
            agent_recommendation=agent_rec,
        )

        PROCESSED_EVENTS[event.event_id] = result
        PROCESSED_EVENTS[event.transaction_id] = result

        logger.info(
            f"Pipeline processed [{event.source_label}] Tx: {event.transaction_id} | "
            f"Score: {ml_res.risk_score:.2f} ({ml_res.risk_band}) | Alert: {alert_triggered}"
        )
        return result
