"""Resend webhook receiver (svix-signed).

Incoming events (`email.delivered`, `email.bounced`, etc.) are persisted
in `email_events` and used to update the matching `whitelist` entry so
the admin dashboard surfaces delivery status in real-time.
"""

from __future__ import annotations

import json as _json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from svix.webhooks import Webhook, WebhookVerificationError

from core.config import RESEND_WEBHOOK_SECRET, db

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/resend")
async def resend_webhook(request: Request):
    """Handle Resend events (delivered, bounced, complained, opened...).

    Signature verification via Svix Webhook header spec:
      svix-id, svix-timestamp, svix-signature
    Secret comes from RESEND_WEBHOOK_SECRET env var.
    """
    body_bytes = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    if RESEND_WEBHOOK_SECRET:
        try:
            wh = Webhook(RESEND_WEBHOOK_SECRET)
            payload = wh.verify(body_bytes, headers)
        except WebhookVerificationError:
            logging.warning("Webhook signature invalid")
            raise HTTPException(status_code=401, detail="Invalid signature")
        except Exception as e:
            logging.exception("Webhook verify failed")
            raise HTTPException(status_code=400, detail=f"Malformed webhook: {e}")
    else:
        # No secret configured yet — accept raw (logged)
        logging.warning(
            "RESEND_WEBHOOK_SECRET not set — accepting webhook without verification"
        )
        try:
            payload = _json.loads(body_bytes.decode("utf-8") or "{}")
        except Exception:
            payload = {}

    event_type = payload.get("type", "unknown")
    data = payload.get("data", {}) or {}
    email_id = data.get("email_id") or data.get("id")
    to_field = data.get("to", [])
    if isinstance(to_field, list) and to_field:
        recipient = (to_field[0] or "").lower()
    elif isinstance(to_field, str):
        recipient = to_field.lower()
    else:
        recipient = ""

    # Persist every event (small log collection)
    await db.email_events.insert_one(
        {
            "_id": str(uuid.uuid4()),
            "type": event_type,
            "email_id": email_id,
            "recipient": recipient,
            "raw": payload,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    # Map event -> status
    status_map = {
        "email.sent": "sent",
        "email.delivered": "delivered",
        "email.delivery_delayed": "delayed",
        "email.bounced": "bounced",
        "email.complained": "complained",
        "email.opened": "opened",
        "email.clicked": "clicked",
    }
    status = status_map.get(event_type, event_type.split(".")[-1])

    # Update the whitelist entry for this email_id (preferred) or recipient
    query = None
    if email_id:
        query = {"email_id": email_id}
    elif recipient:
        query = {"email": recipient}

    if query:
        update = {
            "email_status": status,
            f"email_status_{status}_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == "delivered":
            update["email_sent"] = True
        await db.whitelist.update_one(query, {"$set": update})

    return {"ok": True, "processed": event_type}
