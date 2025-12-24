import os
import stripe
from typing import Optional
from app.database import db
from app.models import User

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")


def create_checkout_session(user: User, success_url: str, cancel_url: str) -> Optional[str]:
    if not stripe.api_key:
        return None
    
    try:
        customer_id = user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": user.id}
            )
            customer_id = customer.id
            user.stripe_customer_id = customer_id
            db.update_user(user)
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_ID,
                "quantity": 1,
            }] if PRICE_ID else [{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "URL Watchdog Pro",
                        "description": "Unlimited monitors and notifications"
                    },
                    "unit_amount": 999,
                    "recurring": {"interval": "month"}
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        
        return session.url
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return None


def handle_webhook_event(payload: bytes, sig_header: str, webhook_secret: str) -> bool:
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return False
    except stripe.error.SignatureVerificationError:
        return False
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        
        for user in db.users.values():
            if user.stripe_customer_id == customer_id:
                user.subscription_status = "pro"
                db.update_user(user)
                break
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        
        for user in db.users.values():
            if user.stripe_customer_id == customer_id:
                user.subscription_status = "free"
                db.update_user(user)
                break
    
    return True


def create_billing_portal_session(user: User, return_url: str) -> Optional[str]:
    if not stripe.api_key or not user.stripe_customer_id:
        return None
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url,
        )
        return session.url
    except stripe.error.StripeError as e:
        print(f"Stripe portal error: {e}")
        return None
