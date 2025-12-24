from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class NotificationChannelType(str, Enum):
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


@dataclass
class User:
    id: str
    email: str
    password_hash: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    subscription_status: str = "free"
    stripe_customer_id: Optional[str] = None
    
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())


@dataclass
class Monitor:
    id: str
    user_id: str
    url: str
    keywords: list[str]
    check_frequency: int
    name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None
    last_result: Optional[str] = None
    last_match_found: bool = False
    
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())


@dataclass
class NotificationChannel:
    id: str
    user_id: str
    channel_type: NotificationChannelType
    name: str
    config: dict
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())


@dataclass
class CheckLog:
    id: str
    monitor_id: str
    checked_at: datetime
    success: bool
    match_found: bool
    matched_keywords: list[str]
    error_message: Optional[str] = None
    
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())
