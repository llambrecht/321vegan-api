import base64
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.log import get_logger
from app.services.subscription_service import subscription_service

log = get_logger(__name__)

router = APIRouter()


@router.post("/apple", status_code=status.HTTP_200_OK)
async def apple_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive Apple App Store Server Notifications V2.
    Apple sends a signed JWS payload with subscription events.
    This endpoint is unauthenticated — Apple calls it directly.
    """
    try:
        body = await request.json()
        signed_payload = body.get("signedPayload")
        if not signed_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signedPayload",
            )

        success = subscription_service.process_apple_webhook(signed_payload, db)
        if not success:
            log.warning("Apple webhook processing returned failure")
            # Return 200 anyway to prevent Apple from retrying endlessly
            # The error is logged for investigation
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Apple webhook error: {str(e)}")
        return {"status": "ok"}


@router.post("/google", status_code=status.HTTP_200_OK)
async def google_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive Google Real-Time Developer Notifications via Pub/Sub push.
    Google sends a Pub/Sub message with base64-encoded subscription data.
    This endpoint is unauthenticated — Google calls it directly.
    """
    try:
        body = await request.json()
        message = body.get("message", {})
        data = message.get("data")
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing message data",
            )

        decoded = json.loads(base64.b64decode(data).decode("utf-8"))

        success = subscription_service.process_google_webhook(decoded, db)
        if not success:
            log.warning("Google webhook processing returned failure")
        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Google webhook error: {str(e)}")
        return {"status": "ok"}
