"""Initial schema: PostGIS, disasters, resources, external_cache.

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-26

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geography
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

disaster_status = postgresql.ENUM("active", "monitoring", "resolved", name="disaster_status", create_type=False)
resource_type = postgresql.ENUM(
    "shelter", "hospital", "food", "water", "rescue", name="resource_type", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.execute("CREATE TYPE disaster_status AS ENUM ('active', 'monitoring', 'resolved')")
    op.execute(
        "CREATE TYPE resource_type AS ENUM ('shelter', 'hospital', 'food', 'water', 'rescue')"
    )

    op.create_table(
        "disasters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location_name", sa.String(length=255), nullable=True),
        sa.Column("geom", Geography(geometry_type="POINT", srid=4326), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String(length=50)), nullable=False, server_default="{}"),
        sa.Column(
            "status",
            disaster_status,
            nullable=False,
            server_default=sa.text("'active'::disaster_status"),
        ),
        sa.Column("created_by", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("disaster_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("type", resource_type, nullable=False),
        sa.Column("geom", Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.ForeignKeyConstraint(["disaster_id"], ["disasters.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_resources_disaster_id", "resources", ["disaster_id"])

    op.create_table(
        "external_cache",
        sa.Column("cache_key", sa.String(length=512), primary_key=True, nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_external_cache_expires_at", "external_cache", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_external_cache_expires_at", table_name="external_cache")
    op.drop_table("external_cache")
    op.drop_index("ix_resources_disaster_id", table_name="resources")
    op.drop_table("resources")
    op.drop_table("disasters")
    op.execute("DROP TYPE IF EXISTS resource_type")
    op.execute("DROP TYPE IF EXISTS disaster_status")
    # PostGIS extension is left installed (shared Neon extension).
