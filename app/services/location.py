import json
import re
from dataclasses import dataclass

import httpx
from groq import Groq

from app.config import settings

# Fallback coordinates for common demo locations when geocoding fails
MOCK_GEOCODE: dict[str, tuple[float, float]] = {
    "manhattan, nyc": (40.7831, -73.9712),
    "manhattan": (40.7831, -73.9712),
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
}


@dataclass
class ResolvedLocation:
    location_name: str
    latitude: float
    longitude: float


class LocationService:
    def __init__(self) -> None:
        self._groq: Groq | None = None
        if settings.groq_api_key and not settings.use_mock_llm:
            self._groq = Groq(api_key=settings.groq_api_key)

    async def resolve_from_description(self, description: str) -> ResolvedLocation | None:
        location_name = await self._extract_location_name(description)
        if not location_name:
            return None
        coords = await self._geocode(location_name)
        if not coords:
            return None
        lat, lng = coords
        return ResolvedLocation(location_name=location_name, latitude=lat, longitude=lng)

    async def _extract_location_name(self, description: str) -> str | None:
        if settings.use_mock_llm or not self._groq:
            return self._mock_extract(description)
        prompt = (
            "Extract the primary geographic location mentioned in this disaster description. "
            "Return ONLY valid JSON: {\"location\": \"City, Region\"}. "
            "If no location is found, return {\"location\": null}.\n\n"
            f"Description: {description}"
        )
        try:
            completion = self._groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=128,
            )
            raw = completion.choices[0].message.content or ""
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                return self._mock_extract(description)
            data = json.loads(match.group())
            loc = data.get("location")
            return str(loc).strip() if loc else None
        except Exception:
            return self._mock_extract(description)

    def _mock_extract(self, description: str) -> str | None:
        lower = description.lower()
        for key in MOCK_GEOCODE:
            if key in lower:
                return key.title() if "," not in key else key.replace(",", ",").title()
        # Simple pattern: "in <place>"
        m = re.search(r"\b(?:in|at|near)\s+([A-Za-z][A-Za-z\s,]{2,40})", description, re.I)
        if m:
            return m.group(1).strip().rstrip(".")
        return None

    async def _geocode(self, location_name: str) -> tuple[float, float] | None:
        key = location_name.lower().strip()
        if settings.use_mock_geocoding:
            return MOCK_GEOCODE.get(key) or self._fuzzy_mock(key)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": location_name, "format": "json", "limit": 1},
                    headers={"User-Agent": settings.nominatim_user_agent},
                )
                resp.raise_for_status()
                data = resp.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            pass
        return MOCK_GEOCODE.get(key) or self._fuzzy_mock(key)

    def _fuzzy_mock(self, key: str) -> tuple[float, float] | None:
        for mock_key, coords in MOCK_GEOCODE.items():
            if mock_key in key or key in mock_key:
                return coords
        return None
