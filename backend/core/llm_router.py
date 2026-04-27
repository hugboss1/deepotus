"""LLM call router — picks between admin-supplied custom keys (native SDKs)
and the Emergent universal key (`emergentintegrations`).

Decision tree per call:

    ┌───────────────────────────────────────────────────────────┐
    │ resolve_llm_call(provider, model, system, user)          │
    │                                                           │
    │   custom = await get_custom_llm_key(provider)            │
    │   if custom:                                              │
    │       return await _call_native(provider, model, custom,  │
    │                                  system, user)            │
    │   else:                                                   │
    │       return await _call_emergent(provider, model,        │
    │                                    system, user)          │
    └───────────────────────────────────────────────────────────┘

Per the user's choice (Tier-2a in the security review), there is NO
silent fallback from a custom key to the Emergent key — if the custom
key fails, the error surfaces to the admin so they know their key is
broken and not silently consuming Emergent credits.

Public API:
    async resolve_llm_call(provider, model, system_message, user_prompt) -> str
    async load_custom_keys_status() -> Dict[provider, {"active": bool, "fingerprint": str, "label": str, "set_at": str}]
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import InvalidToken

from core.config import db
from core import secret_provider
from core.secret_provider import get_emergent_llm_key
from core.secrets_vault import (
    decrypt,
    is_kek_configured,
    mask_for_display,
)

logger = logging.getLogger("deepotus.llm_router")

# Subset of bot_config we look at — keep in sync with bot_scheduler defaults.
CONFIG_COLLECTION = "bot_config"
CONFIG_SINGLETON_ID = "bot_config_singleton"

SUPPORTED_PROVIDERS = ("openai", "anthropic", "gemini")


# ---------------------------------------------------------------------
# Custom key access (decrypt-on-read, never cached)
# ---------------------------------------------------------------------
async def _read_custom_key_doc(provider: str) -> Optional[Dict[str, Any]]:
    """Pull the encrypted slot for `provider` from the bot_config doc."""
    if provider not in SUPPORTED_PROVIDERS:
        return None
    doc = await db[CONFIG_COLLECTION].find_one({"_id": CONFIG_SINGLETON_ID})
    if not doc:
        return None
    bag = (doc.get("custom_llm_keys") or {}).get(provider)
    if not bag or not bag.get("ciphertext"):
        return None
    return bag


async def get_custom_llm_key(provider: str) -> Optional[str]:
    """Return the decrypted plaintext API key for `provider`, or None.

    Resolution order (Sprint 12.4):
      1. **Cabinet Vault** category=llm_custom, key=<PROVIDER>_API_KEY.
         Honoured only when the vault is unlocked. Plaintext never logged.
      2. **Legacy Fernet vault** stored on the bot_config singleton.
         Kept active during transition so existing deployments keep
         working until the admin migrates their keys to the Cabinet.
      3. ``None`` — caller falls back to the Emergent universal key.

    Logs ONLY the masked fingerprint — never the plaintext.
    """
    # 1) Cabinet Vault (preferred)
    cabinet_key_name = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider)
    if cabinet_key_name:
        cabinet_val = await secret_provider.resolve(
            "llm_custom",
            cabinet_key_name,
            env_var=cabinet_key_name,
        )
        if cabinet_val:
            logger.info(
                "[llm_router] custom-key source=CABINET provider=%s mask=%s",
                provider,
                mask_for_display(cabinet_val),
            )
            return cabinet_val

    # 2) Legacy Fernet vault — kept until admin migrates to Cabinet Vault
    bag = await _read_custom_key_doc(provider)
    if not bag:
        return None
    try:
        plaintext = decrypt(bag["ciphertext"])
    except InvalidToken as exc:
        logger.error(
            "[llm_router] decrypt failed for provider=%s mask=%s: %s",
            provider,
            bag.get("mask", "—"),
            exc,
        )
        return None
    logger.info(
        "[llm_router] custom-key source=LEGACY_FERNET provider=%s mask=%s",
        provider,
        mask_for_display(plaintext),
    )
    return plaintext


async def load_custom_keys_status() -> Dict[str, Dict[str, Any]]:
    """Build the public, plaintext-free shape used by the admin GET config.

    The shape EXPLICITLY excludes the ciphertext so a logging mishap
    or response leak cannot trickle real key material out.
    """
    doc = await db[CONFIG_COLLECTION].find_one({"_id": CONFIG_SINGLETON_ID})
    bag_root = ((doc or {}).get("custom_llm_keys") or {})
    out: Dict[str, Dict[str, Any]] = {}
    for provider in SUPPORTED_PROVIDERS:
        bag = bag_root.get(provider) or {}
        out[provider] = {
            "active": bool(bag.get("ciphertext")),
            "mask": bag.get("mask") or "",
            "label": bag.get("label") or "",
            "set_at": bag.get("set_at"),
            "rotated_at": bag.get("rotated_at"),
        }
    out["_meta"] = {
        "kek_configured": is_kek_configured(),
        "supported_providers": list(SUPPORTED_PROVIDERS),
    }
    return out


# ---------------------------------------------------------------------
# Native SDK call paths
# ---------------------------------------------------------------------
async def _call_native_openai(
    api_key: str, model: str, system_message: str, user_prompt: str
) -> str:
    """Call OpenAI's Chat Completions API with the admin's own key."""
    from openai import AsyncOpenAI  # lazy import — keeps cold-start light

    client = AsyncOpenAI(api_key=api_key)
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=900,
    )
    return resp.choices[0].message.content or ""


async def _call_native_anthropic(
    api_key: str, model: str, system_message: str, user_prompt: str
) -> str:
    """Call Anthropic's Messages API with the admin's own key."""
    from anthropic import AsyncAnthropic  # lazy import

    client = AsyncAnthropic(api_key=api_key)
    resp = await client.messages.create(
        model=model,
        system=system_message,
        max_tokens=900,
        messages=[{"role": "user", "content": user_prompt}],
    )
    # Concat all text blocks (Anthropic returns a list of content parts)
    chunks = [
        getattr(block, "text", "")
        for block in resp.content
        if getattr(block, "type", "") == "text"
    ]
    return "".join(chunks)


async def _call_native_gemini(
    api_key: str, model: str, system_message: str, user_prompt: str
) -> str:
    """Call Google AI Studio Gemini API with the admin's own key."""
    import google.generativeai as genai  # lazy import

    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(
        model_name=model, system_instruction=system_message
    )
    # google-generativeai exposes a synchronous .generate_content_async method
    resp = await model_obj.generate_content_async(user_prompt)
    return getattr(resp, "text", "") or ""


_NATIVE_DISPATCH = {
    "openai": _call_native_openai,
    "anthropic": _call_native_anthropic,
    "gemini": _call_native_gemini,
}


# ---------------------------------------------------------------------
# Emergent (default) call path — uses LlmChat
# ---------------------------------------------------------------------
async def _call_emergent(
    provider: str, model: str, system_message: str, user_prompt: str
) -> str:
    """Fallback path — relies on the Emergent universal key resolved at
    call time so admins can rotate the key via the Cabinet Vault without
    restarting the process."""
    api_key = await get_emergent_llm_key()
    if not api_key:
        raise RuntimeError(
            "EMERGENT_LLM_KEY not configured and no custom key set "
            f"for provider={provider}"
        )
    from emergentintegrations.llm.chat import LlmChat, UserMessage  # lazy

    chat = LlmChat(
        api_key=api_key,
        session_id=f"prophet-router-{provider}",
        system_message=system_message,
    ).with_model(provider, model)
    return await chat.send_message(UserMessage(text=user_prompt))


# ---------------------------------------------------------------------
# Public entrypoint used by Prophet Studio
# ---------------------------------------------------------------------
async def resolve_llm_call(
    provider: str,
    model: str,
    system_message: str,
    user_prompt: str,
) -> str:
    """Pick custom-native vs. Emergent, run the call, return the text.

    Per the user's product decision (security review tier 2a), if a
    custom key is configured for `provider` we DO NOT silently fall
    back to Emergent on failure — the exception bubbles up so the
    admin notices a broken / depleted key.
    """
    custom_key = await get_custom_llm_key(provider)
    if custom_key:
        if provider not in _NATIVE_DISPATCH:
            raise ValueError(
                f"Custom key configured for unsupported provider={provider}"
            )
        try:
            logger.info(
                "[llm_router] route=NATIVE provider=%s model=%s mask=%s",
                provider,
                model,
                mask_for_display(custom_key),
            )
            return await _NATIVE_DISPATCH[provider](
                custom_key, model, system_message, user_prompt
            )
        except Exception as exc:  # noqa: BLE001
            # Re-raise WITHOUT the plaintext key in the message.
            logger.exception(
                "[llm_router] native call failed provider=%s model=%s",
                provider,
                model,
            )
            raise RuntimeError(
                f"Custom {provider} key call failed: {type(exc).__name__}: "
                f"{str(exc)[:200]}"
            ) from None  # `from None` strips the original traceback context

    logger.info(
        "[llm_router] route=EMERGENT provider=%s model=%s",
        provider,
        model,
    )
    return await _call_emergent(provider, model, system_message, user_prompt)


# ---------------------------------------------------------------------
# Helpers used by the admin endpoint when persisting a new key
# ---------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
