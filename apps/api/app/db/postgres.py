"""
PostgreSQL Connection Management & Health Probes
Uses asyncpg for high-performance async database connectivity.
"""

import time
from typing import Optional, Dict, Any
import asyncpg
from app.core.config import settings
from app.core.logging import logger

_pg_pool: Optional[asyncpg.Pool] = None


async def init_postgres() -> Optional[asyncpg.Pool]:
    """Initialize asyncpg pool if PostgreSQL is reachable."""
    global _pg_pool
    try:
        _pg_pool = await asyncpg.create_pool(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            min_size=2,
            max_size=10,
            timeout=3.0,
            command_timeout=5.0,
        )
        logger.info(f"PostgreSQL connection pool established at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        return _pg_pool
    except Exception as e:
        logger.warning(f"PostgreSQL initialization failed (will retry on health probe): {str(e)}")
        _pg_pool = None
        return None


async def close_postgres() -> None:
    """Close PostgreSQL connection pool."""
    global _pg_pool
    if _pg_pool:
        await _pg_pool.close()
        _pg_pool = None
        logger.info("PostgreSQL connection pool closed.")


async def get_postgres_pool() -> Optional[asyncpg.Pool]:
    """Get active connection pool, attempting reconnection if needed."""
    global _pg_pool
    if _pg_pool is None:
        await init_postgres()
    return _pg_pool


async def check_postgres_health() -> Dict[str, Any]:
    """
    Health check probe for PostgreSQL.
    Returns connectivity state and round-trip latency.
    """
    start_time = time.perf_counter()
    pool = await get_postgres_pool()
    if pool is None:
        return {
            "status": "unreachable",
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "database": settings.POSTGRES_DB,
            "latency_ms": None,
            "message": "Connection refused or container not ready",
        }

    try:
        async with pool.acquire(timeout=2.0) as conn:
            val = await conn.fetchval("SELECT 1")
            latency = round((time.perf_counter() - start_time) * 1000, 2)
            if val == 1:
                return {
                    "status": "healthy",
                    "host": settings.POSTGRES_HOST,
                    "port": settings.POSTGRES_PORT,
                    "database": settings.POSTGRES_DB,
                    "latency_ms": latency,
                    "message": "Connected",
                }
            return {
                "status": "degraded",
                "host": settings.POSTGRES_HOST,
                "port": settings.POSTGRES_PORT,
                "database": settings.POSTGRES_DB,
                "latency_ms": latency,
                "message": f"Unexpected ping response: {val}",
            }
    except Exception as e:
        return {
            "status": "unreachable",
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "database": settings.POSTGRES_DB,
            "latency_ms": None,
            "message": str(e),
        }
