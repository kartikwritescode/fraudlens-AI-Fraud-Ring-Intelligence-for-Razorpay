"""
Fraud Scenario Generators for FraudLens
Generates 7 distinct coordinated fraud ring patterns with realistic overlapping signals.
"""

import random
from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta
from services.simulator.models import Transaction, FraudRing, Customer, Merchant


class ScenarioGenerator:
    """Generates distinct coordinated fraud ring topologies."""

    def __init__(self, rng: random.Random):
        self.rng = rng

    def generate_shared_device_ring(
        self,
        ring_id: str,
        merchants: List[Merchant],
        base_time: datetime,
        account_count: int = 12,
    ) -> Tuple[FraudRing, List[Customer], List[Transaction]]:
        """
        Scenario 1: Shared-Device Ring
        Multiple synthetic customer identities operating through 1 or 2 rooted devices.
        Rotating payment tokens, high temporal burst.
        """
        device_id = f"dev_rooted_{self.rng.randint(1000, 9999)}"
        backup_device = f"dev_emu_{self.rng.randint(1000, 9999)}"
        devices = [device_id, backup_device]

        ring = FraudRing(
            id=ring_id,
            name=f"Sybil Device Cluster #{ring_id[-4:]}",
            pattern_type="shared_device_ring",
            risk_score=0.94,
            risk_band="CRITICAL",
            status="DISCOVERED",
            created_at=base_time.isoformat(),
            updated_at=(base_time + timedelta(hours=4)).isoformat(),
            description="Multiple newly created accounts sharing rooted Android/emulator hardware fingerprint.",
            device_ids=devices,
        )

        customers = []
        transactions = []
        total_attempted = 0.0

        for i in range(account_count):
            cust_id = f"cust_sdr_{ring_id[-4:]}_{i:03d}"
            email_hash = f"em_syn_{self.rng.randint(100000, 999999)}"
            phone_hash = f"ph_syn_{self.rng.randint(100000, 999999)}"
            token_hash = f"tok_vcard_{self.rng.randint(100000, 999999)}"
            ip_hash = f"ip_sub_{self.rng.randint(10, 99)}_{self.rng.randint(100, 999)}"

            customer = Customer(
                id=cust_id,
                created_at=(base_time - timedelta(days=self.rng.randint(1, 5))).isoformat(),
                first_seen_at=base_time.isoformat(),
                last_seen_at=(base_time + timedelta(hours=3)).isoformat(),
                email_hash=email_hash,
                phone_hash=phone_hash,
                devices=devices,
                ips=[ip_hash],
                payment_tokens=[token_hash],
            )
            customers.append(customer)
            ring.customer_ids.append(cust_id)
            ring.payment_token_hashes.append(token_hash)
            ring.ip_hashes.append(ip_hash)

            # 2-4 transactions per account within 3 hours
            tx_count = self.rng.randint(2, 4)
            for j in range(tx_count):
                tx_time = base_time + timedelta(minutes=self.rng.randint(5, 180))
                # Realistic INR e-commerce / gaming voucher amounts
                amount = round(self.rng.choice([1999.0, 2499.0, 4999.0, 7499.0, 9999.0]) + self.rng.uniform(0.1, 9.9), 2)
                total_attempted += amount
                tx_id = f"tx_sdr_{ring_id[-4:]}_{i:02d}_{j:02d}"
                merchant = self.rng.choice(merchants)
                dev = device_id if self.rng.random() < 0.85 else backup_device

                # 70% success, 30% failed/blocked
                status = "captured" if self.rng.random() < 0.70 else "failed"

                tx = Transaction(
                    transaction_id=tx_id,
                    timestamp=tx_time.isoformat(),
                    merchant_id=merchant.id,
                    customer_id=cust_id,
                    amount=amount,
                    currency="INR",
                    payment_method=self.rng.choice(["upi", "card"]),
                    status=status,
                    device_id=dev,
                    ip_hash=ip_hash,
                    email_hash=email_hash,
                    phone_hash=phone_hash,
                    payment_token_hash=token_hash,
                    billing_country="IND",
                    shipping_country="IND",
                    order_id=f"ord_{tx_id}",
                    is_fraud=True,
                    fraud_type="shared_device_ring",
                    ring_id=ring_id,
                )
                transactions.append(tx)
                ring.transaction_ids.append(tx_id)

        ring.member_count = len(customers)
        ring.attempted_amount = round(total_attempted, 2)
        ring.estimated_loss = round(total_attempted * 0.70, 2)
        return ring, customers, transactions

    def generate_shared_ip_ring(
        self,
        ring_id: str,
        merchants: List[Merchant],
        base_time: datetime,
        account_count: int = 16,
    ) -> Tuple[FraudRing, List[Customer], List[Transaction]]:
        """
        Scenario 2: Shared-IP Proxy / Botnet Ring
        Coordinated burst from an identical VPN/datacenter IP subnet targeting multiple merchants.
        """
        shared_ip = f"ip_dc_proxy_{self.rng.randint(1000, 9999)}"
        ring = FraudRing(
            id=ring_id,
            name=f"Proxy Farm Subnet #{ring_id[-4:]}",
            pattern_type="shared_ip_ring",
            risk_score=0.91,
            risk_band="CRITICAL",
            created_at=base_time.isoformat(),
            updated_at=(base_time + timedelta(hours=2)).isoformat(),
            description="Coordinated multi-account bot transactions originating from a single datacenter proxy.",
            ip_hashes=[shared_ip],
        )

        customers = []
        transactions = []
        total_attempted = 0.0

        for i in range(account_count):
            cust_id = f"cust_sip_{ring_id[-4:]}_{i:03d}"
            dev_id = f"dev_generic_{self.rng.randint(10000, 99999)}"
            email_hash = f"em_sip_{self.rng.randint(100000, 999999)}"
            phone_hash = f"ph_sip_{self.rng.randint(100000, 999999)}"
            token_hash = f"tok_sip_{self.rng.randint(100000, 999999)}"

            customer = Customer(
                id=cust_id,
                created_at=(base_time - timedelta(hours=self.rng.randint(2, 24))).isoformat(),
                first_seen_at=base_time.isoformat(),
                last_seen_at=(base_time + timedelta(hours=2)).isoformat(),
                email_hash=email_hash,
                phone_hash=phone_hash,
                devices=[dev_id],
                ips=[shared_ip],
                payment_tokens=[token_hash],
            )
            customers.append(customer)
            ring.customer_ids.append(cust_id)
            ring.device_ids.append(dev_id)
            ring.payment_token_hashes.append(token_hash)

            # 1-3 transactions per account in tight 90 min window
            for j in range(self.rng.randint(1, 3)):
                tx_time = base_time + timedelta(minutes=self.rng.randint(2, 90))
                amount = round(self.rng.uniform(1200.0, 6500.0), 2)
                total_attempted += amount
                tx_id = f"tx_sip_{ring_id[-4:]}_{i:02d}_{j:02d}"
                merchant = self.rng.choice(merchants)

                tx = Transaction(
                    transaction_id=tx_id,
                    timestamp=tx_time.isoformat(),
                    merchant_id=merchant.id,
                    customer_id=cust_id,
                    amount=amount,
                    currency="INR",
                    payment_method=self.rng.choice(["card", "netbanking"]),
                    status="captured" if self.rng.random() < 0.65 else "failed",
                    device_id=dev_id,
                    ip_hash=shared_ip,
                    email_hash=email_hash,
                    phone_hash=phone_hash,
                    payment_token_hash=token_hash,
                    billing_country="IND",
                    shipping_country="IND",
                    order_id=f"ord_{tx_id}",
                    is_fraud=True,
                    fraud_type="shared_ip_ring",
                    ring_id=ring_id,
                )
                transactions.append(tx)
                ring.transaction_ids.append(tx_id)

        ring.member_count = len(customers)
        ring.attempted_amount = round(total_attempted, 2)
        ring.estimated_loss = round(total_attempted * 0.65, 2)
        return ring, customers, transactions

    def generate_shared_token_ring(
        self,
        ring_id: str,
        merchants: List[Merchant],
        base_time: datetime,
        account_count: int = 14,
    ) -> Tuple[FraudRing, List[Customer], List[Transaction]]:
        """
        Scenario 3: Shared Payment Token / Card Reuse Ring
        1 or 2 stolen credit card hashes tested across many fake customer identities.
        """
        primary_token = f"tok_stolen_{self.rng.randint(10000, 99999)}"
        secondary_token = f"tok_stolen_{self.rng.randint(10000, 99999)}"
        stolen_tokens = [primary_token, secondary_token]

        ring = FraudRing(
            id=ring_id,
            name=f"Card-Reuse Syndicate #{ring_id[-4:]}",
            pattern_type="shared_payment_token_ring",
            risk_score=0.96,
            risk_band="CRITICAL",
            created_at=base_time.isoformat(),
            updated_at=(base_time + timedelta(hours=6)).isoformat(),
            description="Stolen card payment instruments reused across divergent identities and devices.",
            payment_token_hashes=stolen_tokens,
        )

        customers = []
        transactions = []
        total_attempted = 0.0

        for i in range(account_count):
            cust_id = f"cust_stk_{ring_id[-4:]}_{i:03d}"
            dev_id = f"dev_stk_{self.rng.randint(10000, 99999)}"
            ip_hash = f"ip_stk_{self.rng.randint(10, 99)}_{self.rng.randint(100, 999)}"
            email_hash = f"em_stk_{self.rng.randint(100000, 999999)}"
            phone_hash = f"ph_stk_{self.rng.randint(100000, 999999)}"
            tok = primary_token if self.rng.random() < 0.75 else secondary_token

            customer = Customer(
                id=cust_id,
                created_at=(base_time - timedelta(days=self.rng.randint(1, 10))).isoformat(),
                first_seen_at=base_time.isoformat(),
                last_seen_at=(base_time + timedelta(hours=5)).isoformat(),
                email_hash=email_hash,
                phone_hash=phone_hash,
                devices=[dev_id],
                ips=[ip_hash],
                payment_tokens=[tok],
            )
            customers.append(customer)
            ring.customer_ids.append(cust_id)
            ring.device_ids.append(dev_id)
            ring.ip_hashes.append(ip_hash)

            for j in range(self.rng.randint(2, 4)):
                tx_time = base_time + timedelta(minutes=self.rng.randint(10, 300))
                amount = round(self.rng.uniform(3500.0, 18500.0), 2)
                total_attempted += amount
                tx_id = f"tx_stk_{ring_id[-4:]}_{i:02d}_{j:02d}"
                merchant = self.rng.choice(merchants)

                tx = Transaction(
                    transaction_id=tx_id,
                    timestamp=tx_time.isoformat(),
                    merchant_id=merchant.id,
                    customer_id=cust_id,
                    amount=amount,
                    currency="INR",
                    payment_method="card",
                    status="captured" if self.rng.random() < 0.60 else "failed",
                    device_id=dev_id,
                    ip_hash=ip_hash,
                    email_hash=email_hash,
                    phone_hash=phone_hash,
                    payment_token_hash=tok,
                    billing_country="IND",
                    shipping_country="IND",
                    order_id=f"ord_{tx_id}",
                    is_fraud=True,
                    fraud_type="shared_payment_token_ring",
                    ring_id=ring_id,
                )
                transactions.append(tx)
                ring.transaction_ids.append(tx_id)

        ring.member_count = len(customers)
        ring.attempted_amount = round(total_attempted, 2)
        ring.estimated_loss = round(total_attempted * 0.60, 2)
        return ring, customers, transactions

    def generate_account_takeover(
        self,
        ring_id: str,
        merchants: List[Merchant],
        base_time: datetime,
        victim_count: int = 5,
    ) -> Tuple[FraudRing, List[Customer], List[Transaction]]:
        """
        Scenario 4: Account Takeover (ATO) Ring
        Legitimate customers with long benign history suddenly transacting from an attacker's device/IP
        at 5-10x their normal ticket size.
        """
        attacker_device = f"dev_ato_hacker_{self.rng.randint(1000, 9999)}"
        attacker_ip = f"ip_ato_foreign_{self.rng.randint(1000, 9999)}"

        ring = FraudRing(
            id=ring_id,
            name=f"Credential Spill ATO Ring #{ring_id[-4:]}",
            pattern_type="account_takeover",
            risk_score=0.92,
            risk_band="CRITICAL",
            created_at=base_time.isoformat(),
            updated_at=(base_time + timedelta(hours=3)).isoformat(),
            description="Compromised legitimate accounts accessed simultaneously via an external attacker device.",
            device_ids=[attacker_device],
            ip_hashes=[attacker_ip],
        )

        customers = []
        transactions = []
        total_attempted = 0.0

        for i in range(victim_count):
            cust_id = f"cust_ato_victim_{ring_id[-4:]}_{i:02d}"
            legit_device = f"dev_user_phone_{self.rng.randint(10000, 99999)}"
            legit_ip = f"ip_home_isp_{self.rng.randint(10000, 99999)}"
            email_hash = f"em_legit_{self.rng.randint(100000, 999999)}"
            phone_hash = f"ph_legit_{self.rng.randint(100000, 999999)}"
            token_hash = f"tok_stored_{self.rng.randint(100000, 999999)}"

            customer = Customer(
                id=cust_id,
                created_at=(base_time - timedelta(days=self.rng.randint(90, 365))).isoformat(),
                first_seen_at=(base_time - timedelta(days=90)).isoformat(),
                last_seen_at=(base_time + timedelta(hours=2)).isoformat(),
                email_hash=email_hash,
                phone_hash=phone_hash,
                devices=[legit_device, attacker_device],
                ips=[legit_ip, attacker_ip],
                payment_tokens=[token_hash],
            )
            customers.append(customer)
            ring.customer_ids.append(cust_id)
            ring.payment_token_hashes.append(token_hash)

            # Historical benign transactions (20-30 days ago)
            for b in range(3):
                b_time = base_time - timedelta(days=self.rng.randint(10, 45))
                b_amount = round(self.rng.uniform(300.0, 1500.0), 2)
                b_id = f"tx_hist_{cust_id}_{b}"
                m = self.rng.choice(merchants)
                transactions.append(
                    Transaction(
                        transaction_id=b_id,
                        timestamp=b_time.isoformat(),
                        merchant_id=m.id,
                        customer_id=cust_id,
                        amount=b_amount,
                        currency="INR",
                        payment_method="upi",
                        status="captured",
                        device_id=legit_device,
                        ip_hash=legit_ip,
                        email_hash=email_hash,
                        phone_hash=phone_hash,
                        payment_token_hash=token_hash,
                        billing_country="IND",
                        shipping_country="IND",
                        order_id=f"ord_{b_id}",
                        is_fraud=False,
                    )
                )

            # ATO attack burst: huge spike (₹25,000 - ₹65,000) from attacker device/IP
            for a in range(2):
                ato_time = base_time + timedelta(minutes=self.rng.randint(10, 120))
                ato_amount = round(self.rng.uniform(25000.0, 65000.0), 2)
                total_attempted += ato_amount
                ato_id = f"tx_ato_{ring_id[-4:]}_{i}_{a}"
                m_elec = self.rng.choice([m for m in merchants if m.category in ["electronics", "crypto", "gaming"]] or merchants)

                tx = Transaction(
                    transaction_id=ato_id,
                    timestamp=ato_time.isoformat(),
                    merchant_id=m_elec.id,
                    customer_id=cust_id,
                    amount=ato_amount,
                    currency="INR",
                    payment_method="card",
                    status="captured" if a == 0 else "failed",
                    device_id=attacker_device,
                    ip_hash=attacker_ip,
                    email_hash=email_hash,
                    phone_hash=phone_hash,
                    payment_token_hash=token_hash,
                    billing_country="IND",
                    shipping_country=self.rng.choice(["IND", "ARE"]),  # occasional foreign shipping mismatch
                    order_id=f"ord_{ato_id}",
                    is_fraud=True,
                    fraud_type="account_takeover",
                    ring_id=ring_id,
                )
                transactions.append(tx)
                ring.transaction_ids.append(ato_id)

        ring.member_count = len(customers)
        ring.attempted_amount = round(total_attempted, 2)
        ring.estimated_loss = round(total_attempted * 0.50, 2)
        return ring, customers, transactions

    def generate_velocity_attack(
        self,
        ring_id: str,
        merchants: List[Merchant],
        base_time: datetime,
        attack_count: int = 25,
    ) -> Tuple[FraudRing, List[Customer], List[Transaction]]:
        """
        Scenario 5: Merchant Velocity Burst Attack
        Rapid automated authorizations hitting a single high-ticket merchant within 15-30 minutes.
        """
        target_merchant = self.rng.choice([m for m in merchants if m.category in ["electronics", "gaming", "travel"]] or merchants)
        attacker_device = f"dev_botrunner_{self.rng.randint(1000, 9999)}"

        ring = FraudRing(
            id=ring_id,
            name=f"Merchant Rapid-Fire Burst #{ring_id[-4:]}",
            pattern_type="velocity_attack",
            risk_score=0.93,
            risk_band="CRITICAL",
            created_at=base_time.isoformat(),
            updated_at=(base_time + timedelta(minutes=45)).isoformat(),
            description=f"Rapid automated burst targeting merchant {target_merchant.name} in tight time window.",
            device_ids=[attacker_device],
        )

        customers = []
        transactions = []
        total_attempted = 0.0

        for i in range(attack_count):
            cust_id = f"cust_vel_{ring_id[-4:]}_{i:03d}"
            ip_hash = f"ip_vel_tor_{self.rng.randint(10, 99)}_{self.rng.randint(100, 999)}"
            email_hash = f"em_vel_{self.rng.randint(100000, 999999)}"
            phone_hash = f"ph_vel_{self.rng.randint(100000, 999999)}"
            token_hash = f"tok_vel_{self.rng.randint(100000, 999999)}"

            customer = Customer(
                id=cust_id,
                created_at=(base_time - timedelta(hours=1)).isoformat(),
                first_seen_at=base_time.isoformat(),
                last_seen_at=(base_time + timedelta(minutes=30)).isoformat(),
                email_hash=email_hash,
                phone_hash=phone_hash,
                devices=[attacker_device],
                ips=[ip_hash],
                payment_tokens=[token_hash],
            )
            customers.append(customer)
            ring.customer_ids.append(cust_id)
            ring.ip_hashes.append(ip_hash)
            ring.payment_token_hashes.append(token_hash)

            tx_time = base_time + timedelta(seconds=self.rng.randint(10, 1800))
            amount = round(self.rng.uniform(4999.0, 24999.0), 2)
            total_attempted += amount
            tx_id = f"tx_vel_{ring_id[-4:]}_{i:03d}"

            tx = Transaction(
                transaction_id=tx_id,
                timestamp=tx_time.isoformat(),
                merchant_id=target_merchant.id,
                customer_id=cust_id,
                amount=amount,
                currency="INR",
                payment_method="card",
                status="captured" if self.rng.random() < 0.40 else "failed",
                device_id=attacker_device,
                ip_hash=ip_hash,
                email_hash=email_hash,
                phone_hash=phone_hash,
                payment_token_hash=token_hash,
                billing_country="IND",
                shipping_country="IND",
                order_id=f"ord_{tx_id}",
                is_fraud=True,
                fraud_type="velocity_attack",
                ring_id=ring_id,
            )
            transactions.append(tx)
            ring.transaction_ids.append(tx_id)

        ring.member_count = len(customers)
        ring.attempted_amount = round(total_attempted, 2)
        ring.estimated_loss = round(total_attempted * 0.40, 2)
        return ring, customers, transactions

    def generate_testing_and_hit_attack(
        self,
        ring_id: str,
        merchants: List[Merchant],
        base_time: datetime,
        cluster_count: int = 4,
    ) -> Tuple[FraudRing, List[Customer], List[Transaction]]:
        """
        Scenario 6: Testing-and-Hit Attack
        Series of small failed/micro authorizations (₹20-₹100) to test card validity,
        followed within minutes by high-value liquidation cash-out (₹25,000-₹75,000).
        """
        ring = FraudRing(
            id=ring_id,
            name=f"Card Testing & Cash-Out Cluster #{ring_id[-4:]}",
            pattern_type="testing_and_hit_attack",
            risk_score=0.95,
            risk_band="CRITICAL",
            created_at=base_time.isoformat(),
            updated_at=(base_time + timedelta(hours=2)).isoformat(),
            description="Micro-authorization probing on payment instruments followed by large cash-out transaction.",
        )

        customers = []
        transactions = []
        total_attempted = 0.0

        for i in range(cluster_count):
            cust_id = f"cust_tnh_{ring_id[-4:]}_{i:02d}"
            dev_id = f"dev_tnh_{self.rng.randint(10000, 99999)}"
            ip_hash = f"ip_tnh_{self.rng.randint(10000, 99999)}"
            token_hash = f"tok_tested_{self.rng.randint(10000, 99999)}"
            email_hash = f"em_tnh_{self.rng.randint(100000, 999999)}"
            phone_hash = f"ph_tnh_{self.rng.randint(100000, 999999)}"

            customer = Customer(
                id=cust_id,
                created_at=(base_time - timedelta(hours=3)).isoformat(),
                first_seen_at=base_time.isoformat(),
                last_seen_at=(base_time + timedelta(hours=1)).isoformat(),
                email_hash=email_hash,
                phone_hash=phone_hash,
                devices=[dev_id],
                ips=[ip_hash],
                payment_tokens=[token_hash],
            )
            customers.append(customer)
            ring.customer_ids.append(cust_id)
            ring.device_ids.append(dev_id)
            ring.ip_hashes.append(ip_hash)
            ring.payment_token_hashes.append(token_hash)

            # 3-5 small card testing probes (₹21 - ₹99)
            probe_count = self.rng.randint(3, 5)
            for p in range(probe_count):
                p_time = base_time + timedelta(minutes=p * 2 + self.rng.randint(1, 2))
                p_amount = round(self.rng.uniform(21.0, 99.0), 2)
                total_attempted += p_amount
                p_id = f"tx_probe_{ring_id[-4:]}_{i}_{p}"
                m = self.rng.choice(merchants)
                p_status = "failed" if p < probe_count - 1 else "authorized"

                tx = Transaction(
                    transaction_id=p_id,
                    timestamp=p_time.isoformat(),
                    merchant_id=m.id,
                    customer_id=cust_id,
                    amount=p_amount,
                    currency="INR",
                    payment_method="card",
                    status=p_status,
                    device_id=dev_id,
                    ip_hash=ip_hash,
                    email_hash=email_hash,
                    phone_hash=phone_hash,
                    payment_token_hash=token_hash,
                    billing_country="IND",
                    shipping_country="IND",
                    order_id=f"ord_{p_id}",
                    is_fraud=True,
                    fraud_type="testing_and_hit_attack",
                    ring_id=ring_id,
                )
                transactions.append(tx)
                ring.transaction_ids.append(p_id)

            # Big Cash-Out hit: 5-10 minutes after successful probe
            hit_time = base_time + timedelta(minutes=probe_count * 2 + self.rng.randint(5, 12))
            hit_amount = round(self.rng.uniform(28000.0, 78000.0), 2)
            total_attempted += hit_amount
            hit_id = f"tx_hit_{ring_id[-4:]}_{i}"
            m_hit = self.rng.choice([m for m in merchants if m.category in ["electronics", "travel", "crypto"]] or merchants)

            hit_tx = Transaction(
                transaction_id=hit_id,
                timestamp=hit_time.isoformat(),
                merchant_id=m_hit.id,
                customer_id=cust_id,
                amount=hit_amount,
                currency="INR",
                payment_method="card",
                status="captured",
                device_id=dev_id,
                ip_hash=ip_hash,
                email_hash=email_hash,
                phone_hash=phone_hash,
                payment_token_hash=token_hash,
                billing_country="IND",
                shipping_country="IND",
                order_id=f"ord_{hit_id}",
                is_fraud=True,
                fraud_type="testing_and_hit_attack",
                ring_id=ring_id,
            )
            transactions.append(hit_tx)
            ring.transaction_ids.append(hit_id)

        ring.member_count = len(customers)
        ring.attempted_amount = round(total_attempted, 2)
        ring.estimated_loss = round(total_attempted * 0.85, 2)
        return ring, customers, transactions

    def generate_distributed_mesh_ring(
        self,
        ring_id: str,
        merchants: List[Merchant],
        base_time: datetime,
        account_count: int = 18,
    ) -> Tuple[FraudRing, List[Customer], List[Transaction]]:
        """
        Scenario 7: Distributed Multi-Entity Mesh Ring
        Attackers rotate across 3-4 devices, 3 IPs, and 3 payment tokens in a complex bipartite graph.
        Entangled with 2 borderline legitimate users to make community detection authentic.
        """
        devices = [f"dev_mesh_{ring_id[-4:]}_{d}" for d in range(3)]
        ips = [f"ip_mesh_{ring_id[-4:]}_{ip}" for ip in range(3)]
        tokens = [f"tok_mesh_{ring_id[-4:]}_{t}" for t in range(3)]

        ring = FraudRing(
            id=ring_id,
            name=f"Distributed Mesh Syndicate #{ring_id[-4:]}",
            pattern_type="distributed_multi_entity_ring",
            risk_score=0.97,
            risk_band="CRITICAL",
            created_at=base_time.isoformat(),
            updated_at=(base_time + timedelta(hours=8)).isoformat(),
            description="Multi-hop coordinated mesh ring with overlapping infrastructure and token handoffs.",
            device_ids=devices,
            ip_hashes=ips,
            payment_token_hashes=tokens,
        )

        customers = []
        transactions = []
        total_attempted = 0.0

        for i in range(account_count):
            cust_id = f"cust_mesh_{ring_id[-4:]}_{i:03d}"
            email_hash = f"em_mesh_{self.rng.randint(100000, 999999)}"
            phone_hash = f"ph_mesh_{self.rng.randint(100000, 999999)}"

            # Bipartite mesh assignments
            assigned_dev = devices[i % len(devices)]
            assigned_ip = ips[(i // 2) % len(ips)]
            assigned_tok = tokens[(i + 1) % len(tokens)]

            is_edge_benign = (i >= account_count - 2)  # last 2 accounts are borderline legitimate

            customer = Customer(
                id=cust_id,
                created_at=(base_time - timedelta(days=self.rng.randint(5, 30))).isoformat(),
                first_seen_at=base_time.isoformat(),
                last_seen_at=(base_time + timedelta(hours=6)).isoformat(),
                email_hash=email_hash,
                phone_hash=phone_hash,
                devices=[assigned_dev],
                ips=[assigned_ip],
                payment_tokens=[assigned_tok],
            )
            customers.append(customer)
            ring.customer_ids.append(cust_id)

            tx_count = self.rng.randint(2, 4)
            for j in range(tx_count):
                tx_time = base_time + timedelta(minutes=self.rng.randint(10, 420))
                amount = round(self.rng.uniform(2500.0, 16500.0), 2)
                total_attempted += amount
                tx_id = f"tx_mesh_{ring_id[-4:]}_{i:02d}_{j:02d}"
                merchant = self.rng.choice(merchants)

                tx = Transaction(
                    transaction_id=tx_id,
                    timestamp=tx_time.isoformat(),
                    merchant_id=merchant.id,
                    customer_id=cust_id,
                    amount=amount,
                    currency="INR",
                    payment_method=self.rng.choice(["card", "upi", "netbanking"]),
                    status="captured" if self.rng.random() < 0.65 else "failed",
                    device_id=assigned_dev,
                    ip_hash=assigned_ip,
                    email_hash=email_hash,
                    phone_hash=phone_hash,
                    payment_token_hash=assigned_tok,
                    billing_country="IND",
                    shipping_country="IND",
                    order_id=f"ord_{tx_id}",
                    is_fraud=not is_edge_benign,
                    fraud_type="distributed_multi_entity_ring" if not is_edge_benign else None,
                    ring_id=ring_id if not is_edge_benign else None,
                )
                transactions.append(tx)
                if not is_edge_benign:
                    ring.transaction_ids.append(tx_id)

        ring.member_count = len(customers)
        ring.attempted_amount = round(total_attempted, 2)
        ring.estimated_loss = round(total_attempted * 0.65, 2)
        return ring, customers, transactions
