"""Seed sample disasters and resources. Run after DB is up: python -m scripts.seed_data"""

import asyncio
import uuid

from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Disaster, DisasterStatus, Resource, ResourceType


def point(lat: float, lng: float) -> WKTElement:
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    try:
        Session = async_sessionmaker(engine, expire_on_commit=False)
        async with Session() as db:
            existing = await db.execute(select(Disaster).limit(1))
            if existing.scalar_one_or_none():
                print("Seed skipped: disasters already exist")
                return

            disaster = Disaster(
                id=uuid.uuid4(),
                title="Manhattan Flood Response",
                description="Heavy flooding has affected Manhattan, NYC.",
                location_name="Manhattan, NYC",
                geom=point(40.7831, -73.9712),
                tags=["flood", "urgent"],
                status=DisasterStatus.active,
                created_by="admin",
            )
            db.add(disaster)
            await db.flush()

            resources = [
                ("East Side Shelter", ResourceType.shelter, 40.776, -73.954),
                ("Bellevue Hospital", ResourceType.hospital, 40.739, -73.974),
                ("Central Food Bank", ResourceType.food, 40.768, -73.982),
                ("Hudson Water Station", ResourceType.water, 40.754, -74.001),
                ("FDNY Rescue Unit 4", ResourceType.rescue, 40.748, -73.985),
            ]
            for name, rtype, lat, lng in resources:
                db.add(
                    Resource(
                        disaster_id=disaster.id,
                        name=name,
                        type=rtype,
                        geom=point(lat, lng),
                    )
                )
            await db.commit()
            print(f"Seeded disaster {disaster.id} with {len(resources)} resources")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
