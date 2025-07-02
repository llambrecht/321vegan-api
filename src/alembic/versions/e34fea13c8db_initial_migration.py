"""Initial migration, Create products and brands table

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
    # Create brand table
    op.create_table('brands',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('biodynamic', sa.Boolean(), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['brands.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_brands_id'), 'brands', ['id'], unique=False)
    # Create product table
    op.create_table('products',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('ean', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('problem_description', sa.Text(), nullable=True),
    sa.Column('brand_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('VEGAN', 'NON_VEGAN', 'MAYBE_VEGAN', 'NOT_FOUND', name='productstatus'), nullable=True),
    sa.Column('state', sa.Enum('CREATED', 'NEED_CONTACT', 'WAITING_REPLY', 'NOT_FOUND', 'WAITING_PUBLISH', 'PUBLISHED', name='productstate'), nullable=True),
    sa.Column('created_from_off', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_id'), 'products', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_products_id'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_brands_id'), table_name='brands')
    op.drop_table('brands')