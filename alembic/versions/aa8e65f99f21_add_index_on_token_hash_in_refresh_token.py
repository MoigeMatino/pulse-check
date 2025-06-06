"""Add index on token_hash in refresh_token

Revision ID: aa8e65f99f21
Revises: e144f85350b1
Create Date: 2025-05-28 13:24:40.934605

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aa8e65f99f21"
down_revision: Union[str, None] = "e144f85350b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(
        op.f("ix_refreshtoken_token_hash"), "refreshtoken", ["token_hash"], unique=False
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_refreshtoken_token_hash"), table_name="refreshtoken")
    # ### end Alembic commands ###
