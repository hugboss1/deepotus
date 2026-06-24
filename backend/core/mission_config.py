"""Mission Command Center config (Sprint 21).

A single Mongo document (``mission_config._id == 'global'``) acts as
the runtime override layer above the static ``frontend/src/lib/missions.ts``
and i18n strings. Admin edits propagate to the live site in <500ms
(public GET endpoint, no SSR caching).

Design rules
------------
* **Singleton document** — simpler than per-key rows; the schema is
  small (~20 fields) and we never need partial concurrent writes.
* **Server-side defaults** — ``CONFIG_DEFAULTS`` is the source of truth
  if Mongo is empty. The first GET seeds the collection so future
  reads are immune to a Mongo wipe.
* **Never return secrets** — the document only stores public values
  (dates, amounts, status, CTA URLs, extraction-chamber copy). Secrets
  live in env vars / Cabinet Vault.
* **Versioned** — ``updated_at`` + ``updated_by`` to support audit
  trails and "who last changed the date?" questions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.config import db, logger

# ---------------------------------------------------------------------
# Defaults — mirror the static values in frontend/src/lib/missions.ts.
# ---------------------------------------------------------------------
CONFIG_DEFAULTS: Dict[str, Any] = {
    # ----- Giveaway parameters -----
    "giveaway_draw_date_iso": "2026-05-22T12:00:00Z",
    "giveaway_snapshot_date_iso": "2026-05-22T12:00:00Z",
    "giveaway_reward_sol": 5.0,
    "giveaway_winners_count": 2,
    "giveaway_min_invites": 3,
    "giveaway_min_holding_usd": 30.0,
    # ----- Extraction Chamber overrides (optional; null = use i18n) -----
    "extraction_chamber_title_fr": None,
    "extraction_chamber_title_en": None,
    "extraction_chamber_subtitle_fr": None,
    "extraction_chamber_subtitle_en": None,
    "extraction_chamber_body_fr": None,
    "extraction_chamber_body_en": None,
    # ----- Per-mission overrides (status + CTA URL + label date) -----
    # Stored as a dict keyed by mission_id. Missing keys = use defaults
    # from lib/missions.ts and i18n.
    "missions": {
        "infiltration":  {"status": "live", "cta_url": None, "label_date_iso": None},
        "liquidity":     {"status": "live", "cta_url": None, "label_date_iso": None},
        "amplification": {"status": "live", "cta_url": None, "label_date_iso": None},
        "archive":       {"status": "live", "cta_url": None, "label_date_iso": None},
        "signal":        {"status": "live", "cta_url": None, "label_date_iso": None},
        "future_06":     {"status": "redacted", "cta_url": None, "label_date_iso": None},
    },
    # ----- Email automation toggles -----
    "emails_enabled": True,
    "emails_helius_auto_send": False,  # post-mint only; admin flips on Day J
    "emails_sender_name": "Cabinet ΔΣ · DEEPOTUS",
    # ----- Audit -----
    "updated_at": None,
    "updated_by": None,
}

VALID_MISSION_STATUSES = {"live", "redacted", "completed"}
VALID_MISSION_IDS = set(CONFIG_DEFAULTS["missions"].keys())


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def ensure_indexes() -> None:
    """Idempotent index setup."""
    await db.mission_config.create_index("_id")  # implicit but harmless
    logger.info("[mission_config] indexes ready")


async def get_config() -> Dict[str, Any]:
    """Read the singleton, seeding defaults on first call.

    Returns the *merged* doc: defaults filled in for any key missing
    from the persisted row. Guarantees callers always see a complete
    shape.
    """
    doc = await db.mission_config.find_one({"_id": "global"})
    if not doc:
        seed = {"_id": "global", **CONFIG_DEFAULTS, "updated_at": _now_utc(), "updated_by": "system_seed"}
        await db.mission_config.insert_one(seed)
        logger.info("[mission_config] seeded defaults on first read")
        return seed
    merged = {**CONFIG_DEFAULTS, **doc}
    # Deep-merge the ``missions`` sub-dict so newly added mission ids
    # in defaults appear for legacy rows.
    merged["missions"] = {
        **CONFIG_DEFAULTS["missions"],
        **(doc.get("missions") or {}),
    }
    return merged


def _coerce_field(field: str, value: Any) -> Any:
    """Light validation + normalisation per field. Raises ValueError on bad input."""
    if field in {"giveaway_reward_sol", "giveaway_min_holding_usd"}:
        v = float(value)
        if v < 0:
            raise ValueError(f"{field} must be >= 0")
        return v
    if field in {"giveaway_winners_count", "giveaway_min_invites"}:
        v = int(value)
        if v < 0:
            raise ValueError(f"{field} must be >= 0")
        return v
    if field in {
        "giveaway_draw_date_iso",
        "giveaway_snapshot_date_iso",
    }:
        # Best-effort validation: just ensure datetime.fromisoformat parses.
        s = str(value).replace("Z", "+00:00")
        datetime.fromisoformat(s)
        return str(value)
    if field in {"emails_enabled", "emails_helius_auto_send"}:
        return bool(value)
    if field in {"emails_sender_name"}:
        return str(value).strip()[:120]
    if field.startswith("extraction_chamber_"):
        # null clears the override
        if value in (None, "", "null"):
            return None
        return str(value).strip()[:1000]
    if field == "missions":
        # Validate the dict shape
        if not isinstance(value, dict):
            raise ValueError("missions must be an object")
        out: Dict[str, Any] = {}
        for mid, mdoc in value.items():
            if mid not in VALID_MISSION_IDS:
                # Skip unknown ids defensively (don't 400 — future-proofs)
                continue
            if not isinstance(mdoc, dict):
                continue
            status = mdoc.get("status", "live")
            if status not in VALID_MISSION_STATUSES:
                raise ValueError(f"missions.{mid}.status invalid: {status}")
            cta = mdoc.get("cta_url")
            if cta is not None and not isinstance(cta, str):
                raise ValueError(f"missions.{mid}.cta_url must be string or null")
            label_date = mdoc.get("label_date_iso")
            if label_date:
                datetime.fromisoformat(str(label_date).replace("Z", "+00:00"))
            out[mid] = {
                "status": status,
                "cta_url": (cta or None) and cta.strip() or None,
                "label_date_iso": label_date or None,
            }
        return out
    raise ValueError(f"unknown field {field}")


async def update_config(
    patch: Dict[str, Any], *, actor: str = "admin"
) -> Dict[str, Any]:
    """Apply a partial patch and return the merged doc.

    Only known fields are accepted; unknown fields raise ValueError.
    """
    if not isinstance(patch, dict):
        raise ValueError("patch must be an object")
    clean: Dict[str, Any] = {}
    for k, v in patch.items():
        # Allow only fields defined in defaults (excluding audit fields).
        if k in ("updated_at", "updated_by", "_id"):
            continue
        if k not in CONFIG_DEFAULTS:
            raise ValueError(f"unknown field: {k}")
        clean[k] = _coerce_field(k, v)
    if not clean:
        return await get_config()
    clean["updated_at"] = _now_utc()
    clean["updated_by"] = actor[:40] if actor else "admin"
    await db.mission_config.update_one(
        {"_id": "global"},
        {"$set": clean, "$setOnInsert": {"_id": "global"}},
        upsert=True,
    )
    logger.info("[mission_config] patched by=%s fields=%s", actor, sorted(clean.keys()))
    return await get_config()


__all__ = [
    "CONFIG_DEFAULTS",
    "VALID_MISSION_IDS",
    "VALID_MISSION_STATUSES",
    "ensure_indexes",
    "get_config",
    "update_config",
]
