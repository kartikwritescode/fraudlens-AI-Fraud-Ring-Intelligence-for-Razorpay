"""
Feature Engineering Pipeline for FraudLens
Computes rolling behavioral, velocity, and infrastructure reuse features
strictly in chronological order to eliminate target leakage.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from collections import defaultdict, deque
import bisect
import numpy as np
import pandas as pd


FEATURE_NAMES = [
    "amount",
    "amount_to_customer_median",
    "amount_deviation",
    "cust_tx_count_5m",
    "cust_tx_count_1h",
    "cust_tx_count_24h",
    "merchant_tx_count_1h",
    "device_reuse_count",
    "ip_reuse_count",
    "payment_token_reuse_count",
    "account_age_days",
    "failed_payment_ratio",
    "geographic_mismatch",
    "unusual_transaction_hour",
    "is_new_device",
    "is_new_ip",
    "has_previous_suspicious_activity",
    "ip_tx_count_1h",
    "ip_distinct_cust_1h",
    "ip_failed_count_1h",
    "dev_distinct_cust_1h",
    "tok_distinct_cust_1h",
    "is_card",
    "is_netbanking",
    "is_high_ticket",
]


class StreamingFeatureExtractor:
    """
    Stateful retrospective feature calculator for chronological transaction streams.
    Maintains historical customer, merchant, and infrastructure states without target leakage.
    """

    def __init__(self):
        # Customer historical state:
        # customer_id -> list of (timestamp_epoch, amount, is_failed)
        self.cust_history: Dict[str, List[Tuple[float, float, bool]]] = defaultdict(list)
        # customer_id -> set of known devices, IPs
        self.cust_known_devices: Dict[str, set] = defaultdict(set)
        self.cust_known_ips: Dict[str, set] = defaultdict(set)
        # customer_id -> first_seen_epoch
        self.cust_first_seen: Dict[str, float] = {}

        # Merchant state: merchant_id -> deque of timestamps
        self.merchant_history: Dict[str, deque] = defaultdict(deque)

        # Entity reuse state: entity -> set of customer_ids seen
        self.device_customers: Dict[str, set] = defaultdict(set)
        self.ip_customers: Dict[str, set] = defaultdict(set)
        self.token_customers: Dict[str, set] = defaultdict(set)

        # Rolling 1-hour entity transaction history for velocity bursts
        # ip_hash -> deque of (ts, cust_id, is_failed)
        self.ip_1h_dq: Dict[str, deque] = defaultdict(deque)
        # dev_id -> deque of (ts, cust_id)
        self.dev_1h_dq: Dict[str, deque] = defaultdict(deque)
        # token_hash -> deque of (ts, cust_id)
        self.tok_1h_dq: Dict[str, deque] = defaultdict(deque)

    def extract_features_for_transaction(
        self, tx: Dict[str, Any], update_state: bool = True
    ) -> Dict[str, float]:
        """
        Extracts features for a single transaction based strictly on prior history.
        Optionally updates state afterwards.
        """
        amount = float(tx.get("amount", 0.0))
        ts_str = tx.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
        except Exception:
            ts = datetime.now(timezone.utc).timestamp()

        cust_id = tx.get("customer_id", "")
        mer_id = tx.get("merchant_id", "")
        dev_id = tx.get("device_id", "")
        ip_hash = tx.get("ip_hash", "")
        token_hash = tx.get("payment_token_hash", "")
        billing_country = tx.get("billing_country", "IND")
        shipping_country = tx.get("shipping_country", "IND")
        status = tx.get("status", "captured")
        is_failed = status in ["failed", "blocked"]

        # 1. Customer history lookups (prior transactions only)
        prior_txs = self.cust_history.get(cust_id, [])

        if prior_txs:
            amounts = [item[1] for item in prior_txs]
            cust_median = float(np.median(amounts))
            failed_count = sum(1 for item in prior_txs if item[2])
            failed_ratio = failed_count / len(prior_txs)
            has_prev_suspicious = 1.0 if failed_count > 0 else 0.0

            # Velocity in past 5m (300s), 1h (3600s), 24h (86400s)
            c_5m = sum(1 for item in prior_txs if ts - item[0] <= 300)
            c_1h = sum(1 for item in prior_txs if ts - item[0] <= 3600)
            c_24h = sum(1 for item in prior_txs if ts - item[0] <= 86400)
        else:
            cust_median = amount
            failed_ratio = 0.0
            has_prev_suspicious = 0.0
            c_5m = 0
            c_1h = 0
            c_24h = 0

        # Amount ratios
        amount_to_median = (amount / cust_median) if cust_median > 0 else 1.0
        amount_deviation = abs(amount - cust_median)

        # 2. Merchant velocity in past 1h
        mer_dq = self.merchant_history[mer_id]
        # Clean older than 3600s
        while mer_dq and (ts - mer_dq[0] > 3600):
            mer_dq.popleft()
        merchant_velocity_1h = len(mer_dq)

        # 3. Infrastructure reuse counts (distinct customers previously sharing this entity)
        dev_reuse = len(self.device_customers.get(dev_id, set()))
        ip_reuse = len(self.ip_customers.get(ip_hash, set()))
        tok_reuse = len(self.token_customers.get(token_hash, set()))

        # 4. First-time seen / new infrastructure flags
        is_new_dev = 1.0 if dev_id not in self.cust_known_devices[cust_id] else 0.0
        is_new_ip = 1.0 if ip_hash not in self.cust_known_ips[cust_id] else 0.0

        # 5. Account age
        first_seen = self.cust_first_seen.get(cust_id, ts)
        account_age_days = max(0.0, (ts - first_seen) / 86400.0)

        # 6. Country mismatch
        geo_mismatch = 1.0 if billing_country != shipping_country else 0.0

        # 7. Unusual transaction hour (01:00 to 05:59 local UTC+5:30 or UTC)
        tx_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        hour = tx_dt.hour
        unusual_hour = 1.0 if (1 <= hour <= 5) else 0.0

        # 8. Rolling 1-hour entity velocity (burst syndicate detection)
        # IP rolling 1h
        dq_ip = self.ip_1h_dq[ip_hash]
        while dq_ip and (ts - dq_ip[0][0] > 3600):
            dq_ip.popleft()
        ip_tx_1h = len(dq_ip)
        ip_custs_1h = len(set(x[1] for x in dq_ip))
        ip_fails_1h = sum(1 for x in dq_ip if x[2])

        # Device rolling 1h
        dq_dev = self.dev_1h_dq[dev_id]
        while dq_dev and (ts - dq_dev[0][0] > 3600):
            dq_dev.popleft()
        dev_custs_1h = len(set(x[1] for x in dq_dev))

        # Token rolling 1h
        dq_tok = self.tok_1h_dq[token_hash]
        while dq_tok and (ts - dq_tok[0][0] > 3600):
            dq_tok.popleft()
        tok_custs_1h = len(set(x[1] for x in dq_tok))

        # 9. Payment method and ticket size flags
        method = tx.get("payment_method", "upi")
        is_card = 1.0 if method == "card" else 0.0
        is_netbanking = 1.0 if method == "netbanking" else 0.0
        is_high_ticket = 1.0 if amount >= 4999.0 else 0.0

        features = {
            "amount": amount,
            "amount_to_customer_median": amount_to_median,
            "amount_deviation": amount_deviation,
            "cust_tx_count_5m": float(c_5m),
            "cust_tx_count_1h": float(c_1h),
            "cust_tx_count_24h": float(c_24h),
            "merchant_tx_count_1h": float(merchant_velocity_1h),
            "device_reuse_count": float(dev_reuse),
            "ip_reuse_count": float(ip_reuse),
            "payment_token_reuse_count": float(tok_reuse),
            "account_age_days": float(account_age_days),
            "failed_payment_ratio": float(failed_ratio),
            "geographic_mismatch": float(geo_mismatch),
            "unusual_transaction_hour": float(unusual_hour),
            "is_new_device": float(is_new_dev),
            "is_new_ip": float(is_new_ip),
            "has_previous_suspicious_activity": float(has_prev_suspicious),
            "ip_tx_count_1h": float(ip_tx_1h),
            "ip_distinct_cust_1h": float(ip_custs_1h),
            "ip_failed_count_1h": float(ip_fails_1h),
            "dev_distinct_cust_1h": float(dev_custs_1h),
            "tok_distinct_cust_1h": float(tok_custs_1h),
            "is_card": is_card,
            "is_netbanking": is_netbanking,
            "is_high_ticket": is_high_ticket,
        }

        # Update state if requested
        if update_state:
            self.cust_history[cust_id].append((ts, amount, is_failed))
            self.cust_known_devices[cust_id].add(dev_id)
            self.cust_known_ips[cust_id].add(ip_hash)
            if cust_id not in self.cust_first_seen:
                self.cust_first_seen[cust_id] = ts

            self.merchant_history[mer_id].append(ts)
            self.device_customers[dev_id].add(cust_id)
            self.ip_customers[ip_hash].add(cust_id)
            self.token_customers[token_hash].add(cust_id)

            self.ip_1h_dq[ip_hash].append((ts, cust_id, is_failed))
            self.dev_1h_dq[dev_id].append((ts, cust_id))
            self.tok_1h_dq[token_hash].append((ts, cust_id))

        return features


def extract_features_dataset(
    transactions: List[Dict[str, Any]]
) -> Tuple[pd.DataFrame, pd.Series, List[Dict[str, Any]]]:
    """
    Extracts features for an entire chronological list of transactions.
    Returns: (features_df, labels_series, enriched_transactions)
    """
    # Ensure chronological order
    sorted_txs = sorted(transactions, key=lambda t: t["timestamp"])

    extractor = StreamingFeatureExtractor()
    feature_rows = []
    labels = []

    for tx in sorted_txs:
        feat = extractor.extract_features_for_transaction(tx, update_state=True)
        feature_rows.append(feat)
        labels.append(1 if tx.get("is_fraud", False) else 0)

    df_features = pd.DataFrame(feature_rows, columns=FEATURE_NAMES)
    labels_series = pd.Series(labels, name="is_fraud")

    return df_features, labels_series, sorted_txs
