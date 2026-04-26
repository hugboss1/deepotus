"""Bot configuration repository — shared persistence layer.

Extracted from `core/bot_scheduler.py` to break the import cycle
between the scheduler module (which lazily imports its consumers
`loyalty_email`, `news_repost`, `news_feed` to register jobs) and
those same consumers (which need to read bot_config to decide what
to do).

This module has **NO dependencies** on the scheduler or any consumer
module — only on `core.config` (Mongo handle) — so it can be safely
imported from anywhere in the backend without creating a cycle.

Public API:
    - DEFAULT_BOT_CONFIG       : dict baked into the singleton on first boot
    - CONFIG_COLLECTION        : Mongo collection name
    - CONFIG_SINGLETON_ID      : Mongo _id of the unique config doc
    - POSTS_COLLECTION         : audit trail collection name
    - ensure_bot_config()      : idempotent create-if-missing
    - get_bot_config()         : fast read
    - persist_bot_config_patch : write a partial patch (whitelisted keys)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from core.config import db, logger

# ---------------------------------------------------------------------
# Mongo collection names + IDs
# ---------------------------------------------------------------------
CONFIG_COLLECTION = "bot_config"
POSTS_COLLECTION = "bot_posts"
CONFIG_SINGLETON_ID = "singleton"

# ---------------------------------------------------------------------
# Default bot config (used to seed the singleton on first boot)
# ---------------------------------------------------------------------
DEFAULT_BOT_CONFIG: Dict[str, Any] = {
    "_id": CONFIG_SINGLETON_ID,
    # SAFETY: the bot fleet starts in shutdown mode. The admin must
    # explicitly flip kill_switch_active to False to enable any posting.
    "kill_switch_active": True,
    "platforms": {
        "x": {"enabled": False, "post_frequency_hours": 4},
        "telegram": {"enabled": False, "post_frequency_hours": 6},
    },
    "content_modes": {
        "prophecy": True,
        "market_commentary": True,
        "vault_update": True,
        "kol_reply": False,
    },
    "llm": {
        # Default: Claude Sonnet 4.5 — best satirical voice for the Prophet.
        "provider": "anthropic",
        "model": "claude-sonnet-4-5-20250929",
    },
    # ---- News-feed inspiration (RSS aggregator) ----
    "news_feed": {
        "enabled_for": {"x": True, "telegram": False},
        "fetch_interval_hours": 6,  # 4×/jour (00, 06, 12, 18 UTC)
        "feeds": [],   # falls back to DEFAULT_NEWS_FEEDS when empty
        "keywords": [],  # falls back to DEFAULT_NEWS_KEYWORDS when empty
        "headlines_per_post": 5,
        "last_refresh_at": None,
        "last_refresh_stats": None,
    },
    # ---- Loyalty narrative (Sprints 3 + 4) ----
    "loyalty": {
        "hints_enabled": False,
        "email_enabled": False,
        "email_delay_hours": 12,
    },
    # ---- News repost (auto-relay top RSS headlines) ----
    "news_repost": {
        "enabled_for": {"x": False, "telegram": False},
        "interval_minutes": 30,
        "delay_after_refresh_minutes": 5,
        "wait_after_prophet_post_minutes": 2,
        "daily_cap": 10,
        "prefix_fr": "⚡ INTERCEPTÉ ·",
        "prefix_en": "⚡ INTERCEPT ·",
    },
    "heartbeat_interval_minutes": 5,
    "max_posts_per_day": 12,
    "last_updated_at": None,
    "updated_by": None,
    "created_at": None,
}

# Allow-list of keys patchable via the admin update endpoint. Centralised
# here so both the scheduler and the router stay in sync without one
# importing the other.
ALLOWED_PATCH_KEYS = {
    "kill_switch_active",
    "platforms",
    "content_modes",
    "llm",
    "news_feed",
    "loyalty",
    "news_repost",
    "heartbeat_interval_minutes",
    "max_posts_per_day",
}


# ---------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------
async def ensure_bot_config() -> Dict[str, Any]:
    """Return the bot config doc, creating it from defaults if absent."""
    doc = await db[CONFIG_COLLECTION].find_one({"_id": CONFIG_SINGLETON_ID})
    if doc is None:
        doc = dict(DEFAULT_BOT_CONFIG)
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        await db[CONFIG_COLLECTION].insert_one(doc)
        logger.info(
            "[bot_config_repo] bot_config initialized with safe defaults "
            "(kill-switch ON)."
        )
    return doc


async def get_bot_config() -> Dict[str, Any]:
    """Fast read of current bot config (raises only if Mongo is down)."""
    doc = await db[CONFIG_COLLECTION].find_one({"_id": CONFIG_SINGLETON_ID})
    return doc or await ensure_bot_config()


# ---------------------------------------------------------------------
# Write helper (NO scheduler side-effect — that's the scheduler's job)
# ---------------------------------------------------------------------
async def persist_bot_config_patch(
    patch: Dict[str, Any],
    *,
    updated_by: str = "admin",
) -> Dict[str, Any]:
    """Write a whitelisted partial patch into the config doc.

    This function ONLY persists. The caller (e.g. the scheduler) is
    responsible for refreshing live jobs after a successful update.
    """
    update: Dict[str, Any] = {}
    for key, value in (patch or {}).items():
        if key in ALLOWED_PATCH_KEYS:
            update[key] = value

    if not update:
        return await get_bot_config()

    update["last_updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = updated_by

    await db[CONFIG_COLLECTION].update_one(
        {"_id": CONFIG_SINGLETON_ID},
        {"$set": update},
        upsert=True,
    )
    return await get_bot_config()
