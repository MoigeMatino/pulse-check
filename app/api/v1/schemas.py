from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, HttpUrl


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"


# Request and Response Schemas
class UserCreate(BaseModel):
    email: EmailStr
    slack_webhook: str | None
    phone_number: str | None


class UserRead(BaseModel):
    id: str
    email: EmailStr
    slack_webhook: str | None
    phone_number: str | None

    class Config:
        from_attributes = True


class WebsiteCreate(BaseModel):
    url: HttpUrl
    name: str
    check_interval: int | None = 300
    is_active: int | bool = True
    ssl_check_enabled: int | bool = True


class WebsiteRead(BaseModel):
    id: str
    user_id: str
    url: HttpUrl
    name: str
    check_interval: int
    is_active: bool
    ssl_check_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SSLStatusResponse(BaseModel):
    valid: bool
    expiry_date: datetime | None = None
    days_remaining: int | None = None
    issuer: str | None = None
    needs_renewal: bool | None = None
    error: str | None = None

    class Config:
        from_attributes = True


class SSLLogResponse(BaseModel):
    id: int
    website_id: str
    valid_until: datetime | None = None
    issuer: str | None = None
    is_valid: bool
    error: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True


# New wrapper model for paginated response
class PaginatedSSLLogResponse(BaseModel):
    data: List[SSLLogResponse]
    next_cursor: Optional[int] = None
