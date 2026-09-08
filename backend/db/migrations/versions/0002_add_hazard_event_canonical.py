"""add canonical identity columns to hazard_events

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("hazard_events", sa.Column("canonical_id", UUID(as_uuid=True), nullable=True))
    op.add_column("hazard_events", sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("hazard_events", sa.Column("match_confidence", sa.Float(), nullable=True))

    op.execute(
        "UPDATE hazard_events SET canonical_id = id, is_primary = true WHERE canonical_id IS NULL OR is_primary IS NULL"
    )

    op.alter_column("hazard_events", "is_primary", server_default=None)
    op.create_index(
        "idx_hazard_events_canonical",
        "hazard_events",
        ["canonical_id", "is_primary"],
    )


def downgrade() -> None:
    op.drop_index("idx_hazard_events_canonical", table_name="hazard_events")
    op.drop_column("hazard_events", "match_confidence")
    op.drop_column("hazard_events", "is_primary")
    op.drop_column("hazard_events", "canonical_id")
