from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.cache import CacheService
from app.services.reports import ReportsService


@pytest.mark.asyncio
async def test_cache_stores_and_returns_reports():
    db = AsyncMock()
    db.get = AsyncMock(return_value=None)
    db.commit = AsyncMock()

    cache = CacheService(db)
    reports_svc = ReportsService()
    reports = await reports_svc.fetch_reports("id-1", "Manhattan")
    await cache.set("reports:id-1", reports_svc.serialize(reports))

    db.get.assert_called()
    db.commit.assert_called()
