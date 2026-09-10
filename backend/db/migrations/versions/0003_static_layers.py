"""Persist imported static reference layers."""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table, types in (
        ("fault_lines", "'LINESTRING', 'MULTILINESTRING'"),
        ("volcano_zones", "'POLYGON', 'MULTIPOLYGON'"),
    ):
        op.create_table(
            table,
            sa.Column("id", sa.Text(), primary_key=True),
            *[
                sa.Column(name, sa.Text(), nullable=False)
                for name in (
                    "external_id",
                    "name",
                    "source",
                    "source_url",
                    "license_name",
                    "dataset_version",
                )
            ],
            sa.Column("source_properties", JSONB(), nullable=False),
            sa.Column(
                "geometry", Geometry("GEOMETRY", srid=4326, spatial_index=False), nullable=False
            ),
            sa.Column(
                "imported_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint("source", "external_id", name=f"uq_{table}_source_external_id"),
            sa.CheckConstraint("source IN ('gem', 'phivolcs')", name=f"ck_{table}_source"),
            sa.CheckConstraint(
                f"GeometryType(geometry) IN ({types}) AND ST_IsValid(geometry) "
                "AND NOT ST_IsEmpty(geometry)",
                name=f"ck_{table}_geometry",
            ),
        )
        op.create_index(f"idx_{table}_geometry", table, ["geometry"], postgresql_using="gist")


def downgrade() -> None:
    for table in ("volcano_zones", "fault_lines"):
        op.drop_index(f"idx_{table}_geometry", table_name=table)
        op.drop_table(table)
