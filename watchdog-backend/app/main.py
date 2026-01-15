from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# Path to frontend build directory
STATIC_DIR = Path(__file__).parent.parent / "static"

from app.database import db
from app.models import User, Monitor, NotificationChannel
from app.schemas import (
    MonitorCreate, MonitorUpdate, MonitorResponse,
    NotificationChannelCreate, NotificationChannelUpdate, NotificationChannelResponse,
    CheckLogResponse, mask_config
)
from app.scheduler import start_scheduler, stop_scheduler, trigger_immediate_check
from app.url_fetcher import validate_url

# Default anonymous user ID for no-auth mode
ANON_USER_ID = "anonymous"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create anonymous user if not exists
    if not db.get_user_by_id(ANON_USER_ID):
        anon_user = User(id=ANON_USER_ID, email="anonymous@local", password_hash="")
        db.create_user(anon_user)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="URL Watchdog API", lifespan=lifespan)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/api/monitors", response_model=MonitorResponse)
async def create_monitor(monitor_data: MonitorCreate):
    is_valid, error_msg = validate_url(monitor_data.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    if monitor_data.check_frequency < 1 or monitor_data.check_frequency > 24:
        raise HTTPException(status_code=400, detail="Check frequency must be between 1 and 24 times per day")
    
    monitor = Monitor(
        id=Monitor.generate_id(),
        user_id=ANON_USER_ID,
        name=monitor_data.name,
        url=monitor_data.url,
        keywords=monitor_data.keywords,
        check_frequency=monitor_data.check_frequency
    )
    db.create_monitor(monitor)
    
    return MonitorResponse(
        id=monitor.id,
        name=monitor.name,
        url=monitor.url,
        keywords=monitor.keywords,
        check_frequency=monitor.check_frequency,
        is_active=monitor.is_active,
        created_at=monitor.created_at,
        last_checked=monitor.last_checked,
        last_result=monitor.last_result,
        last_match_found=monitor.last_match_found
    )


@app.get("/api/monitors", response_model=list[MonitorResponse])
async def list_monitors():
    monitors = db.get_monitors_by_user(ANON_USER_ID)
    return [
        MonitorResponse(
            id=m.id,
            name=m.name,
            url=m.url,
            keywords=m.keywords,
            check_frequency=m.check_frequency,
            is_active=m.is_active,
            created_at=m.created_at,
            last_checked=m.last_checked,
            last_result=m.last_result,
            last_match_found=m.last_match_found
        )
        for m in monitors
    ]


@app.get("/api/monitors/{monitor_id}", response_model=MonitorResponse)
async def get_monitor(monitor_id: str):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    return MonitorResponse(
        id=monitor.id,
        name=monitor.name,
        url=monitor.url,
        keywords=monitor.keywords,
        check_frequency=monitor.check_frequency,
        is_active=monitor.is_active,
        created_at=monitor.created_at,
        last_checked=monitor.last_checked,
        last_result=monitor.last_result,
        last_match_found=monitor.last_match_found
    )


@app.put("/api/monitors/{monitor_id}", response_model=MonitorResponse)
async def update_monitor(monitor_id: str, monitor_data: MonitorUpdate):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    if monitor_data.url is not None:
        is_valid, error_msg = validate_url(monitor_data.url)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        monitor.url = monitor_data.url
    
    if monitor_data.name is not None:
        monitor.name = monitor_data.name
    if monitor_data.keywords is not None:
        monitor.keywords = monitor_data.keywords
    if monitor_data.check_frequency is not None:
        if monitor_data.check_frequency < 1 or monitor_data.check_frequency > 24:
            raise HTTPException(status_code=400, detail="Check frequency must be between 1 and 24 times per day")
        monitor.check_frequency = monitor_data.check_frequency
    if monitor_data.is_active is not None:
        monitor.is_active = monitor_data.is_active
    
    db.update_monitor(monitor)
    
    return MonitorResponse(
        id=monitor.id,
        name=monitor.name,
        url=monitor.url,
        keywords=monitor.keywords,
        check_frequency=monitor.check_frequency,
        is_active=monitor.is_active,
        created_at=monitor.created_at,
        last_checked=monitor.last_checked,
        last_result=monitor.last_result,
        last_match_found=monitor.last_match_found
    )


@app.delete("/api/monitors/{monitor_id}")
async def delete_monitor(monitor_id: str):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    db.delete_monitor(monitor_id)
    return {"message": "Monitor deleted"}


@app.post("/api/monitors/{monitor_id}/check")
async def trigger_check(monitor_id: str, background_tasks: BackgroundTasks):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    background_tasks.add_task(trigger_immediate_check, monitor_id)
    return {"message": "Check triggered"}


@app.get("/api/monitors/{monitor_id}/logs", response_model=list[CheckLogResponse])
async def get_monitor_logs(monitor_id: str):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    logs = db.get_check_logs_by_monitor(monitor_id)
    return [
        CheckLogResponse(
            id=log.id,
            monitor_id=log.monitor_id,
            checked_at=log.checked_at,
            success=log.success,
            match_found=log.match_found,
            matched_keywords=log.matched_keywords,
            error_message=log.error_message
        )
        for log in logs
    ]


@app.post("/api/notifications", response_model=NotificationChannelResponse)
async def create_notification_channel(channel_data: NotificationChannelCreate):
    channel = NotificationChannel(
        id=NotificationChannel.generate_id(),
        user_id=ANON_USER_ID,
        name=channel_data.name,
        channel_type=channel_data.channel_type,
        config=channel_data.config
    )
    db.create_notification_channel(channel)
    
    return NotificationChannelResponse(
        id=channel.id,
        name=channel.name,
        channel_type=channel.channel_type,
        is_active=channel.is_active,
        created_at=channel.created_at,
        config_masked=mask_config(channel.config)
    )


@app.get("/api/notifications", response_model=list[NotificationChannelResponse])
async def list_notification_channels():
    channels = db.get_notification_channels_by_user(ANON_USER_ID)
    return [
        NotificationChannelResponse(
            id=c.id,
            name=c.name,
            channel_type=c.channel_type,
            is_active=c.is_active,
            created_at=c.created_at,
            config_masked=mask_config(c.config)
        )
        for c in channels
    ]


@app.put("/api/notifications/{channel_id}", response_model=NotificationChannelResponse)
async def update_notification_channel(channel_id: str, channel_data: NotificationChannelUpdate):
    channel = db.get_notification_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    
    if channel_data.name is not None:
        channel.name = channel_data.name
    if channel_data.config is not None:
        channel.config = channel_data.config
    if channel_data.is_active is not None:
        channel.is_active = channel_data.is_active
    
    db.update_notification_channel(channel)
    
    return NotificationChannelResponse(
        id=channel.id,
        name=channel.name,
        channel_type=channel.channel_type,
        is_active=channel.is_active,
        created_at=channel.created_at,
        config_masked=mask_config(channel.config)
    )


@app.delete("/api/notifications/{channel_id}")
async def delete_notification_channel(channel_id: str):
    channel = db.get_notification_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    
    db.delete_notification_channel(channel_id)
    return {"message": "Notification channel deleted"}




# Serve static files from frontend build
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the React SPA for all non-API routes"""
        # Check if it's a static file
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA routing
        return FileResponse(STATIC_DIR / "index.html")
