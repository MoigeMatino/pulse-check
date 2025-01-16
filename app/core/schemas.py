from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum

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
        orm_mode = True

class WebsiteCreate(BaseModel):
    url: str
    name: str
    check_interval: int | None = 300
    is_active: int | bool = True
    ssl_check_enabled: int | bool = True

class WebsiteRead(BaseModel):
    id: str
    user_id: str
    url: str
    name: str
    check_interval: int
    is_active: bool
    ssl_check_enabled: bool
    created_at: datetime

    class Config:
        orm_mode = True
