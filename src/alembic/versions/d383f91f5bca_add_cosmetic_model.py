"""Add cosmetic model

Revision ID: d383f91f5bca
Revises: ce21aae61203
Create Date: 2025-07-12 13:47:05.188081

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd383f91f5bca'
down_revision: Union[str, None] = 'ce21aae61203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'cosmetics',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False, default=datetime.now),
        sa.Column('updated_at', sa.DateTime, nullable=False, default=datetime.now),
        sa.Column('brand_name', sa.String, nullable=False),
        sa.Column('is_vegan', sa.Boolean, nullable=False, default=False),
        sa.Column('is_cruelty_free', sa.Boolean, nullable=False, default=False),
        sa.Column('description', sa.Text),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('cosmetics')
