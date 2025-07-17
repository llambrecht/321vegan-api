"""create_signal_errors

Revision ID: 7055d8019d66
Revises: 1002cf2fbd60
Create Date: 2025-07-17 17:36:39.094443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7055d8019d66'
down_revision: Union[str, None] = '1002cf2fbd60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('error_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('ean', sa.String(), nullable=False),
    sa.Column('comment', sa.String(), nullable=False),
    sa.Column('contact', sa.String(), nullable=True),
    sa.Column('handled', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_error_reports_ean'), 'error_reports', ['ean'], unique=False)
    op.create_index(op.f('ix_error_reports_id'), 'error_reports', ['id'], unique=False)



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_error_reports_id'), table_name='error_reports')
    op.drop_index(op.f('ix_error_reports_ean'), table_name='error_reports')
    op.drop_table('error_reports')
