"""add_brand_name_to_product

Revision ID: ca2d98ff242e
Revises: 3e484d8e1128
Create Date: 2025-07-13 18:54:44.803147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca2d98ff242e'
down_revision: Union[str, None] = '3e484d8e1128'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('products', sa.Column('brand_name', sa.String(), nullable=True))
    
    op.create_index(op.f('ix_products_brand_name'), 'products', ['brand_name'], unique=False)



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_products_brand_name'), table_name='products')
    op.drop_column('products', 'brand_name')