"""
API v1 Central Router
"""

from fastapi import APIRouter
from app.api.v1.endpoints import health, system, transactions, graph, agent, webhooks, analytics, demo

api_router = APIRouter()

# Register endpoints
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(transactions.router)
api_router.include_router(graph.router)
api_router.include_router(agent.router)
api_router.include_router(webhooks.router)
api_router.include_router(analytics.router)
api_router.include_router(demo.router)
