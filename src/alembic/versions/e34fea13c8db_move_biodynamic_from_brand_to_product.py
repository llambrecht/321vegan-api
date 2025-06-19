"""Move biodynamic from brand to product

Revision ID: e34fea13c8db
Revises: 
Create Date: 2025-06-19 08:26:20.118372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e34fea13c8db'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Remove 'biodynamic' from brands
    op.drop_column('brands', 'biodynamic')
    # Add 'biodynamic' to products
    op.add_column('products', sa.Column('biodynamic', sa.Boolean(), nullable=True))

def downgrade() -> None:
    # Add 'biodynamic' back to brands
    op.add_column('brands', sa.Column('biodynamic', sa.Boolean(), nullable=True))
    # Remove 'biodynamic' from products
    op.drop_column('products', 'biodynamic')
