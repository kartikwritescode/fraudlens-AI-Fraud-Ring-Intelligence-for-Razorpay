"""
Scenario Manager for FraudLens Enterprise Threat Simulation
Deterministically simulates FRAUD RING #042:
- Wave 1: 3 initial transactions with moderate/high risk
- Wave 2: Coordinated multi-entity ring:
    37 customers, 5 devices, 3 IP ranges, 2 payment tokens, 4 merchants
- Attempted volume: dynamically generated ~Rs. 8.4-8.9 Lakh
- Clean resetScenario() functionality with state snapshotting
"""

import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from services.ingestion.models import TransactionEvent
from services.orchestrator.pipeline_orchestrator import EndToEndPipelineOrchestrator
from services.risk_engine.inference import RiskScorer
from services.graph_engine.neighbor_expander import GraphNeighborExpander
from services.graph_engine.ring_detector import AlgorithmicRingDetector, DiscoveredRing
from services.agent.workflow import InvestigationAgent
from services.agent.tools import CASE_STORE
from services.agent.models import CaseRecord, InvestigationReport, FinancialImpactResult
import app.api.v1.endpoints.analytics as analytics_module
from app.core.logging import logger


class DemoScenarioManager:
    """Manages the deterministic execution and reset of Fraud Ring #042 demo."""

    _instance: Optional["DemoScenarioManager"] = None

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.injected_tx_ids: List[str] = []
        self.injected_ring_id: Optional[str] = None
        self.case_id: str = "CASE-0042"
        self.is_active: bool = False

    @classmethod
    def get_instance(cls) -> "DemoScenarioManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate_scenario_transactions(self) -> List[Dict[str, Any]]:
        """
        Deterministically produces transactions for Fraud Ring #042:
        37 customers, 5 devices, 3 IP ranges, 2 tokens, 4 merchants, ~Rs. 8-9 Lakh.
        """
        rng = random.Random(self.seed)

        customers = [f"cust_ring042_{i+1:02d}" for i in range(37)]
        devices = [
            "dev_ring042_alpha",
            "dev_ring042_bravo",
            "dev_ring042_charlie",
            "dev_ring042_delta",
            "dev_ring042_echo",
        ]
        ips = [
            "ip_ring042_sub_49_204",
            "ip_ring042_sub_103_21",
            "ip_ring042_sub_157_48",
        ]
        tokens = [
            "tok_ring042_corp_card_01",
            "tok_ring042_visa_token_02",
        ]
        merchants = ["mer_0012", "mer_0042", "mer_0077", "mer_0099"]

        tx_list = []
        now = datetime.now(timezone.utc)

        # Wave 1: 3 Initial suspicious exploratory transactions
        wave1_amts = [18500.0, 21200.0, 19800.0]
        for i in range(3):
            tx_id = f"tx_ring042_w1_{i+1:02d}"
            tx_list.append({
                "transaction_id": tx_id,
                "customer_id": customers[i],
                "merchant_id": merchants[i % len(merchants)],
                "amount": wave1_amts[i],
                "device_id": devices[i % 2],
                "ip_hash": ips[0],
                "payment_token_hash": tokens[0],
                "wave": 1,
                "timestamp": (now - timedelta(minutes=15 - i * 3)).isoformat(),
            })

        # Wave 2: 34 Additional transactions executing the coordinated ring
        # Generating dynamic amounts such that sum is ~8.5-8.8 Lakh
        for i in range(3, 37):
            cust = customers[i]
            dev = rng.choice(devices)
            ip_val = rng.choice(ips)
            tok = rng.choice(tokens)
            mer = rng.choice(merchants)
            amt = round(rng.uniform(22000.0, 27500.0), 2)
            tx_id = f"tx_ring042_w2_{i+1:02d}"

            tx_list.append({
                "transaction_id": tx_id,
                "customer_id": cust,
                "merchant_id": mer,
                "amount": amt,
                "device_id": dev,
                "ip_hash": ip_val,
                "payment_token_hash": tok,
                "wave": 2,
                "timestamp": (now - timedelta(minutes=5 - rng.randint(0, 4))).isoformat(),
            })

        return tx_list

    def start_scenario(self) -> Dict[str, Any]:
        """
        Executes the live pipeline across Wave 1 and Wave 2 of Fraud Ring #042.
        """
        self.reset_scenario()  # Ensure clean slate before launching
        orchestrator = EndToEndPipelineOrchestrator.get_instance()
        detector = AlgorithmicRingDetector.get_instance()

        txs = self.generate_scenario_transactions()
        self.injected_tx_ids = [t["transaction_id"] for t in txs]
        total_attempted = sum(t["amount"] for t in txs)

        # Process through real pipeline
        for t in txs:
            evt = TransactionEvent(
                event_id=f"evt_{t['transaction_id']}",
                source_mode="FRAUDLENS_DEMO_MODE",
                source_label="FraudLens Ring #042 Simulation",
                event_type="payment.authorized",
                transaction_id=t["transaction_id"],
                amount=t["amount"],
                currency="INR",
                status="authorized",
                customer_id=t["customer_id"],
                merchant_id=t["merchant_id"],
                payment_method="card",
                device_id=t["device_id"],
                ip_hash=t["ip_hash"],
                payment_token_hash=t["payment_token_hash"],
                billing_country="IND",
                shipping_country="IND",
                timestamp=t["timestamp"],
            )
            orchestrator.process_event(evt)

        # Formally register FRAUD RING #042 in AlgorithmicRingDetector
        ring_042 = DiscoveredRing(
            ring_id="FRAUD RING #042",
            risk_score=0.998,
            risk_band="CRITICAL",
            pattern_type="distributed_multi_entity_syndicate",
            member_count=37,
            transaction_count=len(txs),
            attempted_amount=round(total_attempted, 2),
            suspicious_amount=round(total_attempted * 0.95, 2),
            merchant_count=4,
            device_count=5,
            ip_count=3,
            payment_token_count=2,
            growth_rate=8.4,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            customer_ids=[t["customer_id"] for t in txs],
            device_ids=["dev_ring042_alpha", "dev_ring042_bravo", "dev_ring042_charlie", "dev_ring042_delta", "dev_ring042_echo"],
            ip_hashes=["ip_ring042_sub_49_204", "ip_ring042_sub_103_21", "ip_ring042_sub_157_48"],
            payment_token_hashes=["tok_ring042_corp_card_01", "tok_ring042_visa_token_02"],
            transaction_ids=self.injected_tx_ids,
            timeline=[
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_type": "BURST_DETECTED",
                    "title": "Coordinated High-Volume Attack Burst",
                    "description": f"37 puppet customer accounts initiated Rs. {total_attempted:,.2f} in card attempts.",
                    "severity": "critical",
                    "entities_involved": ["FRAUD RING #042"],
                },
                {
                    "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
                    "event_type": "TOKEN_SHARED",
                    "title": "Stolen Card Token Distributed",
                    "description": "2 corporate tokens linked across 5 hardware fingerprints.",
                    "severity": "critical",
                    "entities_involved": ["tok_ring042_corp_card_01", "tok_ring042_visa_token_02"],
                },
                {
                    "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat(),
                    "event_type": "ENTITY_JOINED",
                    "title": "Initial Exploratory Transactions",
                    "description": "3 exploratory authorizations executed through proxy subnet.",
                    "severity": "warning",
                    "entities_involved": ["tx_ring042_w1_01", "tx_ring042_w1_02", "tx_ring042_w1_03"],
                },
            ],
            explanation=(
                f"Coordinated multi-entity syndicate comprising 37 puppet accounts sharing 2 stolen credit tokens "
                f"across 5 rotating device fingerprints. Attempted volume: Rs. {total_attempted:,.2f} across 4 merchants."
            ),
        )

        detector.ring_by_id["FRAUD RING #042"] = ring_042
        if hasattr(detector, "discovered_rings"):
            detector.discovered_rings = [r for r in detector.discovered_rings if r.ring_id != "FRAUD RING #042"]
            detector.discovered_rings.insert(0, ring_042)
        for tid in self.injected_tx_ids:
            detector.tx_to_ring[tid] = "FRAUD RING #042"
        for c in ring_042.customer_ids:
            detector.cust_to_ring[c] = "FRAUD RING #042"

        self.injected_ring_id = "FRAUD RING #042"

        # Trigger Investigation Agent for CASE-0042
        agent = InvestigationAgent()
        state = agent.investigate(self.injected_tx_ids[0])

        # Synthesize dedicated CASE-0042 Dossier
        case_042 = CaseRecord(
            case_id=self.case_id,
            title="FRAUD RING #042 - Coordinated Multi-Entity Syndicate",
            severity="CRITICAL",
            status="OPEN",
            primary_transaction_id=self.injected_tx_ids[0],
            associated_transactions=self.injected_tx_ids,
            associated_entities={
                "customers": [t["customer_id"] for t in txs],
                "devices": ring_042.device_ids,
                "tokens": ring_042.payment_token_hashes,
                "ips": ring_042.ip_hashes,
            },
            report=InvestigationReport(
                executive_summary=(
                    f"Investigation completed for FRAUD RING #042. Coordinated syndicate detected linking 37 puppet "
                    f"accounts, 5 devices, and 2 compromised payment tokens across 4 target merchants. "
                    f"Total attempted volume: Rs. {total_attempted:,.2f}. Network exposure: Rs. {total_attempted * 1.3:,.2f}. "
                    f"Recommended Action: STEP-UP + REVIEW (Confidence: 98%)."
                ),
                observed_facts=[
                    f"FACT: 37 customer accounts linked through 2 corporate card instrument tokens.",
                    f"FACT: 5 distinct hardware device fingerprints rotated across all authorization requests.",
                    f"FACT: Total attempted volume across cluster is Rs. {total_attempted:,.2f}.",
                    f"FACT: Multi-entity graph modularity score is 0.998 (CRITICAL).",
                    f"FACT: 4 target merchant endpoints attacked concurrently within rolling 15-minute window.",
                ],
                transaction_evidence={"count": len(txs), "sample_amount": txs[0]["amount"]},
                network_evidence={"cluster_id": "FRAUD RING #042", "members": 37, "tokens": 2, "devices": 5},
                behavioral_evidence={"velocity_5m": len(txs), "burst_factor": 8.4},
                financial_impact=FinancialImpactResult(
                    attempted_fraud_value=round(total_attempted, 2),
                    suspicious_value=round(total_attempted * 1.15, 2),
                    estimated_exposure=round(total_attempted * 1.30, 2),
                    estimated_false_positive_cost=round(total_attempted * 0.02 + 750.0, 2),
                    expected_loss_by_action={
                        "ALLOW": round(total_attempted * 0.98, 2),
                        "MONITOR": round(total_attempted * 0.75, 2),
                        "STEP_UP": 4250.0,
                        "REVIEW": 2850.0,
                        "HOLD": 950.0,
                    },
                    optimal_action_by_loss="STEP_UP",
                ),
                fraud_hypotheses=[
                    "HYPOTHESIS: Coordinated corporate credit card credential compromise distributed across synthetic accounts.",
                    "HYPOTHESIS: Attackers attempting distributed transaction testing to evade individual customer velocity limits.",
                ],
                confidence=0.98,
                recommended_action="STEP_UP",
                requires_human_approval=True,
                approval_status="PENDING_APPROVAL",
                generated_at=datetime.now(timezone.utc).isoformat(),
            ),
            decisions=[],
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

        CASE_STORE[self.case_id] = case_042

        # Invalidate dashboard telemetry cache so next query re-computes immediately
        analytics_module.invalidate_analytics_cache()
        self.is_active = True

        return {
            "scenario": "FRAUD RING #042",
            "status": "DETECTED",
            "customers": 37,
            "devices": 5,
            "ips": 3,
            "payment_tokens": 2,
            "merchants": 4,
            "attempted_volume_inr": round(total_attempted, 2),
            "case_id": self.case_id,
            "ring_id": "FRAUD RING #042",
            "risk_band": "CRITICAL",
            "recommended_action": "STEP-UP + REVIEW",
            "confidence": 0.98,
            "sample_transactions": self.injected_tx_ids[:5],
        }

    def reset_scenario(self) -> Dict[str, Any]:
        """
        Reliably cleanses injected demo transactions and restores system baseline.
        """
        scorer = RiskScorer.get_instance()
        expander = GraphNeighborExpander.get_instance()
        detector = AlgorithmicRingDetector.get_instance()

        # 1. Purge injected transactions from RiskScorer lookup
        for tid in self.injected_tx_ids:
            scorer.tx_lookup.pop(tid, None)
            scorer.tx_feature_cache.pop(tid, None)
            expander.tx_map.pop(tid, None)
            detector.tx_to_ring.pop(tid, None)

        # 2. Remove FRAUD RING #042 from detector
        detector.ring_by_id.pop("FRAUD RING #042", None)
        if hasattr(detector, "discovered_rings"):
            detector.discovered_rings = [r for r in detector.discovered_rings if r.ring_id != "FRAUD RING #042"]
        if hasattr(detector, "cust_to_ring"):
            detector.cust_to_ring = {k: v for k, v in detector.cust_to_ring.items() if v != "FRAUD RING #042"}

        # 3. Clean case store
        CASE_STORE.pop(self.case_id, None)

        # 4. Invalidate analytics cache
        analytics_module.invalidate_analytics_cache()

        self.injected_tx_ids = []
        self.injected_ring_id = None
        self.is_active = False

        logger.info("[OK] Demo Scenario reset cleanly completed.")
        return {"status": "RESET_SUCCESSFUL", "message": "Demo state cleanly restored."}
