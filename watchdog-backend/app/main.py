from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Optional
import os

from dotenv import load_dotenv
load_dotenv()

from app.database import db
from app.models import User, Monitor, NotificationChannel
from app.auth import (
    UserCreate, UserLogin, Token, UserResponse,
    get_current_user, register_user, authenticate_user,
    create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.schemas import (
    MonitorCreate, MonitorUpdate, MonitorResponse,
    NotificationChannelCreate, NotificationChannelUpdate, NotificationChannelResponse,
    CheckLogResponse, CheckoutSessionRequest, BillingPortalRequest, mask_config
)
from app.scheduler import start_scheduler, stop_scheduler, trigger_immediate_check
from app.stripe_service import create_checkout_session, handle_webhook_event, create_billing_portal_session
from app.url_fetcher import validate_url


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    user = register_user(user_data.email, user_data.password)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    user = authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        subscription_status=current_user.subscription_status,
        created_at=current_user.created_at
    )


@app.post("/api/monitors", response_model=MonitorResponse)
async def create_monitor(
    monitor_data: MonitorCreate,
    current_user: User = Depends(get_current_user)
):
    is_valid, error_msg = validate_url(monitor_data.url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    if monitor_data.check_frequency < 1 or monitor_data.check_frequency > 24:
        raise HTTPException(status_code=400, detail="Check frequency must be between 1 and 24 times per day")
    
    user_monitors = db.get_monitors_by_user(current_user.id)
    max_monitors = 3 if current_user.subscription_status == "free" else 100
    if len(user_monitors) >= max_monitors:
        raise HTTPException(
            status_code=403,
            detail=f"Monitor limit reached ({max_monitors}). Upgrade to Pro for more monitors."
        )
    
    monitor = Monitor(
        id=Monitor.generate_id(),
        user_id=current_user.id,
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
async def list_monitors(current_user: User = Depends(get_current_user)):
    monitors = db.get_monitors_by_user(current_user.id)
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
async def get_monitor(monitor_id: str, current_user: User = Depends(get_current_user)):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor or monitor.user_id != current_user.id:
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
async def update_monitor(
    monitor_id: str,
    monitor_data: MonitorUpdate,
    current_user: User = Depends(get_current_user)
):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor or monitor.user_id != current_user.id:
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
async def delete_monitor(monitor_id: str, current_user: User = Depends(get_current_user)):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor or monitor.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    db.delete_monitor(monitor_id)
    return {"message": "Monitor deleted"}


@app.post("/api/monitors/{monitor_id}/check")
async def trigger_check(
    monitor_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor or monitor.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    background_tasks.add_task(trigger_immediate_check, monitor_id)
    return {"message": "Check triggered"}


@app.get("/api/monitors/{monitor_id}/logs", response_model=list[CheckLogResponse])
async def get_monitor_logs(monitor_id: str, current_user: User = Depends(get_current_user)):
    monitor = db.get_monitor_by_id(monitor_id)
    if not monitor or monitor.user_id != current_user.id:
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
async def create_notification_channel(
    channel_data: NotificationChannelCreate,
    current_user: User = Depends(get_current_user)
):
    channel = NotificationChannel(
        id=NotificationChannel.generate_id(),
        user_id=current_user.id,
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
async def list_notification_channels(current_user: User = Depends(get_current_user)):
    channels = db.get_notification_channels_by_user(current_user.id)
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
async def update_notification_channel(
    channel_id: str,
    channel_data: NotificationChannelUpdate,
    current_user: User = Depends(get_current_user)
):
    channel = db.get_notification_channel_by_id(channel_id)
    if not channel or channel.user_id != current_user.id:
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
async def delete_notification_channel(channel_id: str, current_user: User = Depends(get_current_user)):
    channel = db.get_notification_channel_by_id(channel_id)
    if not channel or channel.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    
    db.delete_notification_channel(channel_id)
    return {"message": "Notification channel deleted"}


@app.post("/api/billing/checkout")
async def create_checkout(
    request: CheckoutSessionRequest,
    current_user: User = Depends(get_current_user)
):
    checkout_url = create_checkout_session(
        current_user,
        request.success_url,
        request.cancel_url
    )
    
    if not checkout_url:
        raise HTTPException(
            status_code=503,
            detail="Payment service not configured. Contact support."
        )
    
    return {"checkout_url": checkout_url}


@app.post("/api/billing/portal")
async def create_portal(
    request: BillingPortalRequest,
    current_user: User = Depends(get_current_user)
):
    portal_url = create_billing_portal_session(current_user, request.return_url)
    
    if not portal_url:
        raise HTTPException(
            status_code=400,
            detail="No active subscription found"
        )
    
    return {"portal_url": portal_url}


@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    if not webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured")
    
    success = handle_webhook_event(payload, sig_header, webhook_secret)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid webhook")
    
    return {"received": True}
