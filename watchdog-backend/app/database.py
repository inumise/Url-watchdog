from typing import Optional
from datetime import datetime
from app.models import User, Monitor, NotificationChannel, CheckLog


class InMemoryDatabase:
    def __init__(self):
        self.users: dict[str, User] = {}
        self.users_by_email: dict[str, str] = {}
        self.monitors: dict[str, Monitor] = {}
        self.notification_channels: dict[str, NotificationChannel] = {}
        self.check_logs: dict[str, CheckLog] = {}
    
    def create_user(self, user: User) -> User:
        self.users[user.id] = user
        self.users_by_email[user.email.lower()] = user.id
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        return self.users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        user_id = self.users_by_email.get(email.lower())
        if user_id:
            return self.users.get(user_id)
        return None
    
    def update_user(self, user: User) -> User:
        self.users[user.id] = user
        return user
    
    def create_monitor(self, monitor: Monitor) -> Monitor:
        self.monitors[monitor.id] = monitor
        return monitor
    
    def get_monitor_by_id(self, monitor_id: str) -> Optional[Monitor]:
        return self.monitors.get(monitor_id)
    
    def get_monitors_by_user(self, user_id: str) -> list[Monitor]:
        return [m for m in self.monitors.values() if m.user_id == user_id]
    
    def get_all_active_monitors(self) -> list[Monitor]:
        return [m for m in self.monitors.values() if m.is_active]
    
    def update_monitor(self, monitor: Monitor) -> Monitor:
        self.monitors[monitor.id] = monitor
        return monitor
    
    def delete_monitor(self, monitor_id: str) -> bool:
        if monitor_id in self.monitors:
            del self.monitors[monitor_id]
            return True
        return False
    
    def create_notification_channel(self, channel: NotificationChannel) -> NotificationChannel:
        self.notification_channels[channel.id] = channel
        return channel
    
    def get_notification_channel_by_id(self, channel_id: str) -> Optional[NotificationChannel]:
        return self.notification_channels.get(channel_id)
    
    def get_notification_channels_by_user(self, user_id: str) -> list[NotificationChannel]:
        return [c for c in self.notification_channels.values() if c.user_id == user_id]
    
    def update_notification_channel(self, channel: NotificationChannel) -> NotificationChannel:
        self.notification_channels[channel.id] = channel
        return channel
    
    def delete_notification_channel(self, channel_id: str) -> bool:
        if channel_id in self.notification_channels:
            del self.notification_channels[channel_id]
            return True
        return False
    
    def create_check_log(self, log: CheckLog) -> CheckLog:
        self.check_logs[log.id] = log
        return log
    
    def get_check_logs_by_monitor(self, monitor_id: str, limit: int = 50) -> list[CheckLog]:
        logs = [l for l in self.check_logs.values() if l.monitor_id == monitor_id]
        logs.sort(key=lambda x: x.checked_at, reverse=True)
        return logs[:limit]


db = InMemoryDatabase()
