"""Genesis subscribers → Level 02 promotion (Mail #2 backfill).

While the classified vault is SEALED, /api/access-card/genesis-broadcast
captures visitors into ``db.genesis_subscribers`` and Mail #1 promises the
Level 02 accreditation card will be "auto-sent at mint". This module is the
machinery that honors that promise once the vault flips LIVE:

  * :func:`build_genesis_subscriber_doc` — canonical shape of a vault-terminal
    subscriber document. Carries ``email_hash`` + ``source`` because the
    ecosystem Genesis list (``core.genesis``) maintains a UNIQUE index on
    ``(email_hash, source)`` over the same collection — documents without
    those fields all collide on the (null, null) key pair.
  * :func:`promote_pending` — iterates subscribers still awaiting promotion
    (``promoted_to_accreditation: false``), generates each access card,
    sends Mail #2 and marks the document promoted. Sealed-guarded (refuses
    to run pre-mint unless ``force``), supports ``dry_run`` and ``limit``,
    skips blacklisted agents, and a failed send never marks the doc so a
    later run retries it.

Card creation and email dispatch are injected callables so the logic stays
unit-testable offline (see ``tests/test_genesis_promotion.py``); the admin
router wires the real implementations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from core.genesis import _hash_email
from core.vault_seal import get_sealed_status

# Source tag distinguishing vault-terminal captures from the ecosystem
# Genesis list sources (genesis_roman / genesis_mobile / ...).
VAULT_TERMINAL_SOURCE = "vault_terminal"

# Only vault-terminal docs carry ``promoted_to_accreditation`` — ecosystem
# Genesis list docs never match this query. Docs flagged with a skip reason
# (e.g. blacklisted) are excluded so reruns don't re-scan them forever.
PENDING_QUERY: Dict[str, Any] = {
    "promoted_to_accreditation": False,
    "promotion_skipped_reason": {"$exists": False},
}

CreateCard = Callable[..., Awaitable[Dict[str, Any]]]
SendEmail = Callable[..., Awaitable[bool]]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_genesis_subscriber_doc(
    *,
    email: str,
    display_name: str,
    position: int,
    lang: str,
    ip: Optional[str] = None,
    ua: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the document inserted by the sealed genesis-broadcast flow."""
    email = email.lower().strip()
    return {
        "_id": str(uuid.uuid4()),
        "email": email,
        "email_hash": _hash_email(email),
        "source": VAULT_TERMINAL_SOURCE,
        "display_name": display_name,
        "position": position,
        "subscribed_at": _now_iso(),
        "ip": ip,
        "ua": (ua or "")[:240],
        "lang": lang,
        "vault_status_at_signup": "sealed",
        "promoted_to_accreditation": False,
    }


async def promote_pending(
    db,
    *,
    create_card: CreateCard,
    send_email: SendEmail,
    dry_run: bool = False,
    limit: Optional[int] = None,
    force: bool = False,
) -> Dict[str, Any]:
    """Send Mail #2 (Level 02 access card) to every un-promoted subscriber.

    Arguments:
        create_card: ``async (email=, display_name=, whitelisted=) -> card_doc``
        send_email:  ``async (email=, lang=, card_doc=) -> bool`` (True = sent)
        dry_run:     scan and report, but create/send/mark nothing.
        limit:       cap the number of subscribers processed this run.
        force:       run even while the vault is sealed (staff QA only).
    """
    status = await get_sealed_status(db)
    summary: Dict[str, Any] = {
        "ok": True,
        "sealed": status["sealed"],
        "dry_run": dry_run,
        "scanned": 0,
        "promoted": 0,
        "skipped_blacklisted": 0,
        "failed": 0,
        "results": [],
    }
    if status["sealed"] and not force:
        summary["ok"] = False
        summary["code"] = "VAULT_SEALED"
        return summary

    cursor = db.genesis_subscribers.find(PENDING_QUERY).sort("position", 1)
    if limit:
        cursor = cursor.limit(int(limit))

    results: List[Dict[str, Any]] = summary["results"]
    async for sub in cursor:
        email = (sub.get("email") or "").lower().strip()
        if not email:
            continue
        summary["scanned"] += 1

        if dry_run:
            results.append({"email": email, "status": "pending"})
            continue

        bl = await db.blacklist.find_one({"email": email})
        if bl:
            summary["skipped_blacklisted"] += 1
            await db.genesis_subscribers.update_one(
                {"_id": sub["_id"]},
                {"$set": {"promotion_skipped_reason": "blacklisted"}},
            )
            results.append({"email": email, "status": "skipped_blacklisted"})
            continue

        sent = False
        card_doc: Dict[str, Any] = {}
        try:
            wl = await db.whitelist.find_one({"email": email})
            card_doc = await create_card(
                email=email,
                display_name=(sub.get("display_name") or "").strip()
                or email.split("@")[0],
                whitelisted=bool(wl),
            )
            sent = bool(
                await send_email(
                    email=email,
                    lang=(sub.get("lang") or "fr"),
                    card_doc=card_doc,
                )
            )
        except Exception:  # noqa: BLE001 — one bad subscriber must not stop the run
            logging.exception("[genesis-promotion] failed for %s", email)
            sent = False

        if not sent:
            summary["failed"] += 1
            results.append({"email": email, "status": "failed"})
            continue

        summary["promoted"] += 1
        await db.genesis_subscribers.update_one(
            {"_id": sub["_id"]},
            {
                "$set": {
                    "promoted_to_accreditation": True,
                    "promoted_at": _now_iso(),
                    "accreditation_number": card_doc.get("accreditation_number"),
                }
            },
        )
        results.append(
            {
                "email": email,
                "status": "promoted",
                "accreditation_number": card_doc.get("accreditation_number"),
            }
        )

    return summary


__all__ = [
    "VAULT_TERMINAL_SOURCE",
    "PENDING_QUERY",
    "build_genesis_subscriber_doc",
    "promote_pending",
]
