import pytest

from app.services.location import LocationService


@pytest.mark.asyncio
async def test_mock_extract_manhattan_from_description():
    svc = LocationService()
    resolved = await svc.resolve_from_description("Heavy flooding has affected Manhattan, NYC.")
    assert resolved is not None
    assert "manhattan" in resolved.location_name.lower()
    assert abs(resolved.latitude - 40.7831) < 0.01
    assert abs(resolved.longitude - (-73.9712)) < 0.01


@pytest.mark.asyncio
async def test_no_location_returns_none():
    svc = LocationService()
    resolved = await svc.resolve_from_description("Generic situation with no place names at all.")
    assert resolved is None
