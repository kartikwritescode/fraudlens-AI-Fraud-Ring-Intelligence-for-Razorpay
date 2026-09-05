"""
Temporal Ring Formation Analyzer for FraudLens
Reconstructs the chronological progression of how a coordinated fraud ring assembled.
"""

from typing import List, Dict, Any, Set
from datetime import datetime, timezone
from services.graph_engine.models import TimelineEvent


class TemporalRingAnalyzer:
    """Builds an audit-ready chronological timeline of cluster formation."""

    @staticmethod
    def reconstruct_timeline(
        transactions: List[Dict[str, Any]],
        max_events: int = 15,
    ) -> List[TimelineEvent]:
        """
        Takes cluster transactions, orders them temporally, and identifies key
        inflection points (first entity seen, infrastructure sharing, velocity spikes).
        """
        if not transactions:
            return []

        # Sort chronologically
        sorted_txs = sorted(transactions, key=lambda t: t.get("timestamp", ""))

        seen_customers: Set[str] = set()
        seen_devices: Dict[str, Set[str]] = {}  # dev -> set(customers)
        seen_tokens: Dict[str, Set[str]] = {}   # token -> set(customers)
        seen_ips: Dict[str, Set[str]] = {}      # ip -> set(customers)

        events: List[TimelineEvent] = []

        # 1. Initial event: Formation starts
        t0 = sorted_txs[0]
        c0 = t0.get("customer_id", "")
        d0 = t0.get("device_id", "")
        events.append(
            TimelineEvent(
                timestamp=t0.get("timestamp", ""),
                event_type="ENTITY_JOINED",
                title=f"First Cluster Activity Observed",
                description=f"Customer '{c0}' initiated first transaction of Rs. {t0.get('amount', 0):,.2f} via device '{d0}'.",
                severity="info",
                entities_involved=[c0, d0, t0.get("transaction_id", "")],
            )
        )
        seen_customers.add(c0)
        seen_devices.setdefault(d0, set()).add(c0)
        seen_tokens.setdefault(t0.get("payment_token_hash", ""), set()).add(c0)
        seen_ips.setdefault(t0.get("ip_hash", ""), set()).add(c0)

        # Iterate through subsequent transactions
        recent_window: List[float] = []

        for idx, t in enumerate(sorted_txs[1:], start=1):
            ts_str = t.get("timestamp", "")
            try:
                ts_epoch = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).timestamp()
            except Exception:
                ts_epoch = 0.0

            cust = t.get("customer_id", "")
            dev = t.get("device_id", "")
            tok = t.get("payment_token_hash", "")
            ip = t.get("ip_hash", "")
            tx_id = t.get("transaction_id", "")
            amt = t.get("amount", 0.0)

            # Check for new customer entering existing device
            if dev in seen_devices and cust not in seen_devices[dev]:
                seen_devices[dev].add(cust)
                dev_sharing_count = len(seen_devices[dev])
                if dev_sharing_count >= 2 and len(events) < max_events:
                    events.append(
                        TimelineEvent(
                            timestamp=ts_str,
                            event_type="DEVICE_LINKED",
                            title=f"Hardware Fingerprint Reused ({dev_sharing_count} accounts)",
                            description=f"Customer '{cust}' transacted using device '{dev}', previously used by {dev_sharing_count - 1} other account(s).",
                            severity="warning" if dev_sharing_count < 4 else "critical",
                            entities_involved=[cust, dev, tx_id],
                        )
                    )

            # Check for payment token reused across accounts
            if tok in seen_tokens and cust not in seen_tokens[tok]:
                seen_tokens[tok].add(cust)
                tok_sharing_count = len(seen_tokens[tok])
                if tok_sharing_count >= 2 and len(events) < max_events:
                    events.append(
                        TimelineEvent(
                            timestamp=ts_str,
                            event_type="TOKEN_SHARED",
                            title=f"Payment Token Shared Across Accounts",
                            description=f"Customer '{cust}' attempted transaction of Rs. {amt:,.2f} with token '{tok}' shared across {tok_sharing_count} accounts.",
                            severity="critical",
                            entities_involved=[cust, tok, tx_id],
                        )
                    )

            # Check for sudden large liquidation / testing-and-hit
            if amt > 25000 and len(events) < max_events:
                events.append(
                    TimelineEvent(
                        timestamp=ts_str,
                        event_type="LARGE_LIQUIDATION",
                        title=f"High-Value Cash-Out Spike (Rs. {amt:,.2f})",
                        description=f"Transaction '{tx_id}' attempted high-ticket amount on merchant '{t.get('merchant_id', '')}'.",
                        severity="warning",
                        entities_involved=[cust, tx_id],
                    )
                )

            # Track velocity
            if ts_epoch > 0:
                recent_window.append(ts_epoch)
                # Count in last 10 minutes (600s)
                window_10m = [s for s in recent_window if ts_epoch - s <= 600]
                if len(window_10m) >= 5 and len(events) < max_events:
                    if not any(e.event_type == "BURST_DETECTED" for e in events[-2:]):
                        events.append(
                            TimelineEvent(
                                timestamp=ts_str,
                                event_type="BURST_DETECTED",
                                title=f"High-Velocity Coordinated Burst",
                                description=f"Cluster generated {len(window_10m)} transactions within 10 minutes across multiple accounts.",
                                severity="critical",
                                entities_involved=[cust, tx_id],
                            )
                        )

            seen_customers.add(cust)
            seen_devices.setdefault(dev, set()).add(cust)
            seen_tokens.setdefault(tok, set()).add(cust)
            seen_ips.setdefault(ip, set()).add(cust)

        # Final escalation event
        t_last = sorted_txs[-1]
        events.append(
            TimelineEvent(
                timestamp=t_last.get("timestamp", ""),
                event_type="RISK_ESCALATED",
                title=f"Cluster Identified & Monitored",
                description=f"Total {len(seen_customers)} coordinated accounts, {len(seen_devices)} devices, and {len(seen_tokens)} payment tokens identified.",
                severity="critical" if len(events) >= 4 else "info",
                entities_involved=list(seen_customers)[:5],
            )
        )

        return events[:max_events]
