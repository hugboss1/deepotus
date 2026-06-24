"""License key + temporary download token generator (Sprint 20).

Used when a successful Stripe payment for ``videogen`` is webhooked
in. The generated key is stored on the order, and the email is sent
via Resend (best-effort — the order remains valid even if email
fails so the buyer can be re-emailed by admin).

No CDN/file-hosting is wired yet; the email currently points to the
``PUBLIC_BASE_URL`` + a token path so the actual binary can be served
later (admin can configure once the installer is uploaded).
"""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Tuple

import resend

from core.config import (
    PUBLIC_BASE_URL,
    RESEND_API_KEY,
    SENDER_EMAIL,
    logger,
)

_ALPHABET = string.ascii_uppercase + string.digits


def _gen_block(n: int = 5) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(n))


def generate_license_key(prefix: str = "DEEPOTUS-VGEN") -> str:
    """Format: ``DEEPOTUS-VGEN-XXXXX-XXXXX-XXXXX-XXXXX`` (4 blocks of 5)."""
    blocks = "-".join(_gen_block(5) for _ in range(4))
    return f"{prefix}-{blocks}"


def generate_download_token(ttl_hours: int = 72) -> Tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
    return token, expires_at


def send_license_email(
    *,
    to_email: str,
    customer_name: str,
    license_key: str,
    download_token: str,
    locale: str = "fr",
) -> bool:
    """Send the license + download email. Returns True on success."""
    if not RESEND_API_KEY:
        logger.warning("[license] Resend not configured — email not sent")
        return False
    download_url = f"{PUBLIC_BASE_URL.rstrip('/')}/api/payments/download/{download_token}"
    if locale == "en":
        subject = "DEEPOTUS Video Generator — your license & download link"
        body = (
            f"Hi {customer_name or 'there'},\n\n"
            f"Thank you for purchasing the DEEPOTUS Video Generator.\n\n"
            f"Your license key:\n  {license_key}\n\n"
            f"Download link (valid 72h):\n  {download_url}\n\n"
            f"Keep your license key safe — it's tied to your machine activation.\n"
            f"If the download link expires, reply to this email and we'll re-issue it.\n\n"
            f"— DEEPOTUS / Cabinet ΔΣ\n"
        )
    else:
        subject = "DEEPOTUS Video Generator — votre licence et lien de téléchargement"
        body = (
            f"Bonjour {customer_name or ''},\n\n"
            f"Merci pour votre achat du DEEPOTUS Video Generator.\n\n"
            f"Votre clé de licence :\n  {license_key}\n\n"
            f"Lien de téléchargement (valide 72h) :\n  {download_url}\n\n"
            f"Conservez votre clé — elle active le logiciel sur votre machine.\n"
            f"Si le lien expire, répondez à cet email et nous vous le renverrons.\n\n"
            f"— DEEPOTUS / Cabinet ΔΣ\n"
        )
    try:
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "text": body,
        })
        logger.info("[license] email sent to %s (license=%s…)", to_email, license_key[:18])
        return True
    except Exception:
        logger.exception("[license] failed to send email to %s", to_email)
        return False


__all__ = [
    "generate_license_key",
    "generate_download_token",
    "send_license_email",
]
