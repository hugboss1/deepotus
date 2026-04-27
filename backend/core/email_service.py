"""Transactional email dispatch for the Prophet.

Only the welcome (whitelist) email lives here. Access-card emails are kept
inline in the access-card router for clarity (they bundle attachments and
per-card logic).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import resend

from core.config import db
from core.secret_provider import (
    get_public_base_url,
    get_resend_api_key,
    get_sender_email,
)
from email_templates import email_subject, render_welcome_email


async def send_welcome_email(
    email: str,
    position: int,
    lang: str,
    entry_id: str,
) -> None:
    """Fire a welcome/whitelist confirmation email through Resend.

    Runs in a background task. Never raises: failures are persisted on the
    whitelist document so the admin dashboard can surface them.
    """
    api_key = await get_resend_api_key()
    if not api_key:
        logging.info("RESEND_API_KEY missing — skipping email.")
        return
    # `resend` SDK reads its API key from the module-level attribute, so
    # we reassign on every call to honour rotation through the Cabinet
    # Vault without requiring a process restart.
    resend.api_key = api_key

    try:
        sender = await get_sender_email()
        base_url = await get_public_base_url()
        html = render_welcome_email(
            lang=lang,
            email=email,
            position=position,
            base_url=base_url,
        )
        subject = email_subject(lang)
        params = {
            "from": sender,
            "to": [email],
            "subject": subject,
            "html": html,
        }
        res = await asyncio.to_thread(resend.Emails.send, params)
        email_id = None
        if isinstance(res, dict):
            email_id = res.get("id")
        elif hasattr(res, "get"):
            email_id = res.get("id")

        await db.whitelist.update_one(
            {"_id": entry_id},
            {
                "$set": {
                    "email_sent": True,
                    "email_sent_at": datetime.now(timezone.utc).isoformat(),
                    "email_provider": "resend",
                    "email_id": email_id,
                    "email_status": "sent",
                }
            },
        )
        logging.info(f"Welcome email sent to {email} (id={email_id}).")
    except Exception as e:
        logging.exception(f"Failed to send welcome email to {email}: {e}")
        await db.whitelist.update_one(
            {"_id": entry_id},
            {
                "$set": {
                    "email_sent": False,
                    "email_error": str(e)[:500],
                    "email_error_at": datetime.now(timezone.utc).isoformat(),
                    "email_status": "failed",
                }
            },
        )
