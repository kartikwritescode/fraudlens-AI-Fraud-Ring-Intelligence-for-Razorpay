"""
Neo4j Graph Database Driver & Health Probes
Manages Bolt connection sessions and Cypher connectivity checks.
"""

import time
from typing import Optional, Dict, Any
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import settings
from app.core.logging import logger

_neo4j_driver: Optional[AsyncDriver] = None


async def init_neo4j() -> Optional[AsyncDriver]:
    """Initialize Async Neo4j driver."""
    global _neo4j_driver
    try:
        _neo4j_driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            connection_timeout=3.0,
        )
        logger.info(f"Neo4j driver initialized for {settings.NEO4J_URI}")
        return _neo4j_driver
    except Exception as e:
        logger.warning(f"Neo4j driver initialization failed: {str(e)}")
        _neo4j_driver = None
        return None


async def close_neo4j() -> None:
    """Close Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver:
        await _neo4j_driver.close()
        _neo4j_driver = None
        logger.info("Neo4j driver connection closed.")


async def get_neo4j_driver() -> Optional[AsyncDriver]:
    """Get active Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is None:
        await init_neo4j()
    return _neo4j_driver


async def check_neo4j_health() -> Dict[str, Any]:
    """
    Health check probe for Neo4j.
    Executes ping query over Bolt protocol.
    """
    start_time = time.perf_counter()
    driver = await get_neo4j_driver()
    if driver is None:
        return {
            "status": "unreachable",
            "uri": settings.NEO4J_URI,
            "latency_ms": None,
            "message": "Neo4j driver unavailable",
        }

    try:
        async with driver.session(database=settings.NEO4J_DATABASE) as session:
            result = await session.run("RETURN 1 AS ping")
            record = await result.single()
            latency = round((time.perf_counter() - start_time) * 1000, 2)
            if record and record["ping"] == 1:
                return {
                    "status": "healthy",
                    "uri": settings.NEO4J_URI,
                    "database": settings.NEO4J_DATABASE,
                    "latency_ms": latency,
                    "message": "Connected",
                }
            return {
                "status": "degraded",
                "uri": settings.NEO4J_URI,
                "latency_ms": latency,
                "message": "Query returned unexpected result",
            }
    except Exception as e:
        return {
            "status": "unreachable",
            "uri": settings.NEO4J_URI,
            "latency_ms": None,
            "message": str(e),
        }
