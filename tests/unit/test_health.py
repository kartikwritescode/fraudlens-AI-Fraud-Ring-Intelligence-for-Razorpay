import pytest
from httpx import AsyncClient, ASGITransport
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps" / "api"))

from app.main import app


@pytest.mark.asyncio
async def test_liveness_probe():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["app"] == "FraudLens"


@pytest.mark.asyncio
async def test_readiness_probe():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "services" in data
        assert "api" in data["services"]
        assert data["services"]["api"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_system_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/system/status")
        assert response.status_code == 200
        data = response.json()
        assert data["product"]["name"] == "FraudLens"
        assert len(data["phases"]) > 0
