"""
Synthetic Payment Universe Generator for FraudLens
Generates high-fidelity legitimate transactions and coordinated fraud rings.
"""

import argparse
import random
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

from services.simulator.models import (
    Transaction,
    Customer,
    Merchant,
    FraudRing,
    PaymentUniverse,
)
from services.simulator.scenarios import ScenarioGenerator

# Indian Merchant Categories & Names
INDIAN_MERCHANTS = [
    # E-Commerce & Retail
    ("Flipkart India", "ecommerce"),
    ("Amazon India", "ecommerce"),
    ("Myntra Fashion", "ecommerce"),
    ("Ajio Retail", "ecommerce"),
    ("Tata CLiQ", "ecommerce"),
    ("Nykaa Beauty", "ecommerce"),
    # Quick Commerce & Food
    ("Blinkit Express", "food"),
    ("Zepto Quick", "food"),
    ("Swiggy Instamart", "food"),
    ("Zomato Delivery", "food"),
    ("BigBasket Groceries", "food"),
    # Travel & Hospitality
    ("MakeMyTrip Flights", "travel"),
    ("IRCTC Railway", "travel"),
    ("Goibibo Hotels", "travel"),
    ("EaseMyTrip", "travel"),
    ("Yatra Online", "travel"),
    ("Uber India", "travel"),
    ("Ola Mobility", "travel"),
    # Electronics & Gadgets (Targeted for High-Ticket Liquidation)
    ("Croma Electronics", "electronics"),
    ("Reliance Digital", "electronics"),
    ("Vijay Sales", "electronics"),
    ("Apple Authorized Store", "electronics"),
    # Utilities & Telecom
    ("Jio Infocomm Prepaid", "utilities"),
    ("Airtel Payments", "utilities"),
    ("Adani Electricity", "utilities"),
    ("Tata Power Mumbai", "utilities"),
    ("BESCOM Bangalore", "utilities"),
    # Gaming & Entertainment
    ("Dream11 Gaming", "gaming"),
    ("BookMyShow", "gaming"),
    ("Nazara Games", "gaming"),
    ("SonyLIV Subscriptions", "gaming"),
    # Financial Services & Crypto
    ("CoinSwitch Kuber", "crypto"),
    ("WazirX Digital", "crypto"),
    ("Zerodha Broking", "utilities"),
    ("Groww Investment", "utilities"),
]


class SyntheticUniverseGenerator:
    """Orchestrates generation of legitimate payment stream and coordinated fraud rings."""

    def __init__(
        self,
        target_transactions: int = 50000,
        customer_count: int = 8000,
        merchant_count: int = 120,
        ring_count: int = 10,
        seed: int = 42,
    ):
        self.target_transactions = target_transactions
        self.customer_count = customer_count
        self.merchant_count = merchant_count
        self.ring_count = ring_count
        self.seed = seed

        # Deterministic RNGs
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        self.scenario_gen = ScenarioGenerator(self.rng)

    def _generate_merchants(self) -> List[Merchant]:
        """Generates merchant catalog."""
        merchants = []
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for i in range(self.merchant_count):
            tmpl_name, category = INDIAN_MERCHANTS[i % len(INDIAN_MERCHANTS)]
            suffix = f" #{i // len(INDIAN_MERCHANTS) + 1}" if i >= len(INDIAN_MERCHANTS) else ""
            m_id = f"mer_{i:04d}"
            merchants.append(
                Merchant(
                    id=m_id,
                    name=f"{tmpl_name}{suffix}",
                    category=category,
                    created_at=(base_date + timedelta(days=self.rng.randint(0, 180))).isoformat(),
                )
            )
        return merchants

    def _generate_legitimate_entities(
        self, merchants: List[Merchant]
    ) -> Tuple[List[Customer], Dict[str, Any]]:
        """
        Creates customer profiles with realistic infrastructure:
        - Legitimate shared corporate/campus IPs
        - Legitimate shared family devices
        - Preferred merchants and multiple payment instruments
        """
        customers = []
        base_date = datetime(2025, 6, 1, tzinfo=timezone.utc)

        # 1. Pool of legitimate shared IPs (e.g. University Wi-Fi, Tech Park NATs)
        shared_nat_ips = [f"ip_nat_campus_{idx}" for idx in range(15)]
        shared_corp_ips = [f"ip_nat_techpark_{idx}" for idx in range(25)]
        legit_shared_ips = shared_nat_ips + shared_corp_ips

        # 2. Pool of legitimate shared family devices (home desktop / iPad)
        shared_family_devices = [f"dev_family_ipad_{idx}" for idx in range(40)]

        for i in range(self.customer_count):
            c_id = f"cust_{i:06d}"
            created_at = base_date + timedelta(days=self.rng.randint(0, 120))

            # Preferred merchants (2-4 preferred shops)
            pref_count = self.rng.randint(2, 4)
            prefs = [m.id for m in self.rng.sample(merchants, min(pref_count, len(merchants)))]

            # Devices: 1-2 personal, 15% chance to also share a family device
            personal_dev = f"dev_mobile_{self.rng.randint(100000, 999999)}"
            cust_devices = [personal_dev]
            if self.rng.random() < 0.25:
                cust_devices.append(f"dev_laptop_{self.rng.randint(100000, 999999)}")
            if self.rng.random() < 0.12:
                cust_devices.append(self.rng.choice(shared_family_devices))

            # IPs: 1 primary home ISP, 35% chance to use campus/office shared NAT
            home_ip = f"ip_home_{self.rng.randint(10, 99)}_{self.rng.randint(100, 999)}"
            cust_ips = [home_ip]
            if self.rng.random() < 0.40:
                cust_ips.append(self.rng.choice(legit_shared_ips))

            # Payment instruments: UPI VPA, Credit/Debit card tokens
            token_count = self.rng.choices([1, 2, 3], weights=[0.55, 0.35, 0.10])[0]
            tokens = [f"tok_card_{self.rng.randint(100000, 999999)}" for _ in range(token_count)]

            cust = Customer(
                id=c_id,
                country="IND",
                created_at=created_at.isoformat(),
                first_seen_at=created_at.isoformat(),
                last_seen_at=(created_at + timedelta(days=90)).isoformat(),
                email_hash=f"em_user_{self.rng.randint(1000000, 9999999)}",
                phone_hash=f"ph_user_{self.rng.randint(1000000, 9999999)}",
                devices=cust_devices,
                ips=cust_ips,
                payment_tokens=tokens,
                preferred_merchants=prefs,
            )
            customers.append(cust)

        shared_infra_meta = {
            "legit_shared_ips": legit_shared_ips,
            "legit_shared_devices": shared_family_devices,
        }
        return customers, shared_infra_meta

    def _sample_legitimate_amount(self, category: str) -> float:
        """Draws realistic Indian transaction amounts with log-normal tails by category."""
        if category == "food":
            # Swiggy/Zomato/Blinkit: ₹150 - ₹1,200
            amt = self.np_rng.lognormal(mean=5.8, sigma=0.45)
            amt = np.clip(amt, 60.0, 3500.0)
        elif category == "utilities":
            # Bills / Recharges: ₹200 - ₹3,500
            amt = self.np_rng.lognormal(mean=6.5, sigma=0.55)
            amt = np.clip(amt, 100.0, 12000.0)
        elif category == "ecommerce":
            # Retail/Fashion: ₹600 - ₹8,000
            amt = self.np_rng.lognormal(mean=7.2, sigma=0.7)
            amt = np.clip(amt, 250.0, 35000.0)
        elif category == "electronics":
            # High-ticket gadgets: ₹3,000 - ₹85,000
            amt = self.np_rng.lognormal(mean=8.8, sigma=0.8)
            amt = np.clip(amt, 1500.0, 95000.0)
        elif category == "travel":
            # Flights / Hotels: ₹1,500 - ₹35,000
            amt = self.np_rng.lognormal(mean=8.0, sigma=0.65)
            amt = np.clip(amt, 500.0, 65000.0)
        elif category == "gaming":
            # Micro-purchases / Vouchers: ₹50 - ₹2,500
            amt = self.np_rng.lognormal(mean=5.2, sigma=0.6)
            amt = np.clip(amt, 49.0, 10000.0)
        else:
            amt = self.np_rng.lognormal(mean=6.8, sigma=0.6)
            amt = np.clip(amt, 100.0, 50000.0)

        # Standard Indian pricing rounding (.00 or .99)
        if self.rng.random() < 0.6:
            return float(round(amt))
        return float(round(amt, 2))

    def _sample_payment_method(self) -> str:
        """Indian payment rails distribution: UPI dominates, followed by Cards and Netbanking."""
        return self.rng.choices(["upi", "card", "netbanking", "wallet"], weights=[0.68, 0.22, 0.08, 0.02])[0]

    def _generate_timestamp(self, start_date: datetime, end_date: datetime) -> datetime:
        """Generates realistic timestamp honoring diurnal hour distribution."""
        total_seconds = int((end_date - start_date).total_seconds())
        random_offset = self.rng.randint(0, total_seconds)
        dt = start_date + timedelta(seconds=random_offset)

        # Diurnal distribution: low probability 2 AM-6 AM, peaks at 13-15h & 20-22h
        hour_weights = [
            0.01, 0.005, 0.002, 0.002, 0.005, 0.01, # 00-05
            0.02, 0.035, 0.05, 0.065, 0.07, 0.075,   # 06-11
            0.085, 0.09, 0.07, 0.06, 0.065, 0.075,   # 12-17
            0.085, 0.095, 0.09, 0.065, 0.04, 0.025   # 18-23
        ]
        sampled_hour = self.rng.choices(range(24), weights=hour_weights)[0]
        return dt.replace(hour=sampled_hour, minute=self.rng.randint(0, 59), second=self.rng.randint(0, 59))

    def generate_universe(self) -> PaymentUniverse:
        """Generates the full payment universe including legitimate streams and coordinated rings."""
        merchants = self._generate_merchants()
        merchant_dict = {m.id: m for m in merchants}
        customers, shared_meta = self._generate_legitimate_entities(merchants)

        start_date = datetime(2025, 9, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2025, 9, 30, 23, 59, 59, tzinfo=timezone.utc)

        # 1. Generate Coordinated Fraud Rings
        rings: List[FraudRing] = []
        fraud_transactions: List[Transaction] = []
        ring_customers: List[Customer] = []

        scenario_methods = [
            self.scenario_gen.generate_shared_device_ring,
            self.scenario_gen.generate_shared_ip_ring,
            self.scenario_gen.generate_shared_token_ring,
            self.scenario_gen.generate_account_takeover,
            self.scenario_gen.generate_velocity_attack,
            self.scenario_gen.generate_testing_and_hit_attack,
            self.scenario_gen.generate_distributed_mesh_ring,
        ]

        for r_idx in range(self.ring_count):
            ring_id = f"ring_{r_idx + 1:03d}"
            scenario_func = scenario_methods[r_idx % len(scenario_methods)]
            # Spread ring attacks over the month
            ring_base_time = start_date + timedelta(days=self.rng.randint(2, 28), hours=self.rng.randint(8, 22))

            ring, r_custs, r_txs = scenario_func(ring_id, merchants, ring_base_time)
            rings.append(ring)
            ring_customers.extend(r_custs)
            fraud_transactions.extend(r_txs)

        # 2. Generate Legitimate Transactions
        legit_tx_needed = max(100, self.target_transactions - len(fraud_transactions))
        legit_transactions: List[Transaction] = []

        # Customer transaction frequency follows Pareto distribution (power law)
        # 20% of customers make 70% of transactions
        weights = self.np_rng.pareto(a=1.8, size=len(customers)) + 0.1
        weights /= weights.sum()

        cust_indices = self.np_rng.choice(len(customers), size=legit_tx_needed, p=weights)

        for idx, c_idx in enumerate(cust_indices):
            cust = customers[c_idx]
            tx_id = f"tx_legit_{idx:07d}"
            tx_time = self._generate_timestamp(start_date, end_date)

            # Choose merchant (80% chance to use one of preferred merchants)
            if cust.preferred_merchants and self.rng.random() < 0.80:
                m_id = self.rng.choice(cust.preferred_merchants)
            else:
                m_id = self.rng.choice(merchants).id
            merchant = merchant_dict[m_id]

            # Infrastructure choice from customer's pool
            dev_id = self.rng.choice(cust.devices)
            ip_h = self.rng.choice(cust.ips)
            pay_method = self._sample_payment_method()
            token_h = self.rng.choice(cust.payment_tokens) if pay_method == "card" else f"tok_upi_{cust.id[-4:]}"

            # Amount by merchant category
            amount = self._sample_legitimate_amount(merchant.category)

            # 96% success rate for legitimate transactions (normal failed cards/insufficient funds)
            status = "captured" if self.rng.random() < 0.96 else "failed"

            tx = Transaction(
                transaction_id=tx_id,
                timestamp=tx_time.isoformat(),
                merchant_id=merchant.id,
                customer_id=cust.id,
                amount=amount,
                currency="INR",
                payment_method=pay_method,
                status=status,
                device_id=dev_id,
                ip_hash=ip_h,
                email_hash=cust.email_hash,
                phone_hash=cust.phone_hash,
                payment_token_hash=token_h,
                billing_country="IND",
                shipping_country="IND",
                order_id=f"ord_{tx_id}",
                is_fraud=False,
                fraud_type=None,
                ring_id=None,
            )
            legit_transactions.append(tx)

        # Merge and sort all transactions chronologically
        all_transactions = legit_transactions + fraud_transactions
        all_transactions.sort(key=lambda t: t.timestamp)

        # Consolidate customers
        all_customers = customers + ring_customers

        # Compute summary statistics
        fraud_tx_count = sum(1 for t in all_transactions if t.is_fraud)
        total_volume = sum(t.amount for t in all_transactions)
        fraud_volume = sum(t.amount for t in all_transactions if t.is_fraud)

        stats = {
            "total_transactions": len(all_transactions),
            "legitimate_transactions": len(all_transactions) - fraud_tx_count,
            "fraud_transactions": fraud_tx_count,
            "fraud_rate_percentage": round((fraud_tx_count / len(all_transactions)) * 100, 2),
            "total_volume_inr": round(total_volume, 2),
            "fraud_volume_inr": round(fraud_volume, 2),
            "total_customers": len(all_customers),
            "total_merchants": len(merchants),
            "total_fraud_rings": len(rings),
            "seed": self.seed,
            "rings_detail": [
                {
                    "ring_id": r.id,
                    "name": r.name,
                    "pattern": r.pattern_type,
                    "members": r.member_count,
                    "tx_count": len(r.transaction_ids),
                    "attempted_inr": r.attempted_amount,
                }
                for r in rings
            ],
        }

        return PaymentUniverse(
            customers=all_customers,
            merchants=merchants,
            transactions=all_transactions,
            fraud_rings=rings,
            stats=stats,
        )


def main():
    parser = argparse.ArgumentParser(description="Generate FraudLens Synthetic Payment Universe")
    parser.add_argument("--transactions", type=int, default=50000, help="Target transaction count")
    parser.add_argument("--customers", type=int, default=8000, help="Customer count")
    parser.add_argument("--merchants", type=int, default=120, help="Merchant count")
    parser.add_argument("--rings", type=int, default=10, help="Number of coordinated fraud rings")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--output", type=str, default="", help="Optional JSON output file path")
    parser.add_argument("--stats-only", action="store_true", help="Print stats summary without dumping full data")

    args = parser.parse_args()

    print(f"[*] Initializing FraudLens Synthetic Payment Generator...")
    print(f"    Target Transactions: {args.transactions}")
    print(f"    Target Customers:    {args.customers}")
    print(f"    Target Merchants:    {args.merchants}")
    print(f"    Fraud Rings:         {args.rings}")
    print(f"    Deterministic Seed:  {args.seed}")

    gen = SyntheticUniverseGenerator(
        target_transactions=args.transactions,
        customer_count=args.customers,
        merchant_count=args.merchants,
        ring_count=args.rings,
        seed=args.seed,
    )

    universe = gen.generate_universe()
    stats = universe.stats

    print("\n========================================================")
    print("  FRAUDLENS SYNTHETIC UNIVERSE GENERATION COMPLETED     ")
    print("========================================================")
    print(f"Total Transactions:      {stats['total_transactions']:,}")
    print(f"Legitimate Transactions: {stats['legitimate_transactions']:,}")
    print(f"Fraud Transactions:      {stats['fraud_transactions']:,} ({stats['fraud_rate_percentage']}%)")
    print(f"Total Customers:         {stats['total_customers']:,}")
    print(f"Total Merchants:         {stats['total_merchants']:,}")
    print(f"Total Fraud Rings:       {stats['total_fraud_rings']}")
    print(f"Total Volume Attempted:  Rs. {stats['total_volume_inr']:,.2f}")
    print(f"Fraud Volume Attempted:  Rs. {stats['fraud_volume_inr']:,.2f}")
    print("--------------------------------------------------------")
    print("Injected Fraud Ring Topologies:")
    for r in stats["rings_detail"]:
        print(f"  - [{r['ring_id']}] {r['pattern']} | Members: {r['members']} | Txs: {r['tx_count']} | Rs. {r['attempted_inr']:,.2f}")
    print("========================================================\n")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"[*] Saving generated universe to {out_path}...")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(universe.model_dump_json(indent=2))
        print(f"[OK] Universe saved successfully.")


if __name__ == "__main__":
    main()
