"""Outbound dispatcher abstractions for the Propaganda Engine.

Architecture
------------
Each platform exposes ONE coroutine ``send(item, *, dry_run, settings)``
that returns a normalised ``DispatchResult`` so the worker can handle
all platforms identically.

A platform module is responsible for:
    * resolving its own credentials (via ``secret_provider``)
    * formatting the payload (Markdown for Telegram, plain text for X)
    * calling the live API (or short-circuiting in dry-run mode)
    * mapping platform errors to either a transient failure (retry-able)
      or a permanent failure (do NOT retry)

Platforms can be added without touching the worker — just register
``send`` in ``DISPATCHERS`` below. The worker iterates, normalises,
and aggregates.

Failure model
-------------
Two-state result, surfaced upward:
    * ``DispatchOutcome.SENT``     — fire-and-forget success
    * ``DispatchOutcome.FAILED``   — record reason, do not retry
                                     (worker keeps item in 'failed';
                                      admin re-approve to re-queue)

Transient errors (5xx, 429, network) are mapped to FAILED in this
sprint to keep the scaffold dead-simple. Future work: add a retry
counter + exponential backoff in 13.3.x.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional

logger = logging.getLogger("deepotus.propaganda.dispatchers")


class DispatchOutcome(str, Enum):
    SENT = "sent"
    FAILED = "failed"


@dataclass
class DispatchResult:
    """Per-platform dispatch report. Stored as a dict in
    ``propaganda_queue.results[<platform>]`` for audit trail."""

    outcome: DispatchOutcome
    platform_message_id: Optional[str] = None  # tweet ID, telegram msg ID, …
    error: Optional[str] = None  # human-readable failure reason
    dry_run: bool = False
    duration_ms: int = 0
    response_snippet: Optional[str] = None  # first ~200 chars for diagnostics

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "platform_message_id": self.platform_message_id,
            "error": self.error,
            "dry_run": self.dry_run,
            "duration_ms": self.duration_ms,
            "response_snippet": self.response_snippet,
        }


# ---------------------------------------------------------------------
# Lazy-imported dispatcher registry
# ---------------------------------------------------------------------
# We resolve at call time (rather than at module import) so a misconfig
# in one platform's deps doesn't break the whole worker boot.

DispatchSendFn = Callable[..., Coroutine[Any, Any, DispatchResult]]


async def _send_telegram(*args, **kwargs) -> DispatchResult:
    from core.dispatchers.telegram import send as _impl

    return await _impl(*args, **kwargs)


async def _send_x(*args, **kwargs) -> DispatchResult:
    from core.dispatchers.x import send as _impl

    return await _impl(*args, **kwargs)


DISPATCHERS: Dict[str, DispatchSendFn] = {
    "telegram": _send_telegram,
    "x": _send_x,
}


def get_dispatcher(platform: str) -> Optional[DispatchSendFn]:
    """Return the send-coroutine for a platform, or None if unsupported."""
    return DISPATCHERS.get(platform.lower().strip())


__all__ = [
    "DispatchOutcome",
    "DispatchResult",
    "DISPATCHERS",
    "get_dispatcher",
]
