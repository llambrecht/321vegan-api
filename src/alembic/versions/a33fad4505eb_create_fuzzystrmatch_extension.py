"""Create fuzzystrmatch extension 

Revision ID: a33fad4505eb
Revises: 0a2cb99fef78
Create Date: 2025-08-08 21:25:35.469988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'a33fad4505eb'
down_revision: Union[str, None] = '0a2cb99fef78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands to create fuzzystrmatch extension ###
    op.execute(text("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;"))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands to remove fuzzystrmatch extension ###
    op.execute(text("DROP EXTENSION IF EXISTS fuzzystrmatch;"))
    # ### end Alembic commands ###
