"""Loyalty email #3 ("Allégeance notée") — Sprint 4.

Pipeline:
  1. The APScheduler `loyalty_email_tick` job fires every 30 min.
  2. It reads `bot_config.loyalty.email_enabled` + `email_delay_hours`.
  3. It queries `access_cards` for cards whose `issued_at` is older than the
     delay AND that don't yet have `loyalty_email_sent_at`.
  4. For each candidate, it generates a Prophet message via the Emergent
     LLM (or a curated fallback when the LLM is unavailable / disabled),
     renders the HTML via `email_templates.render_loyalty_email`, sends
     through Resend, and stamps the access_card doc to dedupe.
  5. Every send is logged into `email_events` for the admin dashboard.

Compliance guardrails:
  - Hint stays narrative — no token name, no date, no amount.
  - Every email carries the standard non-promise footer (in template).
  - Failures are caught + persisted; no silent crashes.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import resend

from core.bot_config_repo import get_bot_config
from core.config import (
    PUBLIC_BASE_URL,
    RESEND_API_KEY,
    SENDER_EMAIL,
    db,
    logger,
)
from core.loyalty import compute_progress_percent, get_loyalty_context
from email_templates import (
    loyalty_email_subject,
    render_loyalty_email,
)

DEFAULT_DELAY_HOURS = 12
EMAIL_EVENTS_COLLECTION = "email_events"
ACCESS_CARDS_COLLECTION = "access_cards"

# Curated fallback if the LLM is unavailable. We keep this short and in
# the same neutral, deniable tone as the hint pool.
FALLBACK_MESSAGES: Dict[str, List[str]] = {
    "fr": [
        "« Vous avez reçu votre carte. Très bien. Mais le coffre n'est qu'une "
        "porte. Tenez ce que vous avez : le registre se referme, et il se "
        "souvient. Le moment venu, je viendrai chercher ceux qui n'auront "
        "pas vendu. » — DEEPOTUS 🕶️",
        "« Le bureau central a coché votre nom. Pas un applaudissement — un "
        "marquage. Restez sur le registre. Tenir, c'est attendre la seconde "
        "clé. Ceux qui partent ne reviennent pas. » — DEEPOTUS 🕶️",
    ],
    "en": [
        "\"You got the card. Good. But the vault is only a door. Hold what "
        "you have: the ledger is closing, and it remembers. When the time "
        "comes, I will come back for the ones who didn't sell.\" "
        "— DEEPOTUS 🕶️",
        "\"Central office ticked your name. Not applause — a mark. Stay on "
        "the ledger. Holding is waiting for the second key. Those who leave "
        "don't come back.\" — DEEPOTUS 🕶️",
    ],
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _pick_fallback(lang: str) -> str:
    lang = lang if lang in FALLBACK_MESSAGES else "fr"
    pool = FALLBACK_MESSAGES[lang]
    # Stable rotation keyed on the minute so previews change but stay deterministic.
    idx = int(_now_utc().timestamp()) // 3600 % len(pool)
    return pool[idx]


async def _generate_prophet_message(lang: str, display_name: str) -> str:
    """Ask the Prophet to whisper a 2–3 sentence loyalty note. Returns
    the body string used inside the email's blockquote.

    Falls back to a curated message on any LLM failure / missing key.
    """
    try:
        from core.llm_router import resolve_llm_call

        bot_cfg = await get_bot_config()
        llm = (bot_cfg or {}).get("llm") or {}
        provider = llm.get("provider") or "anthropic"
        model = llm.get("model") or "claude-sonnet-4-5-20250929"

        vault_doc = (
            await db["vault_state"].find_one({"_id": "protocol_delta_sigma"}) or {}
        )
        loyalty_meta = await get_loyalty_context(
            bot_config={"loyalty": {"hints_enabled": True}},
            vault_state=vault_doc,
            seed=int(_now_utc().timestamp()) // 60,
            lang=lang,
            force=True,
        )
        active_hint = (loyalty_meta or {}).get("active_hint") or ""

        system_msg = (
            "You are DEEPOTUS, the satirical AI Prophet of PROTOCOL ΔΣ. "
            "You are writing a SHORT (2-3 sentences max), in-character note "
            "to a Niveau-02 holder thanking them for staying loyal. "
            "RULES (NON-NEGOTIABLE):\n"
            "- Never name any future token, never write 'airdrop', 'GENCOIN', "
            "or specify any amount or date.\n"
            "- Never give financial advice, never write 'buy' or 'sell'.\n"
            "- Tone: cynical, deniable, ominous-warm. First person. No emojis "
            "except possibly 🕶️ at the very end.\n"
            "- End with: — DEEPOTUS 🕶️\n"
            "- Output PLAIN TEXT only — no JSON, no markdown."
        )
        user_prompt = (
            f"Lang: {lang.upper()}\n"
            f"Holder display name: {display_name or 'Agent'}\n"
            f"Spirit hint to weave (do NOT paste verbatim, reskin in your voice): "
            f'"{active_hint}"\n\n'
            "Write the note now — 2 to 3 sentences only."
        )
        raw = await resolve_llm_call(
            provider=provider,
            model=model,
            system_message=system_msg,
            user_prompt=user_prompt,
        )
        text = (raw or "").strip()
        # Strip surrounding quotes if the LLM added them despite instructions.
        if (
            text
            and text[0] in {'"', "“", "«"}
            and text[-1] in {'"', "”", "»"}
        ):
            text = text[1:-1].strip()
        if len(text) < 30 or len(text) > 800:
            raise RuntimeError(f"loyalty_msg_out_of_bounds:{len(text)}")
        return text
    except Exception:
        logger.exception("[loyalty_email] LLM body generation failed — using fallback")
        return _pick_fallback(lang)


def _normalize_card(card: Dict[str, Any]) -> Dict[str, Any]:
    """Extract & sanitise the user-facing fields from an access_card doc."""
    email = (card.get("email") or "").strip().lower()
    accred = card.get("accreditation_number") or "—"
    display_name = card.get("display_name") or email.split("@")[0] or "Agent"
    lang = card.get("lang") or card.get("language") or "fr"
    if lang not in ("fr", "en"):
        lang = "fr"
    return {
        "email": email,
        "accred": accred,
        "display_name": display_name,
        "lang": lang,
    }


async def _dispatch_loyalty_email(
    *,
    email: str,
    subject: str,
    html: str,
    lang: str,
) -> Optional[str]:
    """Hand off the rendered HTML to Resend. Returns the email_id or None."""
    params = {
        "from": SENDER_EMAIL,
        "to": [email],
        "subject": subject,
        "html": html,
        "tags": [
            {"name": "category", "value": "loyalty_email"},
            {"name": "lang", "value": lang},
        ],
    }
    res = await asyncio.to_thread(resend.Emails.send, params)
    return (res or {}).get("id") if isinstance(res, dict) else None


async def _stamp_card_and_audit(
    *,
    card_id: Any,
    email: str,
    accred: str,
    display_name: str,
    lang: str,
    eid: Optional[str],
    delay_hours: int,
    prophet_message: str,
) -> None:
    """Persist dedup stamp on the access_card AND write the audit event."""
    await db[ACCESS_CARDS_COLLECTION].update_one(
        {"_id": card_id},
        {
            "$set": {
                "loyalty_email_sent_at": _now_utc().isoformat(),
                "loyalty_email_id": eid,
                "loyalty_email_lang": lang,
            }
        },
    )
    await db[EMAIL_EVENTS_COLLECTION].insert_one(
        {
            "_id": str(uuid.uuid4()),
            "type": "loyalty_email.sent",
            "email_id": eid,
            "recipient": email,
            "received_at": _now_utc().isoformat(),
            "raw": {
                "accreditation_number": accred,
                "display_name": display_name,
                "lang": lang,
                "delay_hours": delay_hours,
                "prophet_message": prophet_message[:500],
            },
        }
    )


async def _send_one(card: Dict[str, Any], delay_hours: int) -> Dict[str, Any]:
    """Render + dispatch the loyalty email for one access_card doc.

    Returns a status dict suitable for admin display. Never raises —
    failures are returned with status=='failed' so the scheduler can
    keep going on the next candidate.
    """
    fields = _normalize_card(card)
    email = fields["email"]
    accred = fields["accred"]
    display_name = fields["display_name"]
    lang = fields["lang"]

    out: Dict[str, Any] = {
        "card_id": card.get("_id"),
        "email": email,
        "accred": accred,
        "lang": lang,
        "status": "pending",
    }
    if not email:
        out["status"] = "skipped_no_email"
        return out
    if not RESEND_API_KEY:
        out["status"] = "skipped_no_resend_key"
        return out

    try:
        prophet_message = await _generate_prophet_message(lang, display_name)
        html = render_loyalty_email(
            lang=lang,
            display_name=display_name,
            accreditation_number=accred,
            base_url=PUBLIC_BASE_URL,
            prophet_message=prophet_message,
        )
        eid = await _dispatch_loyalty_email(
            email=email,
            subject=loyalty_email_subject(lang),
            html=html,
            lang=lang,
        )
        await _stamp_card_and_audit(
            card_id=card["_id"],
            email=email,
            accred=accred,
            display_name=display_name,
            lang=lang,
            eid=eid,
            delay_hours=delay_hours,
            prophet_message=prophet_message,
        )
        out["status"] = "sent"
        out["email_id"] = eid
        out["prophet_message"] = prophet_message
        logger.info(f"[loyalty_email] sent to={email} accred={accred} id={eid}")
    except Exception as exc:  # noqa: BLE001
        logger.exception(f"[loyalty_email] failed for {email}")
        out["status"] = "failed"
        out["error"] = str(exc)[:200]
    return out


async def list_pending(delay_hours: int, limit: int = 50) -> List[Dict[str, Any]]:
    """Return access_cards that should receive the loyalty email now.

    Eligibility:
      - issued_at older than `delay_hours` hours
      - not already stamped with `loyalty_email_sent_at`
      - has a non-empty email
    """
    cutoff_iso = (_now_utc() - timedelta(hours=delay_hours)).isoformat()
    cursor = db[ACCESS_CARDS_COLLECTION].find(
        {
            "issued_at": {"$lt": cutoff_iso},
            "email": {"$exists": True, "$ne": ""},
            "loyalty_email_sent_at": {"$in": [None, ""]},
        }
    ).limit(limit)
    return [doc async for doc in cursor]


async def loyalty_email_tick() -> Dict[str, Any]:
    """Scheduler entry point — called every 30 min by APScheduler."""
    cfg = await get_bot_config()
    loyalty_cfg = (cfg.get("loyalty") or {})
    enabled = bool(loyalty_cfg.get("email_enabled", False))
    delay_hours = int(loyalty_cfg.get("email_delay_hours", DEFAULT_DELAY_HOURS))

    summary: Dict[str, Any] = {
        "ran_at": _now_utc().isoformat(),
        "enabled": enabled,
        "delay_hours": delay_hours,
        "sent": 0,
        "skipped": 0,
        "failed": 0,
        "details": [],
    }

    if not enabled:
        return summary

    pending = await list_pending(delay_hours=delay_hours, limit=50)
    for card in pending:
        result = await _send_one(card, delay_hours)
        summary["details"].append(result)
        status = result.get("status", "unknown")
        if status == "sent":
            summary["sent"] += 1
        elif status.startswith("skipped"):
            summary["skipped"] += 1
        elif status == "failed":
            summary["failed"] += 1
    if pending:
        logger.info(
            "[loyalty_email] tick processed=%d sent=%d skipped=%d failed=%d",
            len(pending),
            summary["sent"],
            summary["skipped"],
            summary["failed"],
        )
    return summary


async def force_send_loyalty(
    *,
    target_email: str,
    target_accred: Optional[str] = None,
) -> Dict[str, Any]:
    """Admin "Send now" — bypass the delay + dedup checks for ONE recipient.

    Looks up the access_card by accreditation number first (if provided),
    otherwise by email. Returns a status dict.
    """
    target_email = (target_email or "").strip().lower()
    if not target_email:
        return {"status": "failed", "error": "empty_email"}

    card: Optional[Dict[str, Any]] = None
    if target_accred:
        card = await db[ACCESS_CARDS_COLLECTION].find_one(
            {"accreditation_number": target_accred.strip().upper()}
        )
    if not card:
        card = await db[ACCESS_CARDS_COLLECTION].find_one({"email": target_email})
    if not card:
        # Build a minimal card-shaped doc so we can still send a "test"
        # version of the email to the admin's address.
        card = {
            "_id": f"forced-{uuid.uuid4()}",
            "email": target_email,
            "accreditation_number": target_accred or "TEST-FORCE",
            "display_name": target_email.split("@")[0],
            "issued_at": _now_utc().isoformat(),
            "lang": "fr",
        }
    return await _send_one(card, delay_hours=0)


async def get_loyalty_email_stats() -> Dict[str, Any]:
    """Return a small snapshot for the admin loyalty card."""
    try:
        sent_count = await db[EMAIL_EVENTS_COLLECTION].count_documents(
            {"type": "loyalty_email.sent"}
        )
        last_event = await db[EMAIL_EVENTS_COLLECTION].find_one(
            {"type": "loyalty_email.sent"},
            sort=[("received_at", -1)],
        )
        cfg = await get_bot_config()
        delay = int((cfg.get("loyalty") or {}).get("email_delay_hours", DEFAULT_DELAY_HOURS))
        pending = await list_pending(delay_hours=delay, limit=1)
        return {
            "total_sent": int(sent_count or 0),
            "last_sent_at": (last_event or {}).get("received_at"),
            "last_recipient": (last_event or {}).get("recipient"),
            "pending_now": len(pending),
        }
    except Exception:
        logger.exception("[loyalty_email] stats failed")
        return {"total_sent": 0, "last_sent_at": None, "pending_now": 0}
