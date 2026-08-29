"""create hazard_events table

Revision ID: 0001
Revises:
Create Date: 2026-08-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.create_table(
        "hazard_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("hazard_type", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("magnitude", sa.Numeric(), nullable=True),
        sa.Column("depth_km", sa.Numeric(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("place_name", sa.Text(), nullable=False),
        sa.Column("alert_level", sa.Text(), nullable=True),
        sa.Column(
            "location",
            Geography(geometry_type="POINT", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("raw_payload", JSONB(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "hazard_type IN ('earthquake', 'volcanic', 'landslide')",
            name="ck_hazard_events_hazard_type",
        ),
        sa.UniqueConstraint("source", "external_id", name="uq_hazard_events_source_external_id"),
    )
    op.create_index("idx_hazard_events_occurred_at", "hazard_events", ["occurred_at"])
    op.create_index(
        "idx_hazard_events_geo",
        "hazard_events",
        ["location"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index("idx_hazard_events_geo", table_name="hazard_events")
    op.drop_index("idx_hazard_events_occurred_at", table_name="hazard_events")
    op.drop_table("hazard_events")
