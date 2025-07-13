"""add_unique_constraint_on_cosmetic_brand_name

Revision ID: 3e484d8e1128
Revises: 0e4cc90775e4
Create Date: 2025-07-13 12:37:02.463112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3e484d8e1128'
down_revision: Union[str, None] = 'd383f91f5bca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(op.f('ix_cosmetics_brand_name'), 'cosmetics', ['brand_name'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_cosmetics_brand_name'), table_name='cosmetics')
