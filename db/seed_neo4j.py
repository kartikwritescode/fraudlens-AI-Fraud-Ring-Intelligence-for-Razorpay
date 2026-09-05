"""
Neo4j Graph Database Seeding Script for FraudLens
Batch-populates multi-entity nodes and all 9 relationship types using optimized Cypher UNWIND queries.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from neo4j import AsyncGraphDatabase
from app.core.config import settings
from services.simulator.generator import SyntheticUniverseGenerator
from services.simulator.models import PaymentUniverse
from services.graph_engine.graph_builder import build_graph_from_universe, GraphStructure


async def apply_constraints(session):
    """Executes constraints from 001_constraints.cypher."""
    cypher_file = ROOT_DIR / "db" / "neo4j" / "001_constraints.cypher"
    if cypher_file.exists():
        queries = [
            q.strip()
            for q in cypher_file.read_text(encoding="utf-8").split(";")
            if q.strip() and not q.strip().startswith("//")
        ]
        for q in queries:
            try:
                await session.run(q)
            except Exception as e:
                # Constraint or index might already exist
                pass
        print("[OK] Applied Neo4j uniqueness constraints & indexes.")


async def seed_neo4j(
    universe: PaymentUniverse,
    batch_size: int = 5000,
):
    print(f"[*] Connecting to Neo4j at {settings.NEO4J_URI}...")
    try:
        driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=5.0,
        )
        await driver.verify_connectivity()
    except Exception as e:
        print(f"[!] Could not connect to Neo4j: {e}")
        print("    Ensure Neo4j is running (e.g. docker compose -f infra/docker-compose.yml up -d)")
        return False

    graph = build_graph_from_universe(universe)
    node_counts = graph.get_node_counts()
    rel_counts = graph.get_relationship_counts()

    print(f"[*] In-memory graph prepared: {node_counts['TotalNodes']:,} nodes, {rel_counts['TotalRelationships']:,} edges.")

    try:
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            await apply_constraints(session)

            # 1. Ingest Merchants
            print(f"[*] Ingesting {len(graph.merchants)} Merchant nodes...")
            merchant_list = list(graph.merchants.values())
            await session.run(
                """
                UNWIND $batch AS row
                MERGE (m:Merchant {id: row.id})
                SET m.name = row.name, m.category = row.category, m.created_at = row.created_at
                """,
                batch=merchant_list,
            )

            # 2. Ingest Devices
            print(f"[*] Ingesting {len(graph.devices):,} Device nodes...")
            dev_list = list(graph.devices.values())
            for i in range(0, len(dev_list), batch_size):
                chunk = dev_list[i : i + batch_size]
                await session.run(
                    "UNWIND $batch AS row MERGE (d:Device {id: row.id})",
                    batch=chunk,
                )

            # 3. Ingest IPs
            print(f"[*] Ingesting {len(graph.ips):,} IP nodes...")
            ip_list = list(graph.ips.values())
            for i in range(0, len(ip_list), batch_size):
                chunk = ip_list[i : i + batch_size]
                await session.run(
                    "UNWIND $batch AS row MERGE (i:IP {ip_hash: row.ip_hash})",
                    batch=chunk,
                )

            # 4. Ingest Payment Tokens
            print(f"[*] Ingesting {len(graph.payment_tokens):,} PaymentToken nodes...")
            tok_list = list(graph.payment_tokens.values())
            for i in range(0, len(tok_list), batch_size):
                chunk = tok_list[i : i + batch_size]
                await session.run(
                    "UNWIND $batch AS row MERGE (p:PaymentToken {token_hash: row.token_hash})",
                    batch=chunk,
                )

            # 5. Ingest Emails
            print(f"[*] Ingesting {len(graph.emails):,} Email nodes...")
            em_list = list(graph.emails.values())
            for i in range(0, len(em_list), batch_size):
                chunk = em_list[i : i + batch_size]
                await session.run(
                    "UNWIND $batch AS row MERGE (e:Email {email_hash: row.email_hash})",
                    batch=chunk,
                )

            # 6. Ingest Phones
            print(f"[*] Ingesting {len(graph.phones):,} Phone nodes...")
            ph_list = list(graph.phones.values())
            for i in range(0, len(ph_list), batch_size):
                chunk = ph_list[i : i + batch_size]
                await session.run(
                    "UNWIND $batch AS row MERGE (ph:Phone {phone_hash: row.phone_hash})",
                    batch=chunk,
                )

            # 7. Ingest Customers
            print(f"[*] Ingesting {len(graph.customers):,} Customer nodes...")
            cust_list = list(graph.customers.values())
            for i in range(0, len(cust_list), batch_size):
                chunk = cust_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MERGE (c:Customer {id: row.id})
                    SET c.country = row.country, c.created_at = row.created_at
                    """,
                    batch=chunk,
                )

            # 8. Ingest Transactions
            print(f"[*] Ingesting {len(graph.transactions):,} Transaction nodes...")
            tx_list = list(graph.transactions.values())
            for i in range(0, len(tx_list), batch_size):
                chunk = tx_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MERGE (t:Transaction {id: row.id})
                    SET t.amount = row.amount, t.currency = row.currency,
                        t.timestamp = row.timestamp, t.status = row.status,
                        t.payment_method = row.payment_method, t.is_fraud = row.is_fraud,
                        t.fraud_type = row.fraud_type, t.ring_id = row.ring_id
                    """,
                    batch=chunk,
                )

            # -------------------------------------------------------------
            # Relationships Ingestion
            # -------------------------------------------------------------
            print("[*] Ingesting multi-entity graph relationships...")

            # CUSTOMER_MADE_TRANSACTION
            cmt_list = [{"cust": s, "tx": t} for s, t in graph.customer_made_transaction]
            for i in range(0, len(cmt_list), batch_size):
                chunk = cmt_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (c:Customer {id: row.cust})
                    MATCH (t:Transaction {id: row.tx})
                    CREATE (c)-[:CUSTOMER_MADE_TRANSACTION]->(t)
                    """,
                    batch=chunk,
                )

            # TRANSACTION_FOR_MERCHANT
            tfm_list = [{"tx": s, "mer": t} for s, t in graph.transaction_for_merchant]
            for i in range(0, len(tfm_list), batch_size):
                chunk = tfm_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (t:Transaction {id: row.tx})
                    MATCH (m:Merchant {id: row.mer})
                    CREATE (t)-[:TRANSACTION_FOR_MERCHANT]->(m)
                    """,
                    batch=chunk,
                )

            # CUSTOMER_USES_DEVICE
            cud_list = [{"cust": s, "dev": t} for s, t in graph.customer_uses_device]
            for i in range(0, len(cud_list), batch_size):
                chunk = cud_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (c:Customer {id: row.cust})
                    MATCH (d:Device {id: row.dev})
                    MERGE (c)-[:CUSTOMER_USES_DEVICE]->(d)
                    """,
                    batch=chunk,
                )

            # CUSTOMER_USES_IP
            cui_list = [{"cust": s, "ip": t} for s, t in graph.customer_uses_ip]
            for i in range(0, len(cui_list), batch_size):
                chunk = cui_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (c:Customer {id: row.cust})
                    MATCH (i:IP {ip_hash: row.ip})
                    MERGE (c)-[:CUSTOMER_USES_IP]->(i)
                    """,
                    batch=chunk,
                )

            # CUSTOMER_USES_PAYMENT_TOKEN
            cut_list = [{"cust": s, "tok": t} for s, t in graph.customer_uses_payment_token]
            for i in range(0, len(cut_list), batch_size):
                chunk = cut_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (c:Customer {id: row.cust})
                    MATCH (p:PaymentToken {token_hash: row.tok})
                    MERGE (c)-[:CUSTOMER_USES_PAYMENT_TOKEN]->(p)
                    """,
                    batch=chunk,
                )

            # CUSTOMER_HAS_EMAIL
            che_list = [{"cust": s, "em": t} for s, t in graph.customer_has_email]
            for i in range(0, len(che_list), batch_size):
                chunk = che_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (c:Customer {id: row.cust})
                    MATCH (e:Email {email_hash: row.em})
                    MERGE (c)-[:CUSTOMER_HAS_EMAIL]->(e)
                    """,
                    batch=chunk,
                )

            # CUSTOMER_HAS_PHONE
            chp_list = [{"cust": s, "ph": t} for s, t in graph.customer_has_phone]
            for i in range(0, len(chp_list), batch_size):
                chunk = chp_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (c:Customer {id: row.cust})
                    MATCH (ph:Phone {phone_hash: row.ph})
                    MERGE (c)-[:CUSTOMER_HAS_PHONE]->(ph)
                    """,
                    batch=chunk,
                )

            # TRANSACTION_FROM_DEVICE
            tfd_list = [{"tx": s, "dev": t} for s, t in graph.transaction_from_device]
            for i in range(0, len(tfd_list), batch_size):
                chunk = tfd_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (t:Transaction {id: row.tx})
                    MATCH (d:Device {id: row.dev})
                    MERGE (t)-[:TRANSACTION_FROM_DEVICE]->(d)
                    """,
                    batch=chunk,
                )

            # TRANSACTION_FROM_IP
            tfi_list = [{"tx": s, "ip": t} for s, t in graph.transaction_from_ip]
            for i in range(0, len(tfi_list), batch_size):
                chunk = tfi_list[i : i + batch_size]
                await session.run(
                    """
                    UNWIND $batch AS row
                    MATCH (t:Transaction {id: row.tx})
                    MATCH (i:IP {ip_hash: row.ip})
                    MERGE (t)-[:TRANSACTION_FROM_IP]->(i)
                    """,
                    batch=chunk,
                )

            print("[OK] Neo4j graph successfully populated with all nodes and relationships!")
            return True

    finally:
        await driver.close()


def main():
    parser = argparse.ArgumentParser(description="Seed Neo4j graph database with synthetic payment universe")
    parser.add_argument("--transactions", type=int, default=50000, help="Transaction count")
    parser.add_argument("--customers", type=int, default=8000, help="Customer count")
    parser.add_argument("--merchants", type=int, default=120, help="Merchant count")
    parser.add_argument("--rings", type=int, default=10, help="Fraud ring count")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed")

    args = parser.parse_args()

    print(f"[*] Generating {args.transactions:,} transactions (seed={args.seed})...")
    gen = SyntheticUniverseGenerator(
        target_transactions=args.transactions,
        customer_count=args.customers,
        merchant_count=args.merchants,
        ring_count=args.rings,
        seed=args.seed,
    )
    universe = gen.generate_universe()

    asyncio.run(seed_neo4j(universe))


if __name__ == "__main__":
    main()
