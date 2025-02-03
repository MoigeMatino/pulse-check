from sqlmodel import SQLModel, Field, Relationship
from typing import List
from uuid import uuid4
from enum import Enum
from datetime import datetime, timezone

class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"

class User(SQLModel, table=True):
    id: str | None = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    email: str = Field(..., unique=True, nullable=False)
    slack_webhook: str | None = Field(default=None)
    phone_number: str | None = Field(default=None)
    websites: List["Website"] = Relationship(back_populates="user")
    notification_preferences: List["NotificationPreference"] = Relationship(back_populates="user")


class Website(SQLModel, table=True):
    id: str | None = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: str = Field(..., foreign_key="user.id")
    url: str = Field(..., nullable=False)
    name: str = Field(..., nullable=False) # human readable name for website
    uptime_check_interval: int = Field(default=300)  # seconds
    is_active: bool = Field(default=True) # boolean flag to enable/ disable monitoring for website
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # when website was created
    ssl_check_enabled: bool = Field(default=True) # boolean flag to enable/ disable ssl checks
    ssl_expiry_date: datetime | None = Field(default=None) # stores ssl expiry date; to be update during ssl checks
    ssl_last_checked: datetime | None = Field(default=None) # tracks last time ssl status was checked; to be update during ssl checks
    warning_threshold_days: int = Field(default=30) # configurable number of days for warning on ssl expiry
    user: User | None = Relationship(back_populates="websites")

class NotificationPreference(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(..., foreign_key="user.id")
    notification_type: NotificationType
    is_enabled: bool = Field(default=True)
    threshold_minutes: int = Field(default=5) # alert after X minutes of downtime

class UptimeLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    website_id: str = Field(..., foreign_key="website.id")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_up: bool
    response_time: int | None  # milliseconds
    status_code: int | None
    error_message: str | None

class SSLLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    website_id: str = Field(..., foreign_key="website.id")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime
    issuer: str | None
    is_valid: bool
