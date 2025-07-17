"""001_create_initial_schema.py

Revision ID: 211f0fd1a2f2
Revises:
Create Date: 2025-04-06 10:36:47.874158
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID

from alembic import op

# Revision identifiers
revision: str = "211f0fd1a2f2"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Enable uuid-ossp extension for uuid_generate_v4()
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # User table
    op.create_table(
        "user",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("slack_webhook", sa.String(), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Website table
    op.create_table(
        "website",
        sa.Column(
            "id",
            UUID(as_uuid=False),
            nullable=False,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("user_id", UUID(as_uuid=False), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "ssl_check_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("ssl_expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ssl_last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "warning_threshold_days", sa.Integer(), nullable=False, server_default="30"
        ),
        sa.Column("uptime_last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.Index("ix_website_url", "url"),
        sa.Index("ix_website_user_id", "user_id"),
        sa.Index("ix_website_ssl_expiry_date", "ssl_expiry_date"),
    )

    # Notification Preference table
    op.create_table(
        "notificationpreference",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", UUID(as_uuid=False), nullable=False),
        sa.Column(
            "notification_type",
            ENUM("email", "sms", "slack", name="notificationtype"),
            nullable=False,
        ),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "threshold_minutes", sa.Integer(), nullable=False, server_default="5"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )

    # Uptime Log table
    op.create_table(
        "uptimelog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("website_id", UUID(as_uuid=False), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("is_up", sa.Boolean(), nullable=False),
        sa.Column("response_time", sa.Integer(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["website_id"], ["website.id"]),
    )

    # SSL Log table
    op.create_table(
        "ssllog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("website_id", UUID(as_uuid=False), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issuer", sa.String(), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["website_id"], ["website.id"]),
    )


def downgrade():
    op.drop_table("ssllog")
    op.drop_table("uptimelog")
    op.drop_table("notificationpreference")
    op.drop_table("website")
    op.drop_table("user")
    op.execute("DROP TYPE IF EXISTS notificationtype")
