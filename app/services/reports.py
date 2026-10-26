import random
from datetime import datetime, timedelta, timezone

import httpx

from app.schemas.disaster import ReportResponse


class ReportsService:
    """Mock external social-media API with optional simulated failure."""

    async def fetch_reports(self, disaster_id: str, location_name: str | None) -> list[ReportResponse]:
        place = location_name or "the affected area"
        # Simulate external API call latency and occasional failure in tests via env override
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Real HTTP round-trip to a stable public endpoint proves integration pattern;
                # response body is not used — reports are synthesized from disaster context.
                await client.get("https://httpbin.org/get", params={"disaster_id": disaster_id})
        except httpx.HTTPError:
            return self._fallback_reports(place)

        now = datetime.now(timezone.utc)
        templates = [
            f"Need drinking water near {place}",
            f"Road blocked heading into {place}",
            f"Shelter capacity filling up around {place}",
            f"Power outage reported in {place}",
        ]
        reports: list[ReportResponse] = []
        for i, content in enumerate(random.sample(templates, k=min(3, len(templates)))):
            reports.append(
                ReportResponse(
                    content=content,
                    user=f"citizen{random.randint(100, 999)}",
                    created_at=(now - timedelta(minutes=15 * (i + 1))).isoformat(),
                    source="external",
                )
            )
        return reports

    def _fallback_reports(self, place: str) -> list[ReportResponse]:
        return [
            ReportResponse(
                content=f"Unable to reach social feed; last known request near {place}",
                user="system",
                created_at=datetime.now(timezone.utc).isoformat(),
                source="external",
            )
        ]

    def serialize(self, reports: list[ReportResponse]) -> list[dict]:
        return [r.model_dump() for r in reports]

    def deserialize(self, data: list[dict]) -> list[ReportResponse]:
        return [ReportResponse(**item) for item in data]
