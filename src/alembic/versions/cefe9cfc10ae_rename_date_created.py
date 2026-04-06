"""rename date created

Revision ID: cefe9cfc10ae
Revises: 394144a22c93
Create Date: 2026-04-06 16:14:28.997797

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'cefe9cfc10ae'
down_revision: Union[str, None] = '394144a22c93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('product_not_found_reports', 'date_created', new_column_name='created_at')
    op.drop_index('ix_product_not_found_reports_date_created', table_name='product_not_found_reports')
    op.create_index(op.f('ix_product_not_found_reports_created_at'), 'product_not_found_reports', ['created_at'], unique=False)

    op.alter_column('scan_events', 'date_created', new_column_name='created_at')

    op.alter_column('shop_reviews', 'date_created', new_column_name='created_at')
    op.drop_index('ix_shop_reviews_date_created', table_name='shop_reviews')
    op.create_index(op.f('ix_shop_reviews_created_at'), 'shop_reviews', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('shop_reviews', 'created_at', new_column_name='date_created')
    op.drop_index('ix_shop_reviews_created_at', table_name='shop_reviews')
    op.create_index(op.f('ix_shop_reviews_date_created'), 'shop_reviews', ['date_created'], unique=False)

    op.alter_column('scan_events', 'created_at', new_column_name='date_created')

    op.alter_column('product_not_found_reports', 'created_at', new_column_name='date_created')
    op.drop_index('ix_product_not_found_reports_created_at', table_name='product_not_found_reports')
    op.create_index(op.f('ix_product_not_found_reports_date_created'), 'product_not_found_reports', ['date_created'], unique=False)
