import enum
import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DisasterStatus(str, enum.Enum):
    active = "active"
    monitoring = "monitoring"
    resolved = "resolved"


class ResourceType(str, enum.Enum):
    shelter = "shelter"
    hospital = "hospital"
    food = "food"
    water = "water"
    rescue = "rescue"


class Disaster(Base):
    __tablename__ = "disasters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geom: Mapped[object | None] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list, nullable=False)
    status: Mapped[DisasterStatus] = mapped_column(
        Enum(DisasterStatus, name="disaster_status"), default=DisasterStatus.active, nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    resources: Mapped[list["Resource"]] = relationship(back_populates="disaster", cascade="all, delete-orphan")


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    disaster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("disasters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[ResourceType] = mapped_column(Enum(ResourceType, name="resource_type"), nullable=False)
    geom: Mapped[object] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=False)

    disaster: Mapped["Disaster"] = relationship(back_populates="resources")


class ExternalCacheEntry(Base):
    """PostgreSQL-backed cache for external API responses (reports)."""

    __tablename__ = "external_cache"

    cache_key: Mapped[str] = mapped_column(String(512), primary_key=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
