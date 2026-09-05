"""
Deterministic Financial Impact Calculator for FraudLens
Calculates exposure, false-positive friction costs, and expected loss matrices
using pure Python arithmetic without LLM hallucinations.
"""

from typing import Dict, Any, Optional
from services.agent.models import FinancialImpactResult


class FinancialImpactCalculator:
    """Calculates financial risk exposure and optimal action by cost minimization."""

    @staticmethod
    def calculate(
        amount: float,
        risk_score: float,
        cluster_volume: float = 0.0,
        cluster_risk_score: float = 0.0,
    ) -> FinancialImpactResult:
        attempted_fraud_value = round(max(0.0, float(amount)), 2)
        p_fraud = max(0.01, min(0.99, float(risk_score)))
        p_legit = 1.0 - p_fraud

        # Suspicious value and total exposure across cluster
        cluster_vol = max(0.0, float(cluster_volume))
        c_risk = max(0.0, min(1.0, float(cluster_risk_score)))
        suspicious_value = round(attempted_fraud_value + (cluster_vol * c_risk), 2)
        estimated_exposure = round(attempted_fraud_value + (cluster_vol * c_risk * 0.80), 2)

        # False positive friction cost (customer churn, merchant goodwill, dispute handling)
        false_positive_friction = round(0.025 * attempted_fraud_value + 350.0, 2)
        analyst_review_cost = 250.0  # Operational overhead per case

        # Expected Loss per Action:
        # 1. ALLOW: Direct loss if fraudulent
        exp_loss_allow = round(attempted_fraud_value * p_fraud + (cluster_vol * c_risk * 0.40), 2)

        # 2. MONITOR: Passive tracking, delayed chargeback exposure
        exp_loss_monitor = round(attempted_fraud_value * p_fraud * 0.85 + (cluster_vol * c_risk * 0.30), 2)

        # 3. STEP_UP: 2FA/Biometric challenge captures 85% of fraud with minor user drop-off
        exp_loss_step_up = round(
            attempted_fraud_value * p_fraud * 0.15 + false_positive_friction * p_legit * 0.25, 2
        )

        # 4. REVIEW: Manual investigation holds fund pending analyst decision
        exp_loss_review = round(
            analyst_review_cost + attempted_fraud_value * p_fraud * 0.05 + false_positive_friction * p_legit * 0.40, 2
        )

        # 5. HOLD: Strict authorization freeze, high false positive friction if legitimate
        exp_loss_hold = round(
            false_positive_friction * p_legit + attempted_fraud_value * 0.015, 2
        )

        loss_matrix = {
            "ALLOW": exp_loss_allow,
            "MONITOR": exp_loss_monitor,
            "STEP_UP": exp_loss_step_up,
            "REVIEW": exp_loss_review,
            "HOLD": exp_loss_hold,
        }

        # Select action with minimal expected loss
        optimal_action = min(loss_matrix, key=loss_matrix.get)

        return FinancialImpactResult(
            attempted_fraud_value=attempted_fraud_value,
            suspicious_value=suspicious_value,
            estimated_exposure=estimated_exposure,
            estimated_false_positive_cost=false_positive_friction,
            expected_loss_by_action=loss_matrix,
            optimal_action_by_loss=optimal_action,
        )
