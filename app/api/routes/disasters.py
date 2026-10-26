import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, require_admin, require_contributor_or_admin
from app.schemas.disaster import DisasterCreate, DisasterResponse, DisasterUpdate, ReportResponse, ResourceResponse
from app.services import disasters as disaster_service
from app.services.cache import CacheService
from app.services.location import LocationService
from app.services.realtime import realtime_hub
from app.services.reports import ReportsService

router = APIRouter(prefix="/disasters", tags=["disasters"])

location_service = LocationService()
reports_service = ReportsService()


async def _emit_disaster_event(disaster: DisasterResponse, event: str) -> None:
    await realtime_hub.broadcast(event, disaster.model_dump(mode="json"))


@router.post("", response_model=DisasterResponse, status_code=status.HTTP_201_CREATED)
async def create_disaster(
    body: DisasterCreate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(require_contributor_or_admin),
) -> DisasterResponse:
    resolved = await location_service.resolve_from_description(body.description)
    lat = resolved.latitude if resolved else None
    lng = resolved.longitude if resolved else None
    loc_name = resolved.location_name if resolved else None

    disaster = await disaster_service.create_disaster(
        db, body, created_by=user["sub"], location_name=loc_name, lat=lat, lng=lng
    )
    lat, lng = await disaster_service.coords_from_disaster(db, disaster)
    response = disaster_service.disaster_to_response(disaster, lat, lng)
    await _emit_disaster_event(response, "disaster_created")
    return response


@router.get("", response_model=list[DisasterResponse])
async def list_disasters(
    tag: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> list[DisasterResponse]:
    rows = await disaster_service.list_disasters(db, tag)
    return [disaster_service.disaster_to_response(d, lat, lng) for d, lat, lng in rows]


@router.get("/{disaster_id}", response_model=DisasterResponse)
async def get_disaster(
    disaster_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> DisasterResponse:
    disaster = await disaster_service.get_disaster_or_none(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disaster not found")
    lat, lng = await disaster_service.coords_from_disaster(db, disaster)
    return disaster_service.disaster_to_response(disaster, lat, lng)


@router.patch("/{disaster_id}", response_model=DisasterResponse)
async def patch_disaster(
    disaster_id: uuid.UUID,
    body: DisasterUpdate,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(require_contributor_or_admin),
) -> DisasterResponse:
    disaster = await disaster_service.get_disaster_or_none(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disaster not found")

    re_resolve = body.description is not None
    loc_name = lat = lng = None
    if re_resolve and body.description:
        resolved = await location_service.resolve_from_description(body.description)
        if resolved:
            loc_name, lat, lng = resolved.location_name, resolved.latitude, resolved.longitude

    disaster = await disaster_service.update_disaster(
        db, disaster, body, location_name=loc_name, lat=lat, lng=lng, re_resolve=re_resolve
    )
    lat, lng = await disaster_service.coords_from_disaster(db, disaster)
    response = disaster_service.disaster_to_response(disaster, lat, lng)
    await _emit_disaster_event(response, "disaster_updated")
    return response


@router.delete("/{disaster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_disaster(
    disaster_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    user: dict = Depends(require_admin),
) -> None:
    disaster = await disaster_service.get_disaster_or_none(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disaster not found")
    await db.delete(disaster)
    await db.commit()
    await realtime_hub.broadcast("disaster_deleted", {"id": str(disaster_id)})


@router.get("/{disaster_id}/resources", response_model=list[ResourceResponse])
async def get_resources(
    disaster_id: uuid.UUID,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(10.0, gt=0, le=500, description="Radius in kilometers"),
    db: AsyncSession = Depends(get_db_session),
) -> list[ResourceResponse]:
    disaster = await disaster_service.get_disaster_or_none(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disaster not found")
    return await disaster_service.nearby_resources(db, disaster_id, lat, lng, radius)


@router.get("/{disaster_id}/reports", response_model=list[ReportResponse])
async def get_reports(
    disaster_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
) -> list[ReportResponse]:
    disaster = await disaster_service.get_disaster_or_none(db, disaster_id)
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disaster not found")

    cache = CacheService(db)
    cache_key = f"reports:{disaster_id}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return [ReportResponse(**{**item, "source": "cache"}) for item in cached]

    reports = await reports_service.fetch_reports(str(disaster_id), disaster.location_name)
    await cache.set(cache_key, reports_service.serialize(reports))
    return reports
