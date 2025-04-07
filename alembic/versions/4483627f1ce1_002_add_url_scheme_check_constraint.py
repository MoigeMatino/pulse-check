"""002_add_url_scheme_check_constraint

Revision ID: 4483627f1ce1
Revises: 211f0fd1a2f2
Create Date: 2025-04-07 19:40:58.574978

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4483627f1ce1"
down_revision: Union[str, None] = "211f0fd1a2f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Data migration: Prepend 'https://' to already existing URLs without a scheme
    op.execute(
        """
        UPDATE website
        SET url = 'https://' || url
        WHERE url NOT LIKE 'http://%' AND url NOT LIKE 'https://%'
    """
    )

    # Schema migration: Add CHECK constraint to enforce schemes
    op.execute(
        """
        ALTER TABLE website
        ADD CONSTRAINT check_url_scheme
        CHECK (url LIKE 'http://%' OR url LIKE 'https://%')
    """
    )


def downgrade() -> None:
    # Remove the CHECK constraint
    op.execute("ALTER TABLE website DROP CONSTRAINT check_url_scheme")
