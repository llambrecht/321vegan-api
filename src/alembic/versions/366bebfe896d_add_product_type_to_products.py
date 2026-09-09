"""add product_type to products

Revision ID: 366bebfe896d
Revises: 4e9e3e5878d1
Create Date: 2026-09-09 07:50:29.034046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '366bebfe896d'
down_revision: Union[str, None] = '4e9e3e5878d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


product_type_enum = sa.Enum('FOOD', 'COSMETIC', 'HOUSEHOLD', name='producttype')


def upgrade() -> None:
    """Upgrade schema."""
    # add_column does not auto-create the enum type on PostgreSQL - do it here.
    product_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column('products', sa.Column('product_type', product_type_enum, server_default='FOOD', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('products', 'product_type')
    product_type_enum.drop(op.get_bind(), checkfirst=True)
