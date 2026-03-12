"""add pause event

Revision ID: edc5cba73e76
Revises: a47385897873
Create Date: 2026-03-12 10:57:39.556926

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'edc5cba73e76'
down_revision: Union[str, None] = 'a47385897873'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    ctx = op.get_context()
    with ctx.autocommit_block():
        op.execute("ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'PAUSED'")
        op.execute("ALTER TYPE subscriptioneventtype ADD VALUE IF NOT EXISTS 'PAUSED'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; no-op
    pass
