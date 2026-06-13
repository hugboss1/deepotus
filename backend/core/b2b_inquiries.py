"""B2B white-label inquiry intake (Sprint 20).

Lightweight CRUD over ``b2b_inquiries`` for the Video Generator
white-label CTA ("royaltie 25%"). Email notification to
``B2B_INQUIRY_EMAIL`` is best-effort via Resend; persistence is
guaranteed regardless.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import resend

from core.config import B2B_INQUIRY_EMAIL, RESEND_API_KEY, SENDER_EMAIL, db, logger


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes() -> None:
    await db.b2b_inquiries.create_index("created_at")
    await db.b2b_inquiries.create_index("email")
    logger.info("[b2b] inquiries indexes ready")


async def create_inquiry(
    *,
    name: str,
    email: str,
    company: Optional[str],
    message: str,
    locale: str = "fr",
) -> Dict[str, Any]:
    now = _now_utc()
    doc = {
        "_id": str(uuid.uuid4()),
        "name": name.strip(),
        "email": email.strip().lower(),
        "company": (company or "").strip() or None,
        "message": message.strip(),
        "locale": locale,
        "status": "new",
        "created_at": now,
        "updated_at": now,
    }
    await db.b2b_inquiries.insert_one(doc)
    # Best-effort email notification
    if RESEND_API_KEY:
        try:
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": [B2B_INQUIRY_EMAIL],
                "reply_to": [doc["email"]],
                "subject": f"[DEEPOTUS B2B] White-label inquiry — {doc['name']}",
                "text": (
                    f"New white-label inquiry\n\n"
                    f"Name: {doc['name']}\n"
                    f"Email: {doc['email']}\n"
                    f"Company: {doc['company'] or '-'}\n"
                    f"Locale: {locale}\n\n"
                    f"Message:\n{doc['message']}\n\n"
                    f"— deepotus.xyz / Sprint 20 B2B intake\n"
                    f"Inquiry id: {doc['_id']}\n"
                ),
            })
        except Exception:  # noqa: BLE001
            logger.exception("[b2b] resend notification failed (inquiry still persisted)")
    return doc


async def list_inquiries(limit: int = 200) -> list[Dict[str, Any]]:
    cursor = db.b2b_inquiries.find({}).sort("created_at", -1).limit(limit)
    return [d async for d in cursor]


__all__ = [
    "ensure_indexes",
    "create_inquiry",
    "list_inquiries",
]
