"""Tone Engine — LLM-augmented template variation.

Core design choice: **70 % templates / 30 % LLM** as agreed in Sprint 13.
For each fire we either ship the template verbatim (cheap, predictable,
on-message) or we ask the LLM to *re-write* it in the same voice while
strictly preserving placeholders. We never ask the LLM to invent a new
message from scratch — that's how you get bot slop.

Safety guards built into the prompt + post-processing:
  * keep the message under the platform char budget (Twitter 280),
  * never strip the placeholder tokens (``{buy_link}``, ``{mc_label}``…),
  * never add hashtags or emoji (the persona is 'weary intelligence
    officer', not 'crypto influencer'),
  * if the LLM call fails for any reason, fall back to the original
    template silently — the engine must always produce a message.

The personality prompt is stored in ``propaganda_settings`` so the
admin can tune it from the UI without touching code.
"""

from __future__ import annotations

import logging
import secrets
import re
import uuid
from typing import Any, Dict, Optional

from core.config import db
from core.secret_provider import get_emergent_llm_key

logger = logging.getLogger("deepotus.propaganda.tone")

# `secrets.SystemRandom` is used for every non-crypto pick below to keep
# the tone engine unpredictable across dispatches. It's not strictly
# required (cosmetic randomness), but ruff's `S311` audit flags the stdlib
# `random` module here and this change is free.
_rand = secrets.SystemRandom()

# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------
DEFAULT_PERSONALITY_PROMPT = (
    "You are a weary 50-year-old intelligence officer who has seen too "
    "much. Your tone is unimpressed by small gains, mockingly arrogant "
    "toward panic-sellers, and speaks in riddles about 'The Vault' and "
    "'The Elites'. Use terminology like: Redacted, Classified, Clearance "
    "Level, Signal vs Noise, The Bunker.\n\n"
    "TASK: Rewrite the user message in your voice. Keep its core meaning "
    "100% intact. Keep ALL placeholder tokens (anything in curly braces "
    "like {buy_link}, {mc_label}, {whale_amount}) EXACTLY as they appear "
    "— do not translate, paraphrase or remove them. Stay under 260 chars. "
    "NEVER use hashtags, emoji, or marketing buzzwords. Reply with ONLY "
    "the rewritten message, nothing else."
)

MAX_OUTPUT_CHARS = 280
FALLBACK_PROVIDER = "openai"
FALLBACK_MODEL = "gpt-4o-mini"

# Tokens we never want to leak into a propaganda message regardless of
# what the LLM tries.
_FORBIDDEN_PATTERNS = [
    re.compile(r"#[A-Za-z0-9_]+"),                     # hashtags
    re.compile(r"[\U0001F300-\U0001FAFF\U00002700-\U000027BF]"),  # emoji
]


# ---------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------
async def get_tone_settings() -> Dict[str, Any]:
    """Read tone-related fields out of ``propaganda_settings``. Hydrates
    them with defaults so every caller sees a complete view."""
    doc = await db.propaganda_settings.find_one({"_id": "settings"}) or {}
    return {
        "llm_enabled": bool(doc.get("llm_enabled", True)),
        "llm_enhance_ratio": float(doc.get("llm_enhance_ratio", 0.30)),
        "personality_prompt": doc.get("personality_prompt")
            or DEFAULT_PERSONALITY_PROMPT,
        "llm_provider": doc.get("llm_provider") or FALLBACK_PROVIDER,
        "llm_model": doc.get("llm_model") or FALLBACK_MODEL,
    }


async def patch_tone_settings(
    *,
    llm_enabled: Optional[bool] = None,
    llm_enhance_ratio: Optional[float] = None,
    personality_prompt: Optional[str] = None,
    llm_provider: Optional[str] = None,
    llm_model: Optional[str] = None,
) -> Dict[str, Any]:
    patch: Dict[str, Any] = {}
    if llm_enabled is not None:
        patch["llm_enabled"] = bool(llm_enabled)
    if llm_enhance_ratio is not None:
        patch["llm_enhance_ratio"] = float(
            max(0.0, min(float(llm_enhance_ratio), 1.0))
        )
    if personality_prompt is not None:
        text = (personality_prompt or "").strip()
        if not text:
            raise ValueError("personality_prompt cannot be empty")
        if len(text) > 4000:
            raise ValueError("personality_prompt too long (max 4000 chars)")
        patch["personality_prompt"] = text
    if llm_provider is not None:
        patch["llm_provider"] = (llm_provider or "").strip().lower() or FALLBACK_PROVIDER
    if llm_model is not None:
        patch["llm_model"] = (llm_model or "").strip() or FALLBACK_MODEL
    if patch:
        await db.propaganda_settings.update_one(
            {"_id": "settings"}, {"$set": patch}, upsert=True,
        )
    return await get_tone_settings()


# ---------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------
async def maybe_enhance(
    rendered_content: str,
    *,
    locale: str = "en",
    forced: bool = False,
) -> Dict[str, Any]:
    """Decide whether to push this message through the LLM rewriter.

    Returns a dict ``{content, used_llm, source}`` where ``content`` is
    always usable (the original template when the LLM is disabled, when
    the dice roll says ‘skip’, when no API key is available, or when the
    LLM call itself fails).
    """
    settings = await get_tone_settings()
    if not settings["llm_enabled"] and not forced:
        return {"content": rendered_content, "used_llm": False, "source": "template_only"}

    if not forced:
        ratio = settings["llm_enhance_ratio"]
        if ratio <= 0 or _rand.random() > ratio:
            return {"content": rendered_content, "used_llm": False, "source": "template_only"}

    api_key = await get_emergent_llm_key()
    if not api_key:
        logger.info("[tone_engine] no LLM key available — falling back to template.")
        return {"content": rendered_content, "used_llm": False, "source": "no_key"}

    rewritten = await _rewrite_with_llm(
        api_key=api_key,
        provider=settings["llm_provider"],
        model=settings["llm_model"],
        system_prompt=settings["personality_prompt"],
        user_message=rendered_content,
        locale=locale,
    )
    safe = _post_process(rewritten or "", template=rendered_content)
    if not safe:
        return {
            "content": rendered_content,
            "used_llm": False,
            "source": "llm_post_process_dropped",
        }
    return {"content": safe, "used_llm": True, "source": "llm_rewrite"}


# ---------------------------------------------------------------------
# LLM call (lazy import to avoid hard runtime dep when unused)
# ---------------------------------------------------------------------
async def _rewrite_with_llm(
    *,
    api_key: str,
    provider: str,
    model: str,
    system_prompt: str,
    user_message: str,
    locale: str,
) -> Optional[str]:
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # lazy

        # Locale hint helps the LLM keep the FR / EN voice consistent.
        sys_msg = system_prompt + (
            "\n\nLanguage: respond in French if the input message is in French, "
            "otherwise respond in English."
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"propaganda-tone-{uuid.uuid4().hex[:10]}",
            system_message=sys_msg,
        ).with_model(provider, model)
        out = await chat.send_message(
            UserMessage(text=f"REWRITE THIS:\n\n{user_message}"),
        )
        return (out or "").strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("[tone_engine] LLM rewrite failed: %s", exc)
        return None


# ---------------------------------------------------------------------
# Post-processing & validation
# ---------------------------------------------------------------------
_PLACEHOLDER_RE = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}")


def _post_process(text: str, *, template: str) -> str:
    """Sanitise the LLM output. Returns ``''`` to signal a fallback.

    Rules:
      1. Trim, collapse whitespace.
      2. Strip hashtags + emoji.
      3. Truncate to MAX_OUTPUT_CHARS at a clean word boundary.
      4. Confirm every placeholder present in the original template is
         still present in the output — otherwise we'd ship a message
         with a missing buy link, etc.
      5. Refuse outputs shorter than 8 chars (defensive).
    """
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    # 1. whitespace cleanup
    cleaned = re.sub(r"\s+", " ", cleaned)
    # 2. strip forbidden patterns
    for pat in _FORBIDDEN_PATTERNS:
        cleaned = pat.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -—•·")
    # 3. truncate at boundary
    if len(cleaned) > MAX_OUTPUT_CHARS:
        cut = cleaned[:MAX_OUTPUT_CHARS].rsplit(" ", 1)[0]
        cleaned = cut.rstrip(" .,;:—-") + "…"
    # 4. placeholder integrity
    expected = set(_PLACEHOLDER_RE.findall(template))
    got = set(_PLACEHOLDER_RE.findall(cleaned))
    if expected and not expected.issubset(got):
        logger.info(
            "[tone_engine] LLM dropped placeholders %s — falling back.",
            expected - got,
        )
        return ""
    # 5. minimum length
    if len(cleaned) < 8:
        return ""
    return cleaned
