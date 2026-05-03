"""Shared dispatch-result primitives — extracted from `__init__.py` to
break the circular import between ``core.dispatchers`` (the registry)
and ``core.dispatchers.telegram`` / ``core.dispatchers.x`` (the per-
platform implementations).

Architecture intent:
    core/dispatchers/base.py        ← dataclasses + enum (this module)
    core/dispatchers/telegram.py    → from .base import DispatchOutcome, DispatchResult
    core/dispatchers/x.py           → from .base import DispatchOutcome, DispatchResult
    core/dispatchers/__init__.py    → re-exports + DISPATCHERS registry

Importers external to ``core/dispatchers`` keep using the old import
path (``from core.dispatchers import DispatchOutcome, DispatchResult``)
because ``__init__.py`` re-exports both names — no breaking change.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


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
    #: ``True`` for retry-eligible failures (network timeout, 429, 5xx).
    #: The worker will re-schedule the item with exponential backoff
    #: instead of marking it terminally failed. Default ``False`` —
    #: only set explicitly by dispatchers when they detect a known
    #: transient class of error.
    transient_failure: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "platform_message_id": self.platform_message_id,
            "error": self.error,
            "dry_run": self.dry_run,
            "duration_ms": self.duration_ms,
            "response_snippet": self.response_snippet,
            "transient_failure": self.transient_failure,
        }


__all__ = [
    "DispatchOutcome",
    "DispatchResult",
]
