"""Tests for GET /mock/scenario endpoint."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_mock_scenario_returns_started():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/mock/scenario")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "scenario started"
    assert data["duration_s"] == 30


@pytest.mark.asyncio
async def test_mock_scenario_idempotent():
    """Calling twice should both succeed (tasks run independently)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.get("/mock/scenario")
        r2 = await client.get("/mock/scenario")
    assert r1.status_code == 200
    assert r2.status_code == 200
