"""
PostgreSQL Database Seeding Script for FraudLens
Batch-inserts synthetic customers, merchants, rings, and transactions.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import List

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

import asyncpg
from app.core.config import settings
from services.simulator.generator import SyntheticUniverseGenerator
from services.simulator.models import PaymentUniverse


async def apply_schema(conn: asyncpg.Connection):
    """Executes 001_initial_schema.sql DDL."""
    schema_path = ROOT_DIR / "db" / "migrations" / "001_initial_schema.sql"
    if schema_path.exists():
        sql = schema_path.read_text(encoding="utf-8")
        await conn.execute(sql)
        print("[OK] Applied PostgreSQL initial schema.")


async def seed_postgres(
    universe: PaymentUniverse,
    batch_size: int = 5000,
):
    """Inserts all entities into PostgreSQL tables in streaming batches."""
    print(f"[*] Connecting to PostgreSQL at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}...")

    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            timeout=5.0,
        )
    except Exception as e:
        print(f"[!] Could not connect to PostgreSQL: {e}")
        print("    Ensure PostgreSQL is running (e.g. docker compose -f infra/docker-compose.yml up -d)")
        return False

    try:
        await apply_schema(conn)

        # 1. Insert Merchants
        print(f"[*] Seeding {len(universe.merchants)} merchants...")
        merchant_records = [
            (m.id, m.name, m.category, datetime_from_iso(m.created_at))
            for m in universe.merchants
        ]
        await conn.executemany(
            """
            INSERT INTO merchants (id, name, category, created_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, category = EXCLUDED.category;
            """,
            merchant_records,
        )
        print(f"[OK] {len(universe.merchants)} merchants seeded.")

        # 2. Insert Customers
        print(f"[*] Seeding {len(universe.customers)} customers...")
        customer_records = [
            (
                c.id,
                c.country,
                datetime_from_iso(c.first_seen_at),
                datetime_from_iso(c.last_seen_at),
                datetime_from_iso(c.created_at),
            )
            for c in universe.customers
        ]
        # Chunked insert
        for i in range(0, len(customer_records), batch_size):
            chunk = customer_records[i : i + batch_size]
            await conn.executemany(
                """
                INSERT INTO customers (id, country, first_seen_at, last_seen_at, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO NOTHING;
                """,
                chunk,
            )
        print(f"[OK] {len(universe.customers)} customers seeded.")

        # 3. Insert Fraud Rings
        print(f"[*] Seeding {len(universe.fraud_rings)} fraud rings...")
        ring_records = [
            (
                r.id,
                r.name,
                r.pattern_type,
                r.risk_score,
                r.risk_band,
                r.member_count,
                r.attempted_amount,
                r.estimated_loss,
                r.status,
                datetime_from_iso(r.created_at),
                datetime_from_iso(r.updated_at),
            )
            for r in universe.fraud_rings
        ]
        await conn.executemany(
            """
            INSERT INTO rings (id, name, pattern_type, risk_score, risk_band, member_count, attempted_amount, estimated_loss, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (id) DO UPDATE SET risk_score = EXCLUDED.risk_score, member_count = EXCLUDED.member_count;
            """,
            ring_records,
        )
        print(f"[OK] {len(universe.fraud_rings)} fraud rings seeded.")

        # 4. Insert Transactions
        print(f"[*] Seeding {len(universe.transactions)} transactions...")
        tx_records = [
            (
                t.transaction_id,
                f"pay_{t.transaction_id}",
                t.order_id,
                t.merchant_id,
                t.customer_id,
                t.ring_id,
                t.amount,
                t.currency,
                t.status,
                t.payment_method,
                t.device_id,
                t.ip_hash,
                t.email_hash,
                t.phone_hash,
                t.payment_token_hash,
                t.billing_country,
                t.shipping_country,
                0.95 if t.is_fraud else 0.15,
                "CRITICAL" if t.is_fraud else "LOW",
                t.is_fraud,
                t.fraud_type,
                datetime_from_iso(t.timestamp),
            )
            for t in universe.transactions
        ]

        for i in range(0, len(tx_records), batch_size):
            chunk = tx_records[i : i + batch_size]
            await conn.executemany(
                """
                INSERT INTO transactions (
                    id, razorpay_payment_id, order_id, merchant_id, customer_id, ring_id,
                    amount, currency, status, payment_method, device_id, ip_hash,
                    email_hash, phone_hash, payment_token_hash, billing_country, shipping_country,
                    risk_score, risk_band, is_fraud, fraud_type, timestamp
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13, $14, $15, $16, $17, $18, $19, $20, $21, $22
                )
                ON CONFLICT (id) DO NOTHING;
                """,
                chunk,
            )
            print(f"    - Inserted transactions {min(i + batch_size, len(tx_records)):,} / {len(tx_records):,}")

        print(f"[OK] {len(universe.transactions)} transactions seeded successfully into PostgreSQL!")
        return True

    finally:
        await conn.close()


def datetime_from_iso(iso_str: str):
    from datetime import datetime
    try:
        return datetime.fromisoformat(iso_str)
    except Exception:
        return datetime.now()


def main():
    parser = argparse.ArgumentParser(description="Seed PostgreSQL database with synthetic payment data")
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

    asyncio.run(seed_postgres(universe))


if __name__ == "__main__":
    main()
