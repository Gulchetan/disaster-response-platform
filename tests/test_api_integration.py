import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base
from app.main import app


async def _db_available() -> bool:
    try:
        engine = create_async_engine(settings.database_url)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not os.getenv("RUN_INTEGRATION"), reason="Set RUN_INTEGRATION=1 with Postgres")


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_disaster_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/disasters",
        json={"title": "Test flood", "description": "Heavy flooding in Manhattan, NYC.", "tags": ["flood"]},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_contributor_cannot_delete(client: AsyncClient):
    token_resp = await client.post("/auth/token", json={"username": "contributor", "password": "contrib123"})
    token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/disasters",
        json={"title": "Test flood", "description": "Heavy flooding in Manhattan, NYC.", "tags": ["flood"]},
        headers=headers,
    )
    assert create.status_code == 201
    disaster_id = create.json()["id"]

    delete = await client.delete(f"/disasters/{disaster_id}", headers=headers)
    assert delete.status_code == 403


@pytest.mark.asyncio
async def test_filter_by_tag(client: AsyncClient):
    admin_token = (
        await client.post("/auth/token", json={"username": "admin", "password": "admin123"})
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    await client.post(
        "/disasters",
        json={"title": "Flood A", "description": "Flooding in Manhattan, NYC today.", "tags": ["flood"]},
        headers=headers,
    )
    await client.post(
        "/disasters",
        json={"title": "Fire B", "description": "Wildfire near Los Angeles county.", "tags": ["fire"]},
        headers=headers,
    )

    resp = await client.get("/disasters?tag=flood")
    assert resp.status_code == 200
    assert all("flood" in d["tags"] for d in resp.json())
