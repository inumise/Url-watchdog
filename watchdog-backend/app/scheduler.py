import asyncio
from datetime import datetime, timedelta
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import db
from app.models import Monitor, CheckLog
from app.url_fetcher import fetch_url, check_keywords
from app.notifications import send_notification


scheduler: Optional[AsyncIOScheduler] = None


async def check_monitor(monitor_id: str):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor or not monitor.is_active:
        return
    
    success, message, content = await fetch_url(monitor.url)
    
    matched_keywords = []
    if success and content:
        matched_keywords = check_keywords(content, monitor.keywords)
    
    log = CheckLog(
        id=CheckLog.generate_id(),
        monitor_id=monitor.id,
        checked_at=datetime.utcnow(),
        success=success,
        match_found=len(matched_keywords) > 0,
        matched_keywords=matched_keywords,
        error_message=None if success else message
    )
    db.create_check_log(log)
    
    monitor.last_checked = datetime.utcnow()
    monitor.last_result = "success" if success else f"error: {message}"
    monitor.last_match_found = len(matched_keywords) > 0
    db.update_monitor(monitor)
    
    if matched_keywords:
        user_channels = db.get_notification_channels_by_user(monitor.user_id)
        active_channels = [c for c in user_channels if c.is_active]
        
        for channel in active_channels:
            try:
                await send_notification(channel, monitor, matched_keywords)
            except Exception as e:
                print(f"Notification error for channel {channel.id}: {e}")


async def run_all_checks():
    monitors = db.get_all_active_monitors()
    now = datetime.utcnow()
    
    for monitor in monitors:
        if monitor.last_checked is None:
            await check_monitor(monitor.id)
            continue
        
        interval_hours = 24 / monitor.check_frequency
        next_check = monitor.last_checked + timedelta(hours=interval_hours)
        
        if now >= next_check:
            await check_monitor(monitor.id)


def start_scheduler():
    global scheduler
    if scheduler is not None:
        return
    
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        run_all_checks,
        trigger=IntervalTrigger(minutes=5),
        id="check_all_monitors",
        name="Check all active monitors",
        replace_existing=True
    )
    
    scheduler.start()
    print("Scheduler started - checking monitors every 5 minutes")


def stop_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown()
        scheduler = None


async def trigger_immediate_check(monitor_id: str):
    await check_monitor(monitor_id)
