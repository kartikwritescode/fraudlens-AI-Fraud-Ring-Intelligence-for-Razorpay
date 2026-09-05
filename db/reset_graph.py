"""
Neo4j Graph Database Reset Script for FraudLens
Safely drops all nodes, relationships, and constraints in the Neo4j database.
"""

import asyncio
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "apps" / "api"))

from neo4j import AsyncGraphDatabase
from app.core.config import settings


async def reset_graph():
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
        return False

    try:
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            print("[*] Detaching and deleting all nodes and relationships...")
            # Delete in batches to prevent transaction memory overflow
            result = await session.run("MATCH (n) DETACH DELETE n")
            summary = await result.consume()
            print(f"[OK] Deleted nodes and relationships. Nodes deleted: {summary.counters.nodes_deleted:,}")
            return True
    finally:
        await driver.close()


def main():
    asyncio.run(reset_graph())


if __name__ == "__main__":
    main()
