from datetime import datetime
from enum import Enum
from re import fullmatch
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl, field_validator


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"


class UserBase(BaseModel):
    email: EmailStr
    slack_webhook: str | None
    phone_number: str | None


# Request and Response Schemas
class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def validate_password(cls, value: Optional[str]) -> Optional[str]:
        if value and (
            len(value) < 8
            or not fullmatch(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", value)
        ):
            raise ValueError(
                "Password must be at least 8 characters, with uppercase, lowercase, \n"
                "and digits"
            )
        return value

    @field_validator("phone_number")
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value and not fullmatch(r"^\+\d{10,15}$", value):
            raise ValueError("Phone number must be in format +1234567890")
        return value


class UserRead(UserBase):
    id: UUID
    is_active: bool = True

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    slack_webhook: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("is_active", mode="before")
    def normalize_bool(cls, v):
        """Convert int (0/1) to bool if needed"""
        return bool(v) if isinstance(v, int) else v

    @field_validator("password")
    def validate_password(cls, value: Optional[str]) -> Optional[str]:
        if value and (
            len(value) < 8
            or not fullmatch(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", value)
        ):
            raise ValueError(
                "Password must be at least 8 characters, with uppercase, lowercase,\n"
                "and digits"
            )
        return value

    @field_validator("phone_number")
    def validate_phone_number(cls, value: Optional[str]) -> Optional[str]:
        if value and not fullmatch(r"^\+\d{10,15}$", value):
            raise ValueError("Phone number must be in format +1234567890")
        return value


class WebsiteBase(BaseModel):
    user_id: UUID
    url: str  # Base has str, not HttpUrl, for DB compatibility
    name: str
    check_interval: Optional[int] = 300  # Default 5 minutes (300 seconds)
    is_active: Union[int, bool] = True  # Accept int or bool, normalize later
    ssl_check_enabled: Union[int, bool] = True

    @field_validator("is_active", "ssl_check_enabled", mode="before")
    def normalize_bool(cls, v):
        """Convert int (0/1) to bool if needed"""
        return bool(v) if isinstance(v, int) else v


class WebsiteCreate(WebsiteBase):
    url: HttpUrl


class WebsiteRead(WebsiteBase):
    id: UUID
    created_at: datetime
    ssl_expiry_date: Optional[datetime]
    ssl_last_checked: Optional[datetime]
    warning_threshold_days: int
    uptime_last_checked: Optional[datetime]

    class Config:
        from_attributes = True


class PaginatedWebsiteReadResponse(BaseModel):
    data: List[WebsiteRead]
    next_cursor: Optional[str] = None
    has_next: bool = False  # More logs available?


class WebsiteUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    name: Optional[str] = None
    # check_interval: Optional[int] = None # on pause until we introduce
    # tiered offerings, for now we take a 'determined-by-us' approach
    is_active: Optional[Union[int, bool]] = None
    ssl_check_enabled: Optional[Union[int, bool]] = None

    @field_validator("is_active", "ssl_check_enabled", mode="before")
    def normalize_bool(cls, v):
        return bool(v) if isinstance(v, int) else v


class WebsiteSearchResponse(BaseModel):
    data: List[WebsiteRead]
    next_cursor: Optional[str] = None  # Using id as cursor
    has_next: bool = False


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
    website_id: UUID
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
    has_next: bool = False


class UptimeLogResponse(BaseModel):
    id: int
    website_id: UUID
    timestamp: datetime
    is_up: bool
    status_code: Optional[int]
    response_time: Optional[float]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class PaginatedUptimeLogResponse(BaseModel):
    data: List[UptimeLogResponse]
    next_cursor: Optional[datetime] = None
    has_next: bool = False  # More logs available?
