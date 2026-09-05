"""
Cluster Risk Scoring Engine for FraudLens
Combines multi-signal graph topology, entity sharing rarity, temporal concentration,
velocity, and ML risk scores to compute a robust, calibrated graph_risk_score.
Prevents false positives on benign shared infrastructure (campus Wi-Fi, family devices).
"""

from typing import Dict, Any, List, Set, Optional
from datetime import datetime, timezone
import numpy as np


class ClusterRiskScorer:
    """Calculates multidimensional graph risk score for connected entity components."""

    @staticmethod
    def score_cluster(
        transactions: List[Dict[str, Any]],
        customers: Set[str],
        devices: Set[str],
        ips: Set[str],
        tokens: Set[str],
        ml_scores: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Computes calibrated graph risk score between 0.0 and 1.0.
        Returns score, band, risk factors breakdown, and pattern classification.
        """
        if not transactions:
            return {
                "graph_risk_score": 0.0,
                "risk_band": "LOW",
                "factors": {},
                "pattern_type": "inactive_component",
            }

        # 1. Temporal Analysis
        timestamps = []
        for t in transactions:
            ts_str = t.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
                timestamps.append(dt)
            except Exception:
                pass

        if len(timestamps) > 1:
            timestamps.sort()
            duration_hours = max(0.01, (timestamps[-1] - timestamps[0]) / 3600.0)
            tx_per_hour = len(transactions) / duration_hours
            # Temporal concentration: 1.0 if all txs in < 2 hours, fades to 0.1 if spread over 20+ days
            temporal_concentration = min(1.0, 4.0 / max(1.0, duration_hours))
        else:
            duration_hours = 0.5
            tx_per_hour = 1.0
            temporal_concentration = 0.2

        # 2. Entity Sharing & Rarity Signals
        cust_count = max(1, len(customers))
        dev_count = max(1, len(devices))
        token_count = max(1, len(tokens))
        ip_count = max(1, len(ips))

        # A. Shared Token Ratio: distinct customers per payment token
        # In legitimate payments, 1 token is rarely used by > 1 customer
        cust_per_token = cust_count / token_count if token_count > 0 else 1.0
        token_reuse_signal = min(1.0, (cust_per_token - 1.0) / 4.0) if cust_per_token > 1.0 else 0.0

        # B. Shared Device Ratio: distinct customers per device
        # 1-2 per device is normal (family), 5+ is highly suspicious
        cust_per_device = cust_count / dev_count if dev_count > 0 else 1.0
        device_reuse_signal = min(1.0, (cust_per_device - 2.0) / 5.0) if cust_per_device > 2.0 else 0.0

        # C. Shared IP alone is low-signal unless accompanied by high velocity
        # (e.g. 50 users on campus Wi-Fi over 30 days is normal)
        cust_per_ip = cust_count / ip_count if ip_count > 0 else 1.0
        ip_velocity_signal = min(1.0, (tx_per_hour / 10.0)) if cust_per_ip > 3.0 else 0.0

        # 3. Transaction Failure Ratio
        failed_count = sum(1 for t in transactions if t.get("status") in ["failed", "blocked"])
        failure_ratio = failed_count / len(transactions)

        # 4. ML Risk Density
        if ml_scores and len(ml_scores) > 0:
            avg_ml_risk = float(np.mean(ml_scores))
            high_ml_ratio = float(np.mean([1.0 if s >= 0.70 else 0.0 for s in ml_scores]))
        else:
            avg_ml_risk = 0.25
            high_ml_ratio = 0.1

        # 5. Composite Weighted Graph Risk Calculation
        # Combines network topology + behavioral velocity + ML risk
        raw_score = (
            0.30 * device_reuse_signal
            + 0.25 * token_reuse_signal
            + 0.15 * temporal_concentration
            + 0.15 * avg_ml_risk
            + 0.10 * high_ml_ratio
            + 0.05 * failure_ratio
        )

        # High burst multiplier: if both high velocity AND shared token/device exist
        if (device_reuse_signal > 0.4 or token_reuse_signal > 0.4) and temporal_concentration > 0.6:
            raw_score = min(1.0, raw_score * 1.35)

        # Normalization & Banding
        graph_risk_score = round(float(np.clip(raw_score, 0.02, 0.99)), 4)

        if graph_risk_score >= 0.85:
            risk_band = "CRITICAL"
        elif graph_risk_score >= 0.65:
            risk_band = "HIGH"
        elif graph_risk_score >= 0.35:
            risk_band = "MEDIUM"
        else:
            risk_band = "LOW"

        # Pattern Classification
        if token_reuse_signal >= 0.40:
            pattern = "shared_payment_token_ring"
        elif device_reuse_signal >= 0.40:
            pattern = "shared_device_ring"
        elif temporal_concentration >= 0.70 and cust_count >= 8:
            pattern = "velocity_attack"
        elif ip_velocity_signal >= 0.50:
            pattern = "shared_ip_ring"
        elif failure_ratio >= 0.35 and max(t.get("amount", 0) for t in transactions) > 25000:
            pattern = "testing_and_hit_attack"
        elif cust_count >= 10 and dev_count >= 2 and token_count >= 2:
            pattern = "distributed_multi_entity_ring"
        else:
            pattern = "benign_shared_infrastructure" if graph_risk_score < 0.40 else "suspicious_cluster"

        return {
            "graph_risk_score": graph_risk_score,
            "risk_band": risk_band,
            "pattern_type": pattern,
            "metrics": {
                "duration_hours": round(duration_hours, 2),
                "tx_per_hour": round(tx_per_hour, 2),
                "temporal_concentration": round(temporal_concentration, 3),
                "device_reuse_signal": round(device_reuse_signal, 3),
                "token_reuse_signal": round(token_reuse_signal, 3),
                "failure_ratio": round(failure_ratio, 3),
                "avg_ml_risk": round(avg_ml_risk, 3),
            },
        }
