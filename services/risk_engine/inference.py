"""
ML Risk Inference & SHAP Explainability Engine
Loads pre-trained XGBoost artifact and TreeSHAP explainer to provide real-time
risk scores, risk bands, and top explainable reason codes.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from pydantic import BaseModel, Field

from ml.features.engineer import (
    StreamingFeatureExtractor,
    extract_features_dataset,
    FEATURE_NAMES,
)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_ARTIFACT_PATH = ROOT_DIR / "ml" / "artifacts" / "risk_model_v1.joblib"
DEFAULT_DATASET_PATH = ROOT_DIR / "data" / "transactions_50k.json"


class RiskAssessmentResult(BaseModel):
    transaction_id: str
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated risk probability [0.0 - 1.0]")
    risk_band: str = Field(..., description="Decision band: LOW, MEDIUM, HIGH, CRITICAL")
    model_version: str = "v1.0.0-xgb"
    reason_codes: List[str] = Field(default_factory=list, description="Human-readable top SHAP risk drivers")
    feature_summary: Dict[str, float] = Field(default_factory=dict)
    top_shap_contributions: Dict[str, float] = Field(default_factory=dict)


class RiskScorer:
    """Singleton model scorer with pre-loaded weights and TreeSHAP explainer."""

    _instance: Optional["RiskScorer"] = None

    def __init__(self, artifact_path: Optional[Path] = None, data_path: Optional[Path] = None):
        path = artifact_path or DEFAULT_ARTIFACT_PATH
        if not path.exists():
            raise FileNotFoundError(f"ML model artifact not found at {path}. Run python -m ml.training.train first.")

        artifact = joblib.load(path)
        self.model = artifact["model"]
        self.explainer = artifact["explainer"]
        self.feature_names = artifact["feature_names"]
        self.model_version = artifact.get("model_version", "v1.0.0-xgb")
        self.thresholds = artifact.get("thresholds", {"low": 0.39, "medium": 0.69, "high": 0.89})
        self.metrics = artifact.get("metrics", {})

        # Default streaming feature extractor state
        self.extractor = StreamingFeatureExtractor()

        # Indexed transaction repository for instantaneous /transactions/{id}/risk lookups
        self.tx_lookup: Dict[str, Dict[str, Any]] = {}
        self.tx_feature_cache: Dict[str, Dict[str, float]] = {}
        self._assessment_cache: Dict[str, RiskAssessmentResult] = {}

        data_file = data_path or DEFAULT_DATASET_PATH
        if data_file.exists():
            self._load_dataset_index(data_file)

    def _load_dataset_index(self, data_path: Path):
        """Indexes transactions and pre-calculates features for indexed lookups."""
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            txs = data.get("transactions", [])
            for t in txs:
                self.tx_lookup[t["transaction_id"]] = t

            # Chronologically populate feature cache
            df_feat, labels, sorted_txs = extract_features_dataset(txs)
            for idx, t in enumerate(sorted_txs):
                self.tx_feature_cache[t["transaction_id"]] = df_feat.iloc[idx].to_dict()

            print(f"[*] RiskScorer indexed {len(self.tx_lookup):,} transactions & pre-cached features from {data_path.name}.")
        except Exception as e:
            print(f"[!] Warning: Could not pre-index dataset: {e}")

    @classmethod
    def get_instance(cls, artifact_path: Optional[Path] = None) -> "RiskScorer":
        if cls._instance is None:
            cls._instance = cls(artifact_path)
        return cls._instance

    def _determine_risk_band(self, score: float) -> str:
        if score <= self.thresholds["low"]:
            return "LOW"
        elif score <= self.thresholds["medium"]:
            return "MEDIUM"
        elif score <= self.thresholds["high"]:
            return "HIGH"
        return "CRITICAL"

    def _generate_reason_codes(
        self,
        shap_values: np.ndarray,
        feature_values: Dict[str, float],
        top_k: int = 4,
    ) -> List[str]:
        """Translates top positive SHAP drivers into clear, analyst-friendly reason codes."""
        shap_pairs = list(zip(self.feature_names, shap_values))
        # Filter to only positive contributors (features pushing risk UP)
        positive_drivers = [p for p in shap_pairs if p[1] > 0.05]
        positive_drivers.sort(key=lambda x: x[1], reverse=True)

        reason_codes = []
        for feat, shap_val in positive_drivers[:top_k]:
            val = feature_values.get(feat, 0.0)

            if feat == "device_reuse_count" and val > 1:
                reason_codes.append(f"Hardware device fingerprint shared across {int(val)} distinct customer accounts")
            elif feat == "ip_reuse_count" and val > 1:
                reason_codes.append(f"IP address/subnet reused across {int(val)} customer identities")
            elif feat == "payment_token_reuse_count" and val > 1:
                reason_codes.append(f"Payment instrument token reused across {int(val)} customer accounts")
            elif feat == "cust_tx_count_5m" and val >= 2:
                reason_codes.append(f"Abnormal customer velocity ({int(val)} attempts in past 5 minutes)")
            elif feat == "cust_tx_count_1h" and val >= 3:
                reason_codes.append(f"High transaction frequency ({int(val)} transactions in past 1 hour)")
            elif feat == "amount_to_customer_median" and val >= 2.5:
                reason_codes.append(f"Transaction amount is {val:.1f}x higher than customer's historical median")
            elif feat == "failed_payment_ratio" and val >= 0.40:
                reason_codes.append(f"High historical failure rate ({val*100:.0f}%) indicates card-testing probing")
            elif feat == "is_new_device" and val == 1.0:
                reason_codes.append("First time transaction originating from previously unseen device")
            elif feat == "is_new_ip" and val == 1.0:
                reason_codes.append("First time transaction originating from newly seen IP address")
            elif feat == "account_age_days" and val < 2.0:
                reason_codes.append("Newly registered customer account executing immediate transactions")
            elif feat == "unusual_transaction_hour" and val == 1.0:
                reason_codes.append("Transaction occurred during high-risk unusual night hours (01:00-05:00)")
            elif feat == "geographic_mismatch" and val == 1.0:
                reason_codes.append("Cross-border mismatch between billing and shipping country")
            elif feat == "has_previous_suspicious_activity" and val == 1.0:
                reason_codes.append("Customer account has previous failed or flagged activity on record")
            elif feat == "merchant_tx_count_1h" and val > 20:
                reason_codes.append(f"Target merchant experiencing abnormal burst velocity ({int(val)} tx/hr)")
            elif feat == "amount" and val > 25000:
                reason_codes.append(f"Unusually large transaction amount (Rs. {val:,.2f})")
            else:
                reason_codes.append(f"Elevated risk signal on feature '{feat}' (+{shap_val:.2f} impact)")

        if not reason_codes:
            reason_codes.append("Baseline behavioral signals within expected risk variance")

        return reason_codes

    def assess_transaction(
        self,
        tx: Dict[str, Any],
        custom_features: Optional[Dict[str, float]] = None,
        update_state: bool = False,
    ) -> RiskAssessmentResult:
        """Runs full ML risk assessment and SHAP reason code generation on a transaction."""
        tx_id = tx.get("transaction_id", "tx_unknown")

        # Return cached evaluation instantly if standard lookup
        if not update_state and custom_features is None and tx_id in self._assessment_cache:
            return self._assessment_cache[tx_id]

        if custom_features is not None:
            features = custom_features
        elif tx_id in self.tx_feature_cache:
            features = self.tx_feature_cache[tx_id]
        else:
            features = self.extractor.extract_features_for_transaction(tx, update_state=update_state)

        # Build feature DataFrame
        df_feat = pd.DataFrame([[features[k] for k in self.feature_names]], columns=self.feature_names)

        # Predict probability
        prob = float(self.model.predict_proba(df_feat)[0, 1])
        risk_score = round(prob, 4)
        risk_band = self._determine_risk_band(risk_score)

        # Compute SHAP values
        shap_vals = self.explainer.shap_values(df_feat)
        if isinstance(shap_vals, list):
            sample_shap = shap_vals[1][0]
        else:
            sample_shap = shap_vals[0]

        reason_codes = self._generate_reason_codes(sample_shap, features)

        # Top SHAP contributions
        top_shap = {}
        for feat, s_val in sorted(zip(self.feature_names, sample_shap), key=lambda x: abs(x[1]), reverse=True)[:5]:
            top_shap[feat] = round(float(s_val), 4)

        result = RiskAssessmentResult(
            transaction_id=tx_id,
            risk_score=risk_score,
            risk_band=risk_band,
            model_version=self.model_version,
            reason_codes=reason_codes,
            feature_summary={k: round(v, 2) for k, v in features.items()},
            top_shap_contributions=top_shap,
        )

        if not update_state and custom_features is None and tx_id:
            self._assessment_cache[tx_id] = result

        return result

    def assess_by_transaction_id(self, tx_id: str) -> Optional[RiskAssessmentResult]:
        """Look up indexed transaction and evaluate its risk."""
        if tx_id in self._assessment_cache:
            return self._assessment_cache[tx_id]
        tx = self.tx_lookup.get(tx_id)
        if not tx:
            return None
        return self.assess_transaction(tx)

    def prewarm_cache(self, limit: int = 500):
        """Pre-scores candidate transactions and caches their SHAP results for instant response."""
        count = 0
        for tid, t in self.tx_lookup.items():
            if t.get("is_fraud"):
                self.assess_transaction(t)
                count += 1
                if count >= 200:
                    break

        for tid, t in self.tx_lookup.items():
            if not t.get("is_fraud"):
                self.assess_transaction(t)
                count += 1
                if count >= limit:
                    break
        print(f"[*] RiskScorer pre-warmed {len(self._assessment_cache)} transaction risk assessments & TreeSHAP explainers.")

