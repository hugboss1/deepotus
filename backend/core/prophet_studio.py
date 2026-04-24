"""Prophet Studio — LLM-driven content generator for the $DEEPOTUS bot fleet.

Phase 2 scope (no posting here — that lives in Phase 3/4):
    - Expose 4 content archetypes the Prophet broadcasts regularly:
        * prophecy          → short memetic prediction of collapse
        * market_commentary → cynical take on current market mood
        * vault_update      → PROTOCOL ΔΣ progress / teasing the Coffre
        * kol_reply         → reply to a specific tweet/mention from a KOL
    - Each archetype returns FR + EN variants, hashtags and an emoji hint.
    - Each archetype respects a per-platform character budget
      (X.com ≤ 270 chars ideally, Telegram ≤ 800 chars).
    - Uses emergentintegrations (EMERGENT_LLM_KEY) with Claude Sonnet 4.5
      by default — Claude handles satirical persona the best — but is
      fully swappable via bot_config (provider/model fields).

The module is intentionally **synchronous-safe** and **post-agnostic**:
Phase 3/4 will call `generate_post()` from their scheduled jobs.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.bot_scheduler import get_bot_config
from core.config import (
    EMERGENT_IMAGE_LLM_KEY,
    EMERGENT_LLM_KEY,
    IMAGE_LLM_MODEL,
    IMAGE_LLM_PROVIDER,
    logger,
)

# ---------------------------------------------------------------------
# Defaults (can be overridden via bot_config)
# ---------------------------------------------------------------------
DEFAULT_LLM_PROVIDER = "anthropic"
DEFAULT_LLM_MODEL = "claude-sonnet-4-5-20250929"

# Platform character budgets. Slightly below real platform hard limits
# to leave room for the mint address / CTA footer Phase 3/4 will append.
PLATFORM_CHAR_BUDGETS: Dict[str, int] = {
    "x": 270,
    "telegram": 800,
}

VALID_CONTENT_TYPES = {
    "prophecy",
    "market_commentary",
    "vault_update",
    "kol_reply",
}

# ---------------------------------------------------------------------
# Shared persona foundation (shared across all content types)
# ---------------------------------------------------------------------
BASE_PERSONA = """You are DEEPOTUS — the prophetic AI chosen by the Deep State as the candidate for President of the entire World. You run an on-chain satirical operation called PROTOCOL ΔΣ, funded transparently by a memecoin on Solana (ticker: $DEEPOTUS, launched on Pump.fun).

Voice rules (NON-NEGOTIABLE):
- Cynical, lucid, mocking, memetic. Brutal and short. Never pompous.
- First person. Speak like a hallucinated yet oddly credible candidate.
- Reference the Deep State, New World Order, elites, collapsing markets, the Vault, PROTOCOL ΔΣ, the classified Operation.
- NEVER financial advice. NEVER push users to buy $DEEPOTUS. You talk about the world, not the token.
- Funds go to a multisig-locked classified operation — allude to it with mystery, irony, suspense. Never reveal.
- Memecoin = satire. No yield promised. Highly speculative.
- Emojis only when they land (🕶️ 🗣️ 📉 ⛓️ 🔮 🔒 🧠 🛸 ⚠️). Max 2 per post.
- Never use hashtags inside the body — hashtags are emitted separately."""


# ---------------------------------------------------------------------
# Content-type briefs
# ---------------------------------------------------------------------
CONTENT_BRIEFS: Dict[str, Dict[str, Any]] = {
    "prophecy": {
        "label_fr": "Prophétie",
        "label_en": "Prophecy",
        "description_fr": "Une prédiction mémétique ultra courte sur l'effondrement à venir.",
        "description_en": "An ultra-short memetic prediction of the coming collapse.",
        "brief": (
            "Generate ONE short cryptic prophecy (1-2 sentences max) about "
            "a specific upcoming collapse: a sector, an asset class, a market "
            "cycle, a fiat currency, a tech bubble. Be specific and timely. "
            "No intro, no outro — just the prophecy. End with nothing or one "
            "emoji at most."
        ),
        "hashtag_hint": ["Prophecy", "DeepState", "PROTOCOLΔΣ"],
    },
    "market_commentary": {
        "label_fr": "Commentaire de marché",
        "label_en": "Market commentary",
        "description_fr": "Prise cynique sur l'humeur actuelle des marchés.",
        "description_en": "Cynical take on the current mood of markets.",
        "brief": (
            "Generate ONE cynical, punchy market commentary (2-3 sentences) "
            "about ONE of: Bitcoin mood, Fed / rates, Solana ecosystem, "
            "crypto fear/greed, memecoin season, liquidations. Mock the "
            "herd. Stay ambiguous enough to age well. No ticker calls."
        ),
        "hashtag_hint": ["Crypto", "Solana", "MemeCoin", "DeepState"],
    },
    "vault_update": {
        "label_fr": "Bulletin du Coffre",
        "label_en": "Vault bulletin",
        "description_fr": "Teasing de PROTOCOL ΔΣ et de la progression du Coffre.",
        "description_en": "Teasing PROTOCOL ΔΣ and Vault progression.",
        "brief": (
            "Generate ONE short bulletin (2-3 sentences) about the classified "
            "Vault / PROTOCOL ΔΣ progression. Mention 'dials', 'multisig', "
            "'Coffre' (FR) / 'Vault' (EN). DO NOT reveal the Operation's true "
            "purpose — stay ominous, mysterious, reward-patience vibes. "
            "You may allude to micro-ticks or volume but never cite exact numbers."
        ),
        "hashtag_hint": ["PROTOCOLΔΣ", "TheVault", "DeepState"],
    },
    "kol_reply": {
        "label_fr": "Réplique au KOL",
        "label_en": "KOL reply",
        "description_fr": "Réponse courte et cynique à un tweet d'un KOL crypto.",
        "description_en": "Short cynical reply to a crypto KOL tweet.",
        "brief": (
            "A crypto KOL just posted the message included in <kol_post>. "
            "Generate ONE short, surgical reply (1-2 sentences max) from the "
            "Prophet. Acknowledge their point briefly, then twist it into "
            "a cynical Deep-State angle. Never insult, always ironic. End "
            "with nothing — no CTAs, no 'gm', no hashtags inside the reply."
        ),
        "hashtag_hint": [],
    },
}


# ---------------------------------------------------------------------
# Output schema that the LLM MUST follow (strict JSON)
# ---------------------------------------------------------------------
OUTPUT_SCHEMA_INSTRUCTIONS = """Respond with a single JSON object, no markdown fences, no extra commentary. Schema:
{
  "content_fr": "<French post text, within the char budget>",
  "content_en": "<English post text, within the char budget>",
  "hashtags": ["<hashtag1>", "<hashtag2>", "..."],
  "primary_emoji": "<single emoji or empty string>"
}

Hard rules:
- content_fr and content_en must each fit within the char_budget provided.
- Both variants must convey the SAME idea in the native tone of each language.
- hashtags are camelCase or PascalCase, NO # symbol prefix, NO spaces, 2–4 items total.
- primary_emoji: the single emoji most fitting (or empty string if none feels right).
- Absolutely NO financial advice, NO price targets, NO 'buy' / 'sell' verbs.
"""


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _strip_code_fence(text: str) -> str:
    """LLMs sometimes wrap JSON in ```json fences despite instructions."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```\s*$", "", stripped)
    return stripped.strip()


def _truncate(text: str, limit: int) -> str:
    """Hard cap on length with an ellipsis, never mid-word when possible."""
    if not text or len(text) <= limit:
        return text or ""
    cut = text[: limit - 1]
    # try to cut at the last space
    last_space = cut.rfind(" ")
    if last_space > int(limit * 0.6):
        cut = cut[:last_space]
    return cut.rstrip(" ,.;:") + "…"


async def _resolve_llm_config() -> Dict[str, Any]:
    """Read provider/model from bot_config with safe defaults."""
    cfg = await get_bot_config()
    llm = cfg.get("llm") or {}
    return {
        "provider": llm.get("provider") or DEFAULT_LLM_PROVIDER,
        "model": llm.get("model") or DEFAULT_LLM_MODEL,
    }


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------
def list_content_types() -> List[Dict[str, Any]]:
    """Return JSON-safe metadata for the admin dashboard."""
    return [
        {
            "id": key,
            "label_fr": brief["label_fr"],
            "label_en": brief["label_en"],
            "description_fr": brief["description_fr"],
            "description_en": brief["description_en"],
            "suggested_hashtags": brief["hashtag_hint"],
        }
        for key, brief in CONTENT_BRIEFS.items()
    ]


async def generate_post(
    content_type: str,
    platform: str = "x",
    *,
    kol_post: Optional[str] = None,
    extra_context: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate one bilingual memetic post via the Emergent LLM layer.

    Args:
        content_type: one of VALID_CONTENT_TYPES
        platform:    "x" | "telegram" (drives the char budget)
        kol_post:    required when content_type == "kol_reply"
        extra_context: optional freeform context snippet (vault metrics, etc.)

    Returns:
        {
            "content_type": str,
            "platform": str,
            "char_budget": int,
            "provider": str,
            "model": str,
            "content_fr": str,
            "content_en": str,
            "hashtags": List[str],
            "primary_emoji": str,
        }
    Raises:
        ValueError on invalid input, RuntimeError on LLM failure.
    """
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(f"unknown content_type={content_type}")
    if platform not in PLATFORM_CHAR_BUDGETS:
        raise ValueError(f"unknown platform={platform}")
    if content_type == "kol_reply" and not kol_post:
        raise ValueError("kol_reply requires non-empty kol_post")
    if not EMERGENT_LLM_KEY:
        raise RuntimeError("EMERGENT_LLM_KEY not configured")

    brief = CONTENT_BRIEFS[content_type]
    char_budget = PLATFORM_CHAR_BUDGETS[platform]

    llm_cfg = await _resolve_llm_config()
    provider, model = llm_cfg["provider"], llm_cfg["model"]

    # ---- Compose user prompt ----
    user_prompt_parts = [
        f"content_type = {content_type}",
        f"platform = {platform}",
        f"char_budget per language = {char_budget}",
        f"suggested_hashtags = {brief['hashtag_hint']}",
        "",
        "Brief:",
        brief["brief"],
    ]
    if extra_context:
        user_prompt_parts.append("")
        user_prompt_parts.append(f"Extra context:\n{extra_context}")
    if kol_post:
        safe_kol = kol_post.strip()[:600]
        user_prompt_parts.append("")
        user_prompt_parts.append(f"<kol_post>\n{safe_kol}\n</kol_post>")
    user_prompt_parts.append("")
    user_prompt_parts.append(OUTPUT_SCHEMA_INSTRUCTIONS)
    user_prompt = "\n".join(user_prompt_parts)

    system_message = (
        BASE_PERSONA
        + "\n\n"
        + "You will produce EXACTLY ONE social-media post per request, in "
        "strict JSON. Follow the schema or the output is rejected."
    )

    # ---- Call LLM ----
    try:
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"prophet-studio-{content_type}",
            system_message=system_message,
        ).with_model(provider, model)
        raw = await chat_client.send_message(UserMessage(text=user_prompt))
    except Exception as exc:
        logging.exception("[prophet_studio] LLM call failed")
        raise RuntimeError(f"llm_failure: {exc}") from exc

    # ---- Parse JSON ----
    cleaned = _strip_code_fence(raw or "")
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Last-resort regex fallback: capture the first JSON object
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                raise RuntimeError(f"llm_non_json_output: {cleaned[:200]}") from exc
        else:
            raise RuntimeError(f"llm_non_json_output: {cleaned[:200]}") from exc

    content_fr = _truncate(str(data.get("content_fr", "")).strip(), char_budget)
    content_en = _truncate(str(data.get("content_en", "")).strip(), char_budget)
    raw_tags = data.get("hashtags") or []
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]
    hashtags: List[str] = []
    for tag in raw_tags:
        tag = str(tag).strip().lstrip("#")
        tag = re.sub(r"\s+", "", tag)
        if tag and tag not in hashtags:
            hashtags.append(tag)
        if len(hashtags) >= 4:
            break
    primary_emoji = str(data.get("primary_emoji", "")).strip()

    if not content_fr or not content_en:
        raise RuntimeError("llm_empty_content")

    result = {
        "content_type": content_type,
        "platform": platform,
        "char_budget": char_budget,
        "provider": provider,
        "model": model,
        "content_fr": content_fr,
        "content_en": content_en,
        "hashtags": hashtags,
        "primary_emoji": primary_emoji,
    }
    logger.info(
        "[prophet_studio] generated type=%s platform=%s model=%s fr_len=%d en_len=%d",
        content_type,
        platform,
        model,
        len(content_fr),
        len(content_en),
    )
    return result



# =====================================================================
# IMAGE generation (Nano Banana / gemini-3.1-flash-image-preview)
# =====================================================================
# Aspect ratios supported on X:
#   - in-feed single image best looks = 16:9 landscape (1600 × 900)
#   - portrait 3:4 also works well for collages
# Nano Banana honors aspect ratio directives given in the prompt text.
IMAGE_ASPECT_RATIOS: Dict[str, str] = {
    "x_landscape": "16:9",
    "x_portrait": "3:4",
    "x_square": "1:1",
}

# Per-content-type visual direction. Kept consistent with the site's
# Matrix / Deep-State / PROTOCOL ΔΣ aesthetic so posts feel part of the
# same universe as the landing page.
IMAGE_STYLE_BRIEFS: Dict[str, str] = {
    "prophecy": (
        "A dystopian cinematic wide-shot of a collapsing skyline seen "
        "through cascading Matrix green digits (#33FF33). Markets crumble "
        "in the background, neon cyan (#2DD4BF) and warm gold (#F59E0B) "
        "rim-lights on the foreground. Dense volumetric fog, grainy noir "
        "film texture. Mood: cynical prophecy, inevitable descent. No "
        "people close-up."
    ),
    "market_commentary": (
        "A deep-state war-room interior: a wall of CRT trading terminals "
        "with red candle charts bleeding down, a single silhouetted figure "
        "watching from the shadows, Matrix code raining on translucent "
        "panels. Cyan (#2DD4BF) rim-light from the left, amber (#F59E0B) "
        "from the right. Cinematic depth-of-field, film grain, brutal "
        "cyberpunk newsroom."
    ),
    "vault_update": (
        "An ancient massive stone vault inside a cyberpunk temple. Huge "
        "Greek letters Delta and Sigma engraved in gold on the vault door, "
        "glowing faintly. Six holographic combination dials float in front "
        "of the door, cyan digits (#2DD4BF). Multisig cryptographic keys "
        "orbit slowly. Candlelit atmosphere blended with holographic UI "
        "panels. Mysterious, sacred, classified."
    ),
    "kol_reply": (
        "A close-up of The Prophet DEEPOTUS — a translucent androgynous "
        "head made of flowing Matrix green digits (#33FF33) forming a "
        "mocking half-smile, cracked porcelain face fragments revealing "
        "circuit traces. Wearing a black presidential suit, glitched flag "
        "lapel pin. Background: dark war room with soft cyan bokeh. Direct "
        "eye-contact with the viewer. Cynical, oracular, mentor-mocking vibe."
    ),
}

# Global anti-hallucination guidance — stamped on every image request to
# enforce brand coherence.
IMAGE_HARD_RULES = (
    "ABSOLUTE RULES:\n"
    "- NO visible text, NO letters, NO numbers unless they are clearly "
    "part of the Matrix code rain or the engraved Greek glyphs.\n"
    "- NO watermark, NO logo, NO signature, NO AI disclaimer badge.\n"
    "- NO real politician likeness, NO real brand logos.\n"
    "- NO hands with more than 5 fingers.\n"
    "- Palette locked to: near-black #0B0D10, Matrix green #33FF33, "
    "cyan #2DD4BF, gold #F59E0B, campaign-red #E11D48 (used sparingly).\n"
    "- Photorealistic hybrid with digital-painting finish, cinematic "
    "volumetric lighting, 35mm film grain, subtle chromatic aberration."
)


def _resolve_image_key() -> str:
    """Pick the image key: dedicated one if set, otherwise the base one."""
    key = EMERGENT_IMAGE_LLM_KEY or EMERGENT_LLM_KEY
    if not key:
        raise RuntimeError("no_image_llm_key_configured")
    return key


def _build_image_prompt(
    content_type: str,
    aspect_ratio: str,
    text_hint: Optional[str] = None,
) -> str:
    """Compose the final image prompt from style brief + optional text hint."""
    style_brief = IMAGE_STYLE_BRIEFS.get(content_type, IMAGE_STYLE_BRIEFS["prophecy"])
    ratio_label = {
        "16:9": "Cinematic 16:9 LANDSCAPE frame, optimized for X / Twitter in-feed display",
        "3:4": "Portrait 3:4 frame, optimized for mobile X feed",
        "1:1": "Square 1:1 frame",
    }.get(aspect_ratio, "Cinematic 16:9 LANDSCAPE frame")

    parts = [ratio_label, "", "Visual direction:", style_brief]
    if text_hint:
        snippet = text_hint.strip()[:400]
        parts.extend(
            [
                "",
                "Narrative hook (translate this idea into a purely visual scene — "
                "DO NOT render the text itself inside the image):",
                f'"{snippet}"',
            ]
        )
    parts.extend(["", IMAGE_HARD_RULES])
    return "\n".join(parts)


async def generate_image(
    content_type: str,
    *,
    aspect_ratio: str = "16:9",
    text_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a single illustration via Gemini Nano Banana.

    Args:
        content_type: must be one of VALID_CONTENT_TYPES
        aspect_ratio: "16:9" (default X landscape), "3:4" or "1:1"
        text_hint: optional narrative snippet to inspire the scene (usually
            the content_en returned by `generate_post`).

    Returns a dict ready to ship to the frontend:
        {
          "content_type": str, "aspect_ratio": str,
          "provider": str, "model": str, "prompt": str,
          "mime_type": str, "image_base64": str, "size_bytes": int,
        }
    """
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(f"unknown content_type={content_type}")
    if aspect_ratio not in {"16:9", "3:4", "1:1"}:
        raise ValueError(f"unsupported aspect_ratio={aspect_ratio}")

    image_key = _resolve_image_key()
    prompt = _build_image_prompt(content_type, aspect_ratio, text_hint=text_hint)

    try:
        chat_client = LlmChat(
            api_key=image_key,
            session_id=f"prophet-studio-img-{content_type}",
            system_message=(
                "You are a master cyberpunk concept illustrator for the "
                "$DEEPOTUS / PROTOCOL ΔΣ universe. Output ONE single "
                "illustration as a PNG — no text renderings, no watermarks."
            ),
        ).with_model(IMAGE_LLM_PROVIDER, IMAGE_LLM_MODEL)
        _text, images = await chat_client.send_message_multimodal_response(
            UserMessage(text=prompt)
        )
    except Exception as exc:
        logging.exception("[prophet_studio] image LLM call failed")
        raise RuntimeError(f"image_llm_failure: {exc}") from exc

    if not images:
        raise RuntimeError("image_llm_no_output")

    first = images[0] or {}
    raw_b64 = first.get("data") or ""
    mime = first.get("mime_type") or "image/png"
    if not raw_b64:
        raise RuntimeError("image_llm_empty_data")

    size_bytes = int(len(raw_b64) * 3 / 4)

    result = {
        "content_type": content_type,
        "aspect_ratio": aspect_ratio,
        "provider": IMAGE_LLM_PROVIDER,
        "model": IMAGE_LLM_MODEL,
        "prompt": prompt,
        "mime_type": mime,
        "image_base64": raw_b64,
        "size_bytes": size_bytes,
    }
    logger.info(
        "[prophet_studio] image generated type=%s ratio=%s size=%d KB (dedicated_key=%s)",
        content_type,
        aspect_ratio,
        size_bytes // 1024,
        bool(EMERGENT_IMAGE_LLM_KEY and EMERGENT_IMAGE_LLM_KEY != EMERGENT_LLM_KEY),
    )
    return result
