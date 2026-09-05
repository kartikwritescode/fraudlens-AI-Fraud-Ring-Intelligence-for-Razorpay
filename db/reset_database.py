"""
PostgreSQL Database Reset Script for FraudLens
Truncates all tables in safe dependency order.
"""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

import asyncpg
from app.core.config import settings


async def reset_database():
    print(f"[*] Resetting PostgreSQL database at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}...")
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
        return False

    try:
        tables = [
            "audit_logs",
            "cases",
            "risk_events",
            "transactions",
            "rings",
            "customers",
            "merchants",
        ]
        for table in tables:
            await conn.execute(f"TRUNCATE TABLE {table} CASCADE;")
            print(f"    - Truncated table: {table}")

        print("[OK] PostgreSQL database reset successfully!")
        return True
    except Exception as e:
        print(f"[!] Error truncating tables: {e}")
        return False
    finally:
        await conn.close()


def main():
    asyncio.run(reset_database())


if __name__ == "__main__":
    main()
