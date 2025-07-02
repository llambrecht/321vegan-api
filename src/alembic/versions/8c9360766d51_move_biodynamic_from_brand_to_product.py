"""Move biodynamic from brand to product 

Revision ID: 8c9360766d51
Revises: e34fea13c8db
Create Date: 2025-06-28 14:18:15.809257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8c9360766d51'
down_revision: Union[str, None] = 'e34fea13c8db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remove 'biodynamic' from brands
    op.drop_column('brands', 'biodynamic')
    # Add 'biodynamic' to products
    op.add_column('products', sa.Column('biodynamic', sa.Boolean(), nullable=True))



def downgrade() -> None:
    """Downgrade schema."""
    # Add 'biodynamic' back to brands
    op.add_column('brands', sa.Column('biodynamic', sa.Boolean(), nullable=True))
    # Remove 'biodynamic' from products
    op.drop_column('products', 'biodynamic')
    # ### end Alembic commands ###
