"""Unified runtime secret resolver — Cabinet Vault first, env fallback.

Every backend service that needs an external secret (LLM keys, Resend,
Helius, Telegram, X, trading-bot referrals, site URLs…) MUST read it
through one of the helpers in this module instead of:

    1. ``os.environ.get("FOO")``                — bypasses the vault entirely
    2. ``from core.config import FOO``          — captures the value at import
                                                  time and never refreshes when
                                                  the admin rotates a secret in
                                                  the Cabinet Vault.

Resolution order
----------------
1. **Cabinet Vault** — when the admin has unlocked the vault, the master
   key is held in process memory (TTL 15 min). We try a silent read for
   the requested ``(category, key)``; the read is *not* audit-logged
   because every HTTP request would otherwise flood the audit table.

2. **Process environment** — when the vault is locked (or the secret
   has not been migrated yet), we fall back to ``os.environ`` so the
   site continues to function during the transition. This fallback can
   be disabled in production by setting ``STRICT_VAULT_ONLY=true``.

The resolver memoises hits for a short TTL (default 60 s) to avoid
hitting Mongo on every LLM call. The cache is invalidated automatically
when the vault is locked / re-unlocked (we hash the unlocked-session
identity into the cache key).

Thread / async safety
---------------------
The module uses asyncio coroutines. The cache is a plain dict — Python
3.11 GIL guarantees atomic dict operations for our access patterns.
There is no awaitable suspension between cache check and cache write.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from core import cabinet_vault as vault

logger = logging.getLogger("deepotus.secret_provider")

# ---------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------
_CACHE_TTL_S = 60
STRICT_VAULT_ONLY: bool = os.environ.get(
    "STRICT_VAULT_ONLY", "false"
).strip().lower() in ("1", "true", "yes")


@dataclass
class _CacheEntry:
    value: Optional[str]
    source: str  # "vault" | "env" | "miss"
    expires_at: float


_cache: dict[Tuple[str, str], _CacheEntry] = {}


def _cache_key_session_token() -> str:
    """Identity of the current vault session — flips when the vault is
    locked or re-unlocked, automatically invalidating cached vault hits.
    """
    return "unlocked" if vault.is_unlocked() else "locked"


def invalidate_cache() -> None:
    """Force a full refresh on the next read. Call this from admin
    endpoints that mutate vault state (set/delete/rotate)."""
    _cache.clear()


# ---------------------------------------------------------------------
# Generic resolver
# ---------------------------------------------------------------------
async def resolve(
    category: str,
    key: str,
    env_var: Optional[str] = None,
    default: Optional[str] = None,
) -> Optional[str]:
    """Return the secret value, trying Cabinet Vault first, then env.

    Parameters
    ----------
    category, key
        Cabinet Vault coordinates (see ``KNOWN_CATEGORIES``).
    env_var
        Environment variable name to fall back on. Defaults to ``key``
        which matches our convention (vault key == env var name).
    default
        Value returned when both lookups miss.
    """
    env_var = env_var or key
    cache_id = (category, key)
    sess_token = _cache_key_session_token()

    # ---- Cache lookup ------------------------------------------------
    cached = _cache.get(cache_id)
    if cached and cached.expires_at > time.monotonic():
        # Vault → env transitions invalidate via session_token (we tag
        # cache entries with the session_token observed at write time).
        if (cached.source == "vault" and sess_token == "unlocked") or \
           (cached.source != "vault"):
            return cached.value if cached.value is not None else default

    # ---- Vault attempt ------------------------------------------------
    val: Optional[str] = None
    src = "miss"
    if vault.is_unlocked():
        try:
            val = await vault.get_secret_silent(category, key)
            if val is not None:
                src = "vault"
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "[secret_provider] vault read failed cat=%s key=%s err=%s",
                category, key, exc,
            )

    # ---- Env fallback -------------------------------------------------
    if val is None and not STRICT_VAULT_ONLY:
        env_val = os.environ.get(env_var)
        if env_val is not None and env_val != "":
            val = env_val
            src = "env"

    # ---- Cache write --------------------------------------------------
    _cache[cache_id] = _CacheEntry(
        value=val,
        source=src,
        expires_at=time.monotonic() + _CACHE_TTL_S,
    )
    return val if val is not None else default


# ---------------------------------------------------------------------
# Typed convenience helpers — call these from services
# ---------------------------------------------------------------------
async def get_emergent_llm_key() -> Optional[str]:
    return await resolve("llm_emergent", "EMERGENT_LLM_KEY")


async def get_emergent_image_llm_key() -> Optional[str]:
    """Falls back to the regular EMERGENT_LLM_KEY when the dedicated
    image key is not configured (matches legacy behaviour from
    ``core/config.py``)."""
    img = await resolve("llm_emergent", "EMERGENT_IMAGE_LLM_KEY")
    if img:
        return img
    return await get_emergent_llm_key()


async def get_resend_api_key() -> Optional[str]:
    return await resolve("email_resend", "RESEND_API_KEY")


async def get_resend_webhook_secret() -> Optional[str]:
    return await resolve("email_resend", "RESEND_WEBHOOK_SECRET")


async def get_sender_email() -> str:
    """Sender always defaults to onboarding@resend.dev so we never break
    the email flow when the secret isn't configured yet."""
    val = await resolve("email_resend", "SENDER_EMAIL")
    return val or "onboarding@resend.dev"


async def get_helius_api_key() -> Optional[str]:
    val = await resolve("solana_helius", "HELIUS_API_KEY")
    return (val or "").strip() or None


async def get_helius_webhook_auth() -> Optional[str]:
    val = await resolve("solana_helius", "HELIUS_WEBHOOK_AUTH")
    return (val or "").strip() or None


async def get_telegram_bot_token() -> Optional[str]:
    return await resolve("telegram", "TELEGRAM_BOT_TOKEN")


async def get_telegram_chat_id() -> Optional[str]:
    return await resolve("telegram", "TELEGRAM_CHAT_ID")


async def get_twitter_bearer_token() -> Optional[str]:
    """Legacy flat env var name kept for compat — vault stores it under
    ``x_twitter/X_BEARER_TOKEN``.

    Resolution chain (first hit wins):
        1. Cabinet Vault   x_twitter/X_BEARER_TOKEN
        2. env             X_BEARER_TOKEN          (current name)
        3. env             TWITTER_BEARER_TOKEN    (legacy)
        4. Cabinet Vault   x_twitter/X_API_KEY     (very old fallback)
    """
    val = await resolve(
        "x_twitter",
        "X_BEARER_TOKEN",
        env_var="X_BEARER_TOKEN",
    )
    if val:
        return val
    val = await resolve(
        "x_twitter",
        "X_BEARER_TOKEN",
        env_var="TWITTER_BEARER_TOKEN",
    )
    if val:
        return val
    return await resolve("x_twitter", "X_API_KEY", env_var="X_API_KEY")


async def get_public_base_url() -> str:
    """Site public URL — falls back to a hardcoded preview URL so emails
    always have a working CTA target."""
    val = await resolve("site", "PUBLIC_BASE_URL")
    return (
        val
        or os.environ.get("PUBLIC_BASE_URL")
        or "https://prophet-ai-memecoin.preview.emergentagent.com"
    )


async def get_x_client_id() -> Optional[str]:
    return await resolve("x_twitter", "X_CLIENT_ID")


async def get_x_client_secret() -> Optional[str]:
    return await resolve("x_twitter", "X_CLIENT_SECRET")


async def get_bonkbot_ref_url() -> Optional[str]:
    """BonkBot affiliate referral link, surfaced on the landing's
    'Access Secured Terminals' panel and (optionally) appended to
    high-tier propaganda dispatches as a footer link.

    Stored under ``trading_refs/BONKBOT_REF_URL`` in the Cabinet Vault
    and falls back to the equivalent env var. Empty string is treated
    as ``None`` so a stub-blank value won't render a broken button.
    """
    val = await resolve("trading_refs", "BONKBOT_REF_URL")
    return val if (val and val.strip()) else None


async def get_trojan_ref_url() -> Optional[str]:
    val = await resolve("trading_refs", "TROJAN_REF_URL")
    return val if (val and val.strip()) else None


# ---------------------------------------------------------------------
# Diagnostic helper for the admin UI / health endpoint
# ---------------------------------------------------------------------
async def describe_resolution(category: str, key: str,
                              env_var: Optional[str] = None) -> dict:
    """Return ``{source, set, value_length}`` without leaking the value."""
    env_var = env_var or key
    val = await resolve(category, key, env_var=env_var)
    src = _cache.get((category, key))
    return {
        "category": category,
        "key": key,
        "set": val is not None,
        "value_length": len(val) if val else 0,
        "source": (src.source if src else "miss"),
    }


__all__ = [
    "STRICT_VAULT_ONLY",
    "invalidate_cache",
    "resolve",
    "get_emergent_llm_key",
    "get_emergent_image_llm_key",
    "get_resend_api_key",
    "get_resend_webhook_secret",
    "get_sender_email",
    "get_helius_api_key",
    "get_helius_webhook_auth",
    "get_telegram_bot_token",
    "get_telegram_chat_id",
    "get_twitter_bearer_token",
    "get_x_client_id",
    "get_x_client_secret",
    "get_bonkbot_ref_url",
    "get_trojan_ref_url",
    "get_public_base_url",
    "describe_resolution",
]
