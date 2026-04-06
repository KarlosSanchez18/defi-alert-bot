import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import stripe

load_dotenv()

app = FastAPI()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")


class CheckoutRequest(BaseModel):
    telegram_user_id: int
    chat_id: int
    email: str | None = None


@app.get("/health")
async def health():
    return {
        "ok": True,
        "stripe_key_loaded": bool(stripe.api_key),
    }


@app.post("/create-checkout-session")
async def create_checkout_session(data: CheckoutRequest):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe key not configured")

    if not STRIPE_PRICE_ID:
        raise HTTPException(status_code=500, detail="STRIPE_PRICE_ID not configured")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[
                {
                    "price": STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ],
            success_url="https://t.me/ciih_bot",
            cancel_url="https://t.me/ciih_bot",
            metadata={
                "telegram_user_id": str(data.telegram_user_id),
                "chat_id": str(data.chat_id),
            },
            customer_email=data.email if data.email else None,
        )

        return {
            "url": session.url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))