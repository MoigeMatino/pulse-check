from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"


class CheckType(str, Enum):
    HTTP = "http"
    PING = "ping"


class User(SQLModel, table=True):
    id: UUID = Field(default_factory=lambda: uuid4(), primary_key=True)
    email: str = Field(..., unique=True, nullable=False)
    password_hash: str = Field(...)
    is_active: bool = Field(default=True)
    slack_webhook: str | None = Field(default=None)
    phone_number: str | None = Field(default=None)
    websites: List["Website"] = Relationship(back_populates="user")
    notification_preferences: List["NotificationPreference"] = Relationship(
        back_populates="user"
    )
    refresh_tokens: list["RefreshToken"] = Relationship(back_populates="user")


class Website(SQLModel, table=True):
    id: UUID = Field(default_factory=lambda: uuid4(), primary_key=True)
    user_id: UUID = Field(..., foreign_key="user.id", index=True)
    url: str = Field(
        ..., nullable=False, index=True
    )  # TODO: need to add unique constraint
    name: str = Field(
        ..., nullable=False, index=True
    )  # human readable name for website
    # uptime_check_interval: int = Field(default=300)  # on pause until we introduce
    # tiered offerings, for now we take a 'determined-by-us' approach
    is_active: bool = Field(
        default=True
    )  # boolean flag to enable/ disable monitoring for website
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )  # when website was created
    ssl_check_enabled: bool = Field(
        default=True
    )  # boolean flag to enable/ disable ssl checks
    ssl_expiry_date: datetime | None = Field(
        default=None, index=True
    )  # stores ssl expiry date; to be update during ssl checks
    ssl_last_checked: datetime | None = Field(
        default=None
    )  # tracks last time ssl status was checked; to be update during ssl checks
    warning_threshold_days: int = Field(
        default=30
    )  # configurable number of days for warning on ssl expiry
    uptime_last_checked: datetime | None = Field(default=None)
    check_type: Optional[CheckType] = Field(
        default=CheckType.HTTP
    )  # type of check to perform (HTTP, PING, etc.)
    user: User | None = Relationship(back_populates="websites")


class NotificationPreference(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: UUID = Field(..., foreign_key="user.id")
    notification_type: NotificationType
    is_enabled: bool = Field(default=True)
    threshold_minutes: int = Field(default=5)  # alert after X minutes of downtime

    user: Optional[User] = Relationship(back_populates="notification_preferences")


class UptimeLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    # TODO: add index to website_id and timestamp
    website_id: UUID = Field(..., foreign_key="website.id")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_up: bool
    response_time: int | None  # milliseconds
    status_code: int | None
    error_message: str | None


class SSLLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    website_id: UUID = Field(..., foreign_key="website.id")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime  # Expiry date of the SSL certificate
    issuer: str | None = None  # Certificate issuer (e.g., "Let's Encrypt") or None
    is_valid: bool  # Whether the certificate is valid
    error: str | None = None  # Store error messages if the check fails


class RefreshToken(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    token_hash: str = Field(max_length=128, index=True)  # Hashed token
    expires_at: datetime
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: Optional[User] = Relationship(back_populates="refresh_tokens")
