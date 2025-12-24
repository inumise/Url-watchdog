import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.models import NotificationChannel, NotificationChannelType, Monitor


async def send_notification(
    channel: NotificationChannel,
    monitor: Monitor,
    matched_keywords: list[str]
) -> tuple[bool, str]:
    if channel.channel_type == NotificationChannelType.EMAIL:
        return await send_email_notification(channel, monitor, matched_keywords)
    elif channel.channel_type == NotificationChannelType.TELEGRAM:
        return await send_telegram_notification(channel, monitor, matched_keywords)
    elif channel.channel_type == NotificationChannelType.WEBHOOK:
        return await send_webhook_notification(channel, monitor, matched_keywords)
    else:
        return False, f"Unknown channel type: {channel.channel_type}"


async def send_email_notification(
    channel: NotificationChannel,
    monitor: Monitor,
    matched_keywords: list[str]
) -> tuple[bool, str]:
    try:
        config = channel.config
        smtp_host = config.get("smtp_host", "smtp.gmail.com")
        smtp_port = int(config.get("smtp_port", 587))
        smtp_user = config.get("smtp_user")
        smtp_password = config.get("smtp_password")
        to_email = config.get("to_email")
        
        if not all([smtp_user, smtp_password, to_email]):
            return False, "Missing email configuration"
        
        subject = f"URL Watchdog Alert: {monitor.name}"
        body = f"""
URL Watchdog Alert

Monitor: {monitor.name}
URL: {monitor.url}
Matched Keywords: {', '.join(matched_keywords)}

This is an automated alert from URL Watchdog.
        """
        
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return True, "Email sent successfully"
    except Exception as e:
        return False, f"Email error: {str(e)}"


async def send_telegram_notification(
    channel: NotificationChannel,
    monitor: Monitor,
    matched_keywords: list[str]
) -> tuple[bool, str]:
    try:
        config = channel.config
        bot_token = config.get("bot_token")
        chat_id = config.get("chat_id")
        
        if not all([bot_token, chat_id]):
            return False, "Missing Telegram configuration"
        
        message = f"""
🔔 *URL Watchdog Alert*

*Monitor:* {monitor.name}
*URL:* {monitor.url}
*Matched Keywords:* {', '.join(matched_keywords)}
        """
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
            
            if response.status_code == 200:
                return True, "Telegram message sent"
            else:
                return False, f"Telegram API error: {response.text}"
                
    except Exception as e:
        return False, f"Telegram error: {str(e)}"


async def send_webhook_notification(
    channel: NotificationChannel,
    monitor: Monitor,
    matched_keywords: list[str]
) -> tuple[bool, str]:
    try:
        config = channel.config
        webhook_url = config.get("webhook_url")
        headers = config.get("headers", {})
        
        if not webhook_url:
            return False, "Missing webhook URL"
        
        payload = {
            "event": "keyword_match",
            "monitor": {
                "id": monitor.id,
                "name": monitor.name,
                "url": monitor.url
            },
            "matched_keywords": matched_keywords,
            "timestamp": str(monitor.last_checked)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code < 400:
                return True, f"Webhook sent (status: {response.status_code})"
            else:
                return False, f"Webhook error: {response.status_code}"
                
    except Exception as e:
        return False, f"Webhook error: {str(e)}"
