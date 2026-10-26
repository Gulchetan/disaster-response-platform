import uuid

from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID, ST_X, ST_Y
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Disaster, Resource
from app.schemas.disaster import DisasterCreate, DisasterResponse, DisasterUpdate, ResourceResponse


def point_wkt(lat: float, lng: float) -> WKTElement:
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


async def get_disaster_or_none(db: AsyncSession, disaster_id: uuid.UUID) -> Disaster | None:
    return await db.get(Disaster, disaster_id)


async def coords_from_disaster(db: AsyncSession, disaster: Disaster) -> tuple[float | None, float | None]:
    if disaster.geom is None:
        return None, None
    result = await db.execute(
        select(ST_Y(disaster.geom).label("lat"), ST_X(disaster.geom).label("lng"))
    )
    row = result.one()
    return float(row.lat), float(row.lng)


def disaster_to_response(
    disaster: Disaster, lat: float | None = None, lng: float | None = None
) -> DisasterResponse:
    return DisasterResponse(
        id=disaster.id,
        title=disaster.title,
        description=disaster.description,
        location_name=disaster.location_name,
        latitude=lat,
        longitude=lng,
        tags=list(disaster.tags or []),
        status=disaster.status,
        created_by=disaster.created_by,
        created_at=disaster.created_at,
        updated_at=disaster.updated_at,
    )


async def create_disaster(
    db: AsyncSession,
    payload: DisasterCreate,
    created_by: str,
    location_name: str | None,
    lat: float | None,
    lng: float | None,
) -> Disaster:
    disaster = Disaster(
        title=payload.title,
        description=payload.description,
        tags=payload.tags,
        status=payload.status,
        created_by=created_by,
        location_name=location_name,
        geom=point_wkt(lat, lng) if lat is not None and lng is not None else None,
    )
    db.add(disaster)
    await db.commit()
    await db.refresh(disaster)
    return disaster


async def update_disaster(
    db: AsyncSession,
    disaster: Disaster,
    payload: DisasterUpdate,
    location_name: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    re_resolve: bool = False,
) -> Disaster:
    if payload.title is not None:
        disaster.title = payload.title
    if payload.description is not None:
        disaster.description = payload.description
    if payload.tags is not None:
        disaster.tags = payload.tags
    if payload.status is not None:
        disaster.status = payload.status
    if re_resolve and location_name is not None:
        disaster.location_name = location_name
        if lat is not None and lng is not None:
            disaster.geom = point_wkt(lat, lng)
    await db.commit()
    await db.refresh(disaster)
    return disaster


async def list_disasters(db: AsyncSession, tag: str | None) -> list[tuple[Disaster, float | None, float | None]]:
    stmt = select(Disaster).order_by(Disaster.created_at.desc())
    if tag:
        stmt = stmt.where(Disaster.tags.any(tag.lower()))
    result = await db.execute(stmt)
    disasters = result.scalars().all()
    out: list[tuple[Disaster, float | None, float | None]] = []
    for d in disasters:
        lat, lng = await coords_from_disaster(db, d)
        out.append((d, lat, lng))
    return out


async def nearby_resources(
    db: AsyncSession,
    disaster_id: uuid.UUID,
    lat: float,
    lng: float,
    radius_km: float,
) -> list[ResourceResponse]:
    center = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
    radius_m = radius_km * 1000
    distance_m = ST_Distance(Resource.geom, center)
    stmt = (
        select(Resource, (distance_m / 1000.0).label("distance_km"))
        .where(Resource.disaster_id == disaster_id)
        .where(ST_DWithin(Resource.geom, center, radius_m))
        .order_by(distance_m)
    )
    result = await db.execute(stmt)
    items: list[ResourceResponse] = []
    for resource, distance_km in result.all():
        coord = await db.execute(
            select(ST_Y(resource.geom).label("lat"), ST_X(resource.geom).label("lng"))
        )
        c = coord.one()
        items.append(
            ResourceResponse(
                id=resource.id,
                name=resource.name,
                type=resource.type.value,
                latitude=float(c.lat),
                longitude=float(c.lng),
                distance_km=round(float(distance_km), 3),
            )
        )
    return items
