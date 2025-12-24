from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from app.models import NotificationChannelType


class MonitorCreate(BaseModel):
    name: str
    url: str
    keywords: list[str]
    check_frequency: int


class MonitorUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    keywords: Optional[list[str]] = None
    check_frequency: Optional[int] = None
    is_active: Optional[bool] = None


class MonitorResponse(BaseModel):
    id: str
    name: str
    url: str
    keywords: list[str]
    check_frequency: int
    is_active: bool
    created_at: datetime
    last_checked: Optional[datetime]
    last_result: Optional[str]
    last_match_found: bool


class NotificationChannelCreate(BaseModel):
    name: str
    channel_type: NotificationChannelType
    config: dict


class NotificationChannelUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class NotificationChannelResponse(BaseModel):
    id: str
    name: str
    channel_type: NotificationChannelType
    is_active: bool
    created_at: datetime
    config_masked: dict


class CheckLogResponse(BaseModel):
    id: str
    monitor_id: str
    checked_at: datetime
    success: bool
    match_found: bool
    matched_keywords: list[str]
    error_message: Optional[str]


class CheckoutSessionRequest(BaseModel):
    success_url: str
    cancel_url: str


class BillingPortalRequest(BaseModel):
    return_url: str


def mask_config(config: dict) -> dict:
    masked = {}
    sensitive_keys = ["password", "token", "secret", "api_key", "smtp_password", "bot_token"]
    
    for key, value in config.items():
        if any(s in key.lower() for s in sensitive_keys):
            if isinstance(value, str) and len(value) > 4:
                masked[key] = value[:2] + "*" * (len(value) - 4) + value[-2:]
            else:
                masked[key] = "****"
        else:
            masked[key] = value
    
    return masked
