"""Telegram Bot API dispatcher.

Spec
----
* Bot Token   : Cabinet Vault (``telegram/TELEGRAM_BOT_TOKEN``) or env
* Chat ID     : Cabinet Vault (``telegram/TELEGRAM_CHAT_ID``) or env
                Channel/group/user the bot has permission to post to.
* Endpoint    : ``POST https://api.telegram.org/bot<TOKEN>/sendMessage``
* Body        : ``{"chat_id", "text", "parse_mode": "Markdown",
                   "disable_web_page_preview": true}``

Dry-run mode
------------
If ``dry_run=True`` we LOG the would-be payload and return SENT
without any HTTP call. This is the default until the admin flips
``propaganda_settings.dispatch_dry_run = false``.

Failure mapping
---------------
* No bot_token configured     → FAILED ("no_credentials")
* Telegram returns ok=true    → SENT (with message_id)
* Telegram returns ok=false   → FAILED (with description)
* HTTP 4xx/5xx                → FAILED (status code in error)
* Timeout / network           → FAILED ("network_error: …")

Rate limit awareness
--------------------
Telegram allows ~30 messages/sec to the same chat. Our per-trigger
rate limit (15 min default) plus the queue's per-hour/day caps keep
us comfortably under that — no extra throttle needed here.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import httpx

from core.dispatchers.base import DispatchOutcome, DispatchResult
from core.secret_provider import (
    get_telegram_bot_token,
    get_telegram_chat_id,
)

logger = logging.getLogger("deepotus.propaganda.dispatchers.telegram")


_API_BASE = "https://api.telegram.org"
_REQUEST_TIMEOUT_S = 15.0


async def send(
    item: Dict[str, Any],
    *,
    dry_run: bool = True,
    settings: Optional[Dict[str, Any]] = None,
) -> DispatchResult:
    """Send a queue item's text to Telegram.

    Args:
        item: Normalised queue item (from ``dispatch_queue.list_queue``).
            Must contain ``rendered_content`` (the message body).
        dry_run: When True, no real HTTP call. Used as the default in
            scaffold mode until live credentials are wired.
        settings: Optional propaganda_settings dict (currently unused,
            kept for future per-channel routing).

    Returns:
        DispatchResult with outcome=SENT or FAILED.
    """
    started = time.monotonic()
    text = (item.get("rendered_content") or "").strip()
    if not text:
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error="empty_content",
            dry_run=dry_run,
            duration_ms=_elapsed_ms(started),
        )

    # Truncate to Telegram's 4096-char limit (margin for safety)
    if len(text) > 4000:
        text = text[:3996] + "…"

    if dry_run:
        logger.info(
            "[telegram.dry_run] would_send chars=%d preview=%r",
            len(text),
            text[:80],
        )
        return DispatchResult(
            outcome=DispatchOutcome.SENT,
            platform_message_id="dry-run",
            dry_run=True,
            duration_ms=_elapsed_ms(started),
            response_snippet="(dry-run, no HTTP call)",
        )

    # ------------- Live mode -------------
    bot_token = await get_telegram_bot_token()
    chat_id = await get_telegram_chat_id()
    if not bot_token or not chat_id:
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error="no_credentials",
            duration_ms=_elapsed_ms(started),
        )

    url = f"{_API_BASE}/bot{bot_token}/sendMessage"
    body = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT_S) as client:
            resp = await client.post(url, json=body)
        snippet = resp.text[:200] if resp.text else None
        if resp.status_code >= 400:
            # Telegram doesn't use 429 standard but flooding triggers
            # 429 with "Too Many Requests" + Retry-After. Treat 429
            # and 5xx as retry-eligible; 4xx (other) = permanent
            # (bad chat_id, blocked bot, banned chat, unparseable
            # markdown — admin must re-edit before retrying).
            transient = resp.status_code == 429 or resp.status_code >= 500
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error=f"http_{resp.status_code}",
                duration_ms=_elapsed_ms(started),
                response_snippet=snippet,
                transient_failure=transient,
            )
        data = resp.json()
        if not data.get("ok"):
            return DispatchResult(
                outcome=DispatchOutcome.FAILED,
                error=f"telegram_error: {data.get('description', 'unknown')}",
                duration_ms=_elapsed_ms(started),
                response_snippet=snippet,
            )
        msg_id = str((data.get("result") or {}).get("message_id") or "?")
        logger.info(
            "[telegram] sent chars=%d msg_id=%s in %d ms",
            len(text), msg_id, _elapsed_ms(started),
        )
        return DispatchResult(
            outcome=DispatchOutcome.SENT,
            platform_message_id=msg_id,
            duration_ms=_elapsed_ms(started),
            response_snippet=snippet,
        )
    except httpx.TimeoutException:
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error="timeout",
            duration_ms=_elapsed_ms(started),
            transient_failure=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[telegram] dispatch crashed")
        return DispatchResult(
            outcome=DispatchOutcome.FAILED,
            error=f"network_error: {exc}",
            duration_ms=_elapsed_ms(started),
            transient_failure=True,
        )


def _elapsed_ms(started_monotonic: float) -> int:
    return int((time.monotonic() - started_monotonic) * 1000)
