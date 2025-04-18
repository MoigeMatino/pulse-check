"""Add index to name field of Website table
and update timestamps to use timezone-aware datetime

Revision ID: 8c1c3ea7c65d
Revises: 4483627f1ce1
Create Date: 2025-04-12 09:12:08.694941

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c1c3ea7c65d"
down_revision: Union[str, None] = "4483627f1ce1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "ssllog",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "ssllog",
        "valid_until",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        "uptimelog",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )

    op.alter_column(
        "website",
        "created_at",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "website",
        "ssl_expiry_date",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "website",
        "ssl_last_checked",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "website",
        "uptime_last_checked",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
    )
    op.create_index(op.f("ix_website_name"), "website", ["name"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_website_name"), table_name="website")
    op.alter_column(
        "website",
        "uptime_last_checked",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "website",
        "ssl_last_checked",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "website",
        "ssl_expiry_date",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=True,
    )
    op.alter_column(
        "website",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "uptimelog",
        "timestamp",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
    op.alter_column(
        "ssllog",
        "valid_until",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
    )
    op.alter_column(
        "ssllog",
        "timestamp",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
    )
    # ### end Alembic commands ###
