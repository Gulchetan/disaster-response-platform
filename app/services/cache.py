import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import ExternalCacheEntry


class CacheService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ttl = timedelta(seconds=settings.cache_ttl_seconds)

    async def get(self, key: str) -> Any | None:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(ExternalCacheEntry).where(
                ExternalCacheEntry.cache_key == key,
                ExternalCacheEntry.expires_at > now,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return json.loads(row.payload)

    async def set(self, key: str, value: Any) -> None:
        expires = datetime.now(timezone.utc) + self.ttl
        payload = json.dumps(value)
        existing = await self.db.get(ExternalCacheEntry, key)
        if existing:
            existing.payload = payload
            existing.expires_at = expires
        else:
            self.db.add(ExternalCacheEntry(cache_key=key, payload=payload, expires_at=expires))
        await self.db.commit()

    async def purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        await self.db.execute(delete(ExternalCacheEntry).where(ExternalCacheEntry.expires_at <= now))
        await self.db.commit()
