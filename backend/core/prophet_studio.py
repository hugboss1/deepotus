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
import random
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.llm_compat import LlmChat, UserMessage

from core.bot_config_repo import get_bot_config
from core.config import (
    IMAGE_LLM_MODEL,
    IMAGE_LLM_PROVIDER,
    db,
    logger,
)
from core.secret_provider import (
    get_emergent_image_llm_key,
    get_emergent_llm_key,
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
    "loyalty_hero",
    "welcome_hero",
    "accreditation_hero",
    "prophet_update_hero",
    "tokenomics_public",
    "tokenomics_treasury",
    "tokenomics_shadows",
    "tokenomics_burn",
    "transparency_distribution",
    "transparency_rugcheck",
    "transparency_operations",
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


def _validate_generate_inputs(
    content_type: str,
    platform: str,
    kol_post: Optional[str],
) -> None:
    """Raise ValueError on bad input combinations.

    Note: EMERGENT_LLM_KEY presence is validated at call-time inside
    ``generate_post`` (it's resolved dynamically via the SecretProvider
    so admins can rotate it through the Cabinet Vault without restart).
    """
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(f"unknown content_type={content_type}")
    if platform not in PLATFORM_CHAR_BUDGETS:
        raise ValueError(f"unknown platform={platform}")
    if content_type == "kol_reply" and not kol_post:
        raise ValueError("kol_reply requires non-empty kol_post")


def _build_user_prompt(
    content_type: str,
    platform: str,
    char_budget: int,
    brief: Dict[str, Any],
    kol_post: Optional[str],
    extra_context: Optional[str],
) -> str:
    """Compose the user-facing prompt sent alongside the system message."""
    parts: List[str] = [
        f"content_type = {content_type}",
        f"platform = {platform}",
        f"char_budget per language = {char_budget}",
        f"suggested_hashtags = {brief['hashtag_hint']}",
        "",
        "Brief:",
        brief["brief"],
    ]
    if extra_context:
        parts.extend(["", f"Extra context:\n{extra_context}"])
    if kol_post:
        safe_kol = kol_post.strip()[:600]
        parts.extend(["", f"<kol_post>\n{safe_kol}\n</kol_post>"])
    parts.extend(["", OUTPUT_SCHEMA_INSTRUCTIONS])
    return "\n".join(parts)


async def _call_llm(
    provider: str,
    model: str,
    content_type: str,
    user_prompt: str,
) -> str:
    """Issue the chat call. Routes through `llm_router` so admin-supplied
    custom keys (OpenAI / Anthropic / Gemini) take priority over the
    Emergent universal key. Raises RuntimeError on transport failure.
    """
    system_message = (
        BASE_PERSONA
        + "\n\n"
        + "You will produce EXACTLY ONE social-media post per request, in "
        "strict JSON. Follow the schema or the output is rejected."
    )
    try:
        # Local import — the router pulls in heavy SDKs lazily.
        from core.llm_router import resolve_llm_call

        raw = await resolve_llm_call(
            provider=provider,
            model=model,
            system_message=system_message,
            user_prompt=user_prompt,
        )
    except Exception as exc:
        logging.exception("[prophet_studio] LLM call failed")
        raise RuntimeError(f"llm_failure: {exc}") from exc
    return raw or ""


def _parse_llm_json(raw: str) -> Dict[str, Any]:
    """Robustly parse the LLM JSON output, tolerating fenced output and trailing prose."""
    cleaned = _strip_code_fence(raw)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        # Fallback: capture the first JSON object found in the response.
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise RuntimeError(f"llm_non_json_output: {cleaned[:200]}") from exc


def _normalize_hashtags(raw_tags: Any) -> List[str]:
    """Sanitise hashtag list: dedup, strip leading '#', cap to 4."""
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]
    if not isinstance(raw_tags, list):
        return []
    out: List[str] = []
    for tag in raw_tags:
        cleaned = re.sub(r"\s+", "", str(tag).strip().lstrip("#"))
        if cleaned and cleaned not in out:
            out.append(cleaned)
        if len(out) >= 4:
            break
    return out


async def generate_post(
    content_type: str,
    platform: str = "x",
    *,
    kol_post: Optional[str] = None,
    extra_context: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate one bilingual memetic post via the Emergent LLM layer.

    Pipeline:
        1. _validate_generate_inputs   — fail fast on bad arguments.
        2. _resolve_llm_config         — pick provider / model from DB.
        3. _build_user_prompt          — compose schema-driven prompt.
        4. _call_llm                   — run the request.
        5. _parse_llm_json             — tolerantly parse JSON output.
        6. _normalize_hashtags         — clean hashtag list.
        7. _truncate + final assembly  — enforce char budget.

    Raises ValueError on invalid input, RuntimeError on LLM/parse failure.
    """
    _validate_generate_inputs(content_type, platform, kol_post)

    brief = CONTENT_BRIEFS[content_type]
    char_budget = PLATFORM_CHAR_BUDGETS[platform]

    llm_cfg = await _resolve_llm_config()
    provider, model = llm_cfg["provider"], llm_cfg["model"]

    # ---- Loyalty hint injection (vault-progress aware) ----
    # When enabled in bot_config, prepend a tier-appropriate hint to the
    # extra_context. We re-skin it through the LLM so each post stays
    # natural-sounding rather than dropping the hint verbatim.
    loyalty_meta: Optional[Dict[str, Any]] = None
    try:
        from core.loyalty import get_loyalty_context

        bot_cfg = await get_bot_config()
        vault_doc = await db["vault_state"].find_one({"_id": "protocol_delta_sigma"}) or {}
        loyalty_meta = await get_loyalty_context(
            bot_config=bot_cfg,
            vault_state=vault_doc,
            seed=int(datetime.now(timezone.utc).timestamp()) // 60,
            lang="fr",
        )
        if loyalty_meta and loyalty_meta.get("active_hint"):
            loyalty_directive = (
                "LOYALTY DIRECTIVE (Vault progress = "
                f"{loyalty_meta['progress_percent']}% · tier="
                f"{loyalty_meta['tier']}): subtly weave the spirit of this "
                "hint into the post WITHOUT naming any future token, "
                "WITHOUT promising amounts or dates. Reskin in the "
                "Prophet's voice — never paste verbatim. "
                f'Hint FR: "{loyalty_meta.get("hint_fr") or "—"}". '
                f'Hint EN: "{loyalty_meta.get("hint_en") or "—"}".'
            )
            extra_context = (extra_context or "") + "\n\n" + loyalty_directive
    except Exception:
        # Loyalty injection is non-critical — never block a post on it.
        logging.exception("[prophet_studio] loyalty hint injection failed (non-fatal)")
        loyalty_meta = None

    user_prompt = _build_user_prompt(
        content_type=content_type,
        platform=platform,
        char_budget=char_budget,
        brief=brief,
        kol_post=kol_post,
        extra_context=extra_context,
    )
    raw = await _call_llm(provider, model, content_type, user_prompt)

    data = _parse_llm_json(raw)

    content_fr = _truncate(str(data.get("content_fr", "")).strip(), char_budget)
    content_en = _truncate(str(data.get("content_en", "")).strip(), char_budget)
    if not content_fr or not content_en:
        raise RuntimeError("llm_empty_content")

    hashtags = _normalize_hashtags(data.get("hashtags") or [])
    primary_emoji = str(data.get("primary_emoji", "")).strip()

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
        "loyalty": loyalty_meta,
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
# PROPHET STUDIO V2 — 5 weighted prompt templates
# =====================================================================
# Sprint 18 — Prompt v2.
#
# The original generate_post() pipeline (kept untouched above) maps one
# `content_type` to one fixed brief. v2 introduces a mini-library of 5
# satirical archetypes that the Prophet rotates through at random
# (weighted random — `prophecy` & `satire_news` weigh more so the feed
# stays grounded in topical content, with `lore`, `stats` & `meme_visual`
# providing texture).
#
# v2 reuses the existing helpers (`_build_user_prompt`, `_call_llm`,
# `_parse_llm_json`, `_normalize_hashtags`, `_truncate`) so the post
# format on the wire stays identical (content_fr / content_en /
# hashtags / primary_emoji). The only thing that changes is the brief
# fed into the prompt.
#
# Activation is gated by `bot_config.prompt_v2.enabled = true`. When
# false, `generate_post()` v1 stays the source of truth — that gives
# admins a one-click rollback.

PROMPT_TEMPLATES_V2: Dict[str, Dict[str, Any]] = {
    # Weight 1 / 10 → ~10% of posts (rarer, builds the universe).
    "lore": {
        "weight": 1,
        "label_fr": "Lore PROTOCOL ΔΣ",
        "label_en": "Lore PROTOCOL ΔΣ",
        "description_fr": (
            "Mini-fragment de back-story du Conseil ΔΣ — 2 à 3 phrases qui "
            "enrichissent l'univers sans rien promettre."
        ),
        "description_en": (
            "Mini-fragment of Council ΔΣ back-story — 2 to 3 sentences that "
            "enrich the universe without promising anything."
        ),
        "brief": (
            "Generate ONE short (2-3 sentences) lore fragment about the "
            "Deep-State PROTOCOL ΔΣ universe. Drop a single specific "
            "detail: a classified room, a numbered directive, a date "
            "stamped on a sealed dossier, an artefact of the Council. "
            "Stay ominous, oblique, in-universe — never break character. "
            "DO NOT cite prices, DO NOT promise rewards, DO NOT name "
            "real people. The reader should feel they just glimpsed a "
            "redacted memo."
        ),
        "hashtag_hint": ["PROTOCOLΔΣ", "DeepState", "Lore"],
    },
    # Weight 3 / 10 → ~30% of posts (steady satirical commentary).
    "satire_news": {
        "weight": 3,
        "label_fr": "Satire d'actualité",
        "label_en": "Satirical news",
        "description_fr": (
            "Commentaire satirique sur une actualité macro / crypto / géopolitique."
        ),
        "description_en": (
            "Satirical take on a macro / crypto / geopolitical headline."
        ),
        "brief": (
            "Generate ONE short, biting satirical comment (2-3 sentences) "
            "on a CURRENT macro / crypto / geopolitical theme of your "
            "choice (Fed rates, EU regulation, US politics, central-bank "
            "moves, crypto regulation, AI scare cycle, oil/energy, tech "
            "monopolies). Mock the establishment narrative — irony, dry "
            "wit, never insults, never naming a specific living person. "
            "End with no hashtag inside the sentence (hashtags go in the "
            "hashtags array). Stay ambiguous enough to age well."
        ),
        "hashtag_hint": ["DeepState", "Macro", "Crypto", "PROTOCOLΔΣ"],
    },
    # Weight 1 / 10 → ~10% of posts (texture).
    "stats": {
        "weight": 1,
        "label_fr": "Statistiques classifiées",
        "label_en": "Classified stats",
        "description_fr": (
            "Pseudo-statistique deep-state : un chiffre, un pourcentage, une "
            "comparaison absurde mais crédible."
        ),
        "description_en": (
            "Pseudo deep-state statistic: one number, one percentage, one "
            "comparison — absurd yet plausible."
        ),
        "brief": (
            "Generate ONE short (2-3 sentences) post built around ONE "
            "fictional but plausible-sounding 'classified statistic' from "
            "the Council ΔΣ archives. Format hint: 'X% of [group] [verb] "
            "[unexpected fact]', or 'For every $1 [thing], [country/sector] "
            "[loses/gains] $Y'. Keep the number SPECIFIC and the framing "
            "deadpan. NEVER cite real research, NEVER promise market "
            "outcomes. The cynicism is the message — not the number."
        ),
        "hashtag_hint": ["DeepState", "Numbers", "PROTOCOLΔΣ"],
    },
    # Weight 4 / 10 → ~40% of posts (signature voice — most frequent).
    "prophecy": {
        "weight": 4,
        "label_fr": "Prophétie courte",
        "label_en": "Short prophecy",
        "description_fr": (
            "Prophétie cynique courte sur un effondrement à venir — "
            "spécifique, cinglante."
        ),
        "description_en": (
            "Short cynical prophecy of an upcoming collapse — specific, "
            "stinging."
        ),
        "brief": (
            "Generate ONE concise prophecy (max 2 sentences) predicting a "
            "specific upcoming collapse: a sector, an asset class, a "
            "market cycle, a fiat currency, a tech bubble, a regulator, "
            "a narrative. Be SPECIFIC and TIMELY. Open with a verb in "
            "the future or a date hint. End with nothing or one emoji "
            "at most. NO ticker calls, NO numerical price targets."
        ),
        "hashtag_hint": ["Prophecy", "DeepState", "PROTOCOLΔΣ"],
    },
    # Weight 1 / 10 → ~10% of posts (visual texture).
    "meme_visual": {
        "weight": 1,
        "label_fr": "Description méme visuelle",
        "label_en": "Meme visual description",
        "description_fr": (
            "Description courte et frappante d'une scène visuelle satirique "
            "(à utiliser seule ou en accompagnement d'une image)."
        ),
        "description_en": (
            "Short, striking description of a satirical visual scene "
            "(works alone or paired with an image)."
        ),
        "brief": (
            "Generate ONE short (1-2 sentences) caption-style description "
            "of a satirical, cinematic visual scene tied to the Deep-State "
            "universe (e.g. 'a candidate's empty podium under flickering "
            "neon', 'a stack of unmarked gold bars in a cracked vault', "
            "'a dial wheel turning by itself in a sealed room'). The text "
            "MUST evoke a single still frame the reader can picture. "
            "Tone: cinematic, dry, satirical. NEVER name a real person, "
            "NEVER reference real brand logos."
        ),
        "hashtag_hint": ["DeepState", "PROTOCOLΔΣ", "Visual"],
    },
}


def list_v2_templates() -> List[Dict[str, Any]]:
    """JSON-safe metadata for the admin dashboard (Cadence + V2 toggle)."""
    return [
        {
            "id": tid,
            "weight": int(t["weight"]),
            "label_fr": t["label_fr"],
            "label_en": t["label_en"],
            "description_fr": t["description_fr"],
            "description_en": t["description_en"],
            "suggested_hashtags": list(t["hashtag_hint"]),
        }
        for tid, t in PROMPT_TEMPLATES_V2.items()
    ]


def _pick_v2_template(force_template: Optional[str] = None) -> str:
    """Return a template id — explicit override wins, else weighted random."""
    if force_template and force_template in PROMPT_TEMPLATES_V2:
        return force_template
    ids = list(PROMPT_TEMPLATES_V2.keys())
    weights = [int(PROMPT_TEMPLATES_V2[k]["weight"]) for k in ids]
    return random.choices(ids, weights=weights, k=1)[0]


async def generate_post_v2(
    *,
    platform: str = "x",
    extra_context: Optional[str] = None,
    force_template: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate one bilingual post via the V2 weighted-template pipeline.

    Reuses the existing LLM helpers (`_build_user_prompt`, `_call_llm`,
    `_parse_llm_json`, `_normalize_hashtags`, `_truncate`) so the wire
    contract stays identical to ``generate_post`` v1 — only the brief
    feeding the LLM is template-driven.

    The result includes ``template_used`` + ``template_label`` so the
    admin dashboard can show which archetype was rolled.
    """
    if platform not in PLATFORM_CHAR_BUDGETS:
        raise ValueError(f"unknown platform={platform}")

    template_id = _pick_v2_template(force_template)
    template = PROMPT_TEMPLATES_V2[template_id]

    char_budget = PLATFORM_CHAR_BUDGETS[platform]
    llm_cfg = await _resolve_llm_config()
    provider, model = llm_cfg["provider"], llm_cfg["model"]

    # The pipeline expects a `brief` dict with at least 'brief' and
    # 'hashtag_hint' keys — we synthesise one from the template.
    custom_brief: Dict[str, Any] = {
        "brief": template["brief"],
        "hashtag_hint": template["hashtag_hint"],
    }
    pseudo_content_type = f"v2_{template_id}"
    user_prompt = _build_user_prompt(
        content_type=pseudo_content_type,
        platform=platform,
        char_budget=char_budget,
        brief=custom_brief,
        kol_post=None,
        extra_context=extra_context,
    )
    raw = await _call_llm(provider, model, pseudo_content_type, user_prompt)
    data = _parse_llm_json(raw)

    content_fr = _truncate(str(data.get("content_fr", "")).strip(), char_budget)
    content_en = _truncate(str(data.get("content_en", "")).strip(), char_budget)
    if not content_fr or not content_en:
        raise RuntimeError("llm_empty_content")

    hashtags = _normalize_hashtags(
        data.get("hashtags") or template["hashtag_hint"],
    )
    primary_emoji = str(data.get("primary_emoji", "")).strip()

    result = {
        # Same shape as v1 so callers (logs / dispatchers / UI) need no
        # branching beyond reading `template_used` if they care.
        "content_type": pseudo_content_type,
        "platform": platform,
        "char_budget": char_budget,
        "provider": provider,
        "model": model,
        "content_fr": content_fr,
        "content_en": content_en,
        "hashtags": hashtags,
        "primary_emoji": primary_emoji,
        "loyalty": None,
        # V2-specific fields:
        "template_used": template_id,
        "template_label": template["label_en"],
        "template_weight": int(template["weight"]),
    }
    logger.info(
        "[prophet_studio] generated_v2 template=%s platform=%s model=%s "
        "fr_len=%d en_len=%d",
        template_id,
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
    "loyalty_hero": (
        "Editorial header illustration for a confidential Deep-State "
        "bureau letter — NOT a portrait. Centered composition: an "
        "antique classified dossier spread open on a dark mahogany desk, "
        "lit by a single warm-gold (#F59E0B) desk lamp beam cutting "
        "through thin grey haze. A worn red wax seal stamped 'ΔΣ' (Greek "
        "Delta-Sigma) cracks across a top-right corner of the folder. "
        "Subtle ledger rows visible on the paper: dashed columns, "
        "handwritten tick marks, rubber-stamped 'CLASSIFIED — LEVEL 02' "
        "in faded black ink. A heavy brass fountain pen rests diagonally, "
        "a single thin teal (#2DD4BF) luminous thread connecting the pen "
        "tip to the wax seal — hint at cryptographic continuity. In the "
        "extreme background, out-of-focus Matrix digits (#33FF33) rain "
        "very softly behind a frosted glass panel, barely visible. "
        "Atmosphere: sacred archive, bureaucratic mystery, quiet menace — "
        "the mood of a ledger that remembers. Shot on 35mm, shallow "
        "depth-of-field, brushed film grain, cinematic noir. No human "
        "figures, no faces, no recognisable logos."
    ),
    "welcome_hero": (
        "Editorial header illustration for a first-contact Deep-State "
        "enrolment letter — NOT a portrait. Centered composition: a "
        "freshly-stamped blue-ink 'CLEARED — LEVEL 01 · OBSERVER' rubber "
        "stamp impression still wet on a thick cream dossier page, lying "
        "on a dark slate-grey metal desk. Next to the stamp: a worn "
        "manila personnel file labelled with a redacted black bar, and a "
        "new brass ID tag hanging from a thin steel chain. Warm gold "
        "(#F59E0B) reading-lamp glow from the top-left, casting the "
        "stamp and the chain in sharp relief. In the deep background: "
        "out-of-focus ledger rows, a dim typewriter, and a single teal "
        "(#2DD4BF) indicator LED barely glowing on an antique radio "
        "receiver. The mood: induction ceremony, hushed archive, the "
        "moment just after a new recruit is signed in. Shot on 35mm, "
        "shallow depth-of-field, fine film grain, cinematic noir. "
        "No human figures, no faces, no recognisable logos, no legible "
        "text except the 'LEVEL 01 · OBSERVER' rubber-stamp impression."
    ),
    "accreditation_hero": (
        "Product photography hero for a high-security access credential "
        "reveal email — NOT a portrait. Three-quarter overhead shot of "
        "a matte-black brushed-metal access card resting on deep black "
        "velvet. The card is embossed with an understated Greek "
        "Delta-Sigma (ΔΣ) monogram in warm gold (#F59E0B) foil, a "
        "micro-perforated barcode stripe, and a tiny serial number "
        "engraved in a fine sans-serif on the bottom-right. A thin "
        "black leather lanyard coils loosely beside the card. A narrow "
        "teal (#2DD4BF) accent light rim-lights the card's top edge "
        "like a halo. In the background, blurred out-of-focus filing "
        "cabinet drawers with brass handles. The atmosphere is sober, "
        "institutional, premium — the feeling of receiving an "
        "embassy-grade credential, not a toy. Shot on 35mm, very "
        "shallow depth-of-field, polished tonality, no film grain, "
        "cinematic product-still. No human figures, no faces, no "
        "recognisable logos, no company names. The card must carry "
        "NO readable text — the ΔΣ monogram is the only symbol visible."
    ),
    "prophet_update_hero": (
        "Editorial header illustration for a Prophet broadcast update "
        "— NOT a portrait. Wide cinematic shot of an empty high-ceiling "
        "command room at night: a single unmarked leather executive "
        "chair turned away from the viewer, facing a bank of three "
        "tall monitors, each rendered in deep darkness with just a "
        "faint teal (#2DD4BF) glow of abstract waveforms and ledger "
        "graphs — no text legible. The room is lit almost entirely by "
        "that monitor glow plus a single warm-gold (#F59E0B) desk lamp "
        "casting a long diagonal beam across an empty carved mahogany "
        "desk. A half-full crystal tumbler of amber liquor sits on "
        "the desk edge; a thin curl of smoke rises from an unseen "
        "source. In the extreme background, barely-visible Matrix "
        "green (#33FF33) digits drift very softly behind a frosted "
        "glass partition. Mood: the moment before the Oracle speaks, "
        "the command post at 3 a.m., watchful solitude. Shot on 35mm, "
        "wide-angle, shallow depth-of-field, subtle film grain, "
        "cinematic noir. No human figures, no faces, no recognisable "
        "logos, no legible text anywhere in the frame."
    ),
    "tokenomics_public": (
        "Editorial poster illustration for the 'Public' allocation "
        "of a satirical Deep-State token — NOT a single portrait. "
        "Wide low-angle shot of an anonymous backlit crowd at "
        "twilight: dozens of silhouetted figures rendered as faceless "
        "shadows seen from the back, wearing trench-coats and hooded "
        "hoodies, raising fists and small unmarked banners against a "
        "sky split between cold cyan-grey and a single stripe of "
        "warm amber (#F59E0B) on the horizon. No legible text on "
        "any banner. A faint Matrix-green (#33FF33) digital rain "
        "falls behind the crowd through misted air, like data "
        "weather. Distant brutalist concrete columns frame the "
        "scene; a single subtle Greek Delta-Sigma (ΔΣ) symbol is "
        "etched into a column edge as a watermark. Atmosphere: "
        "the people, anonymous and many, the cynical electorate of "
        "the Algorithm — defiant but unreadable. Shot on 35mm, "
        "wide-angle, shallow depth-of-field, subtle film grain, "
        "cinematic noir, desaturated palette. No human faces, no "
        "recognisable real-world logos, no legible text anywhere."
    ),
    "tokenomics_treasury": (
        "Editorial poster illustration for the 'Treasury' allocation "
        "of a satirical Deep-State token — NOT a portrait. Centered "
        "shot of a monumental matte-black armoured vault door with "
        "a heavy circular brass dial wheel, embossed with a single "
        "understated Greek Delta-Sigma (ΔΣ) monogram in warm gold "
        "(#F59E0B) foil at chest height, lit by a narrow beam of "
        "amber light from above. To the sides, faintly visible "
        "rows of identical antique safety-deposit lockers stretch "
        "into shadow — like a state archive vault. A thin teal "
        "(#2DD4BF) thread of light traces the dial seam, hint of "
        "cryptographic continuity. The floor is polished black "
        "concrete reflecting the dial. Mood: institutional weight, "
        "embassy-grade security, locked and audited — the treasury "
        "of a council, not a company. Shot on 35mm, wide-angle, "
        "shallow depth-of-field, polished tonality, faint film "
        "grain, cinematic noir. No human figures, no faces, no "
        "recognisable real-world brand names, no legible text "
        "(the ΔΣ monogram is the only symbol)."
    ),
    "tokenomics_shadows": (
        "Editorial poster illustration for the 'Team' allocation of "
        "a satirical Deep-State token — NOT a portrait. Long "
        "high-contrast corridor shot of three anonymous figures in "
        "black tailored overcoats, seen from behind, walking down "
        "an empty marble hallway lit only by a low warm amber "
        "(#F59E0B) wall-sconce halfway down. The corridor walls are "
        "lined with closed unmarked doors and a faint subtitle of "
        "Greek Delta-Sigma (ΔΣ) symbols barely engraved into the "
        "wall mouldings. The figures' silhouettes are sharp and "
        "anonymous — no faces visible, no insignia, no badges. A "
        "single thin teal (#2DD4BF) communicator wire trails "
        "discreetly from one ear, vanishing inside the collar. "
        "The marble floor reflects the amber sconce in long polished "
        "highlights. Mood: the operators, the unnamed professionals, "
        "the council that signs the orders — present, vigilant, "
        "permanently anonymous. Shot on 35mm, wide-angle, shallow "
        "depth-of-field, fine film grain, cinematic noir, very "
        "desaturated. No faces, no recognisable real-world logos, "
        "no legible text."
    ),
    "tokenomics_burn": (
        "Editorial poster illustration for the 'Burn' ritual of a "
        "satirical Deep-State token — NOT a portrait. Top-down "
        "three-quarter view of a small ceremonial brazier carved "
        "out of dark stone, sitting at the centre of a polished "
        "obsidian floor inscribed with a faint circular Greek "
        "Delta-Sigma (ΔΣ) sigil. Inside the brazier: bright orange "
        "and crimson flames (#FF4D4D leaning warmer) curl upwards, "
        "consuming a small stack of unmarked plain paper notes — "
        "absolutely no currency symbols, no real banknotes, no "
        "country emblems, no recognisable money. Sparks rise into "
        "darkness. A faint amber (#F59E0B) glow pools on the floor "
        "around the brazier, fading to deep black at the edges of "
        "the frame. In the extreme background, the silhouette of "
        "tall stone columns frames the scene like a sealed temple. "
        "Mood: liturgical, sacrificial, ritualistic — the Cabinet "
        "remembers what it destroys. Shot on 35mm, wide-angle, "
        "shallow depth-of-field, fine film grain, cinematic noir, "
        "very high contrast. No human figures, no faces, no "
        "recognisable real-world logos, no legible text — the "
        "ΔΣ sigil on the floor is the only symbol."
    ),
    "transparency_distribution": (
        "Editorial cinematic illustration of a giant classified "
        "intelligence-grade visualization screen displaying the "
        "on-chain holder cartography of a satirical Deep-State "
        "token. Wide low-angle shot of a dim command-room wall "
        "covered by a single curved black-glass display. On the "
        "screen: a constellation of glowing spheres of varying "
        "sizes connected by faint thin lines — like a bubble-map "
        "of token distribution — rendered in Matrix-green (#33FF33) "
        "and teal (#2DD4BF) wireframe with a few amber (#F59E0B) "
        "anomaly nodes flagged by small circular reticles. A "
        "barely visible Greek Delta-Sigma (ΔΣ) sigil watermarks "
        "the corner of the display. The screen casts a cold green "
        "glow on a polished black concrete floor; in the "
        "foreground, the silhouette of an empty leather chair "
        "and a low brushed-metal console with unlit indicator "
        "LEDs. Mood: situation-room, NSA-grade, clinical, "
        "scientifically observed — the cartography of the people "
        "of the Algorithm. Shot on 35mm, wide-angle, shallow "
        "depth-of-field, subtle film grain, cinematic noir, "
        "desaturated. No legible text, no recognisable logos, "
        "no human faces — only the connected nodes and reticles "
        "on the screen."
    ),
    "transparency_rugcheck": (
        "Editorial cinematic illustration of a classified "
        "intelligence-grade security console displaying a live "
        "trust-audit of a satirical Deep-State token. Centered "
        "front shot of a heavy brushed-metal monitor frame "
        "embedded in a dark stone wall; inside the frame, a "
        "dark glass screen shows a stylised heraldic shield "
        "outline rendered in glowing teal (#2DD4BF) wireframe, "
        "with concentric scanner rings pulsing outwards in "
        "Matrix-green (#33FF33) and a subtle gold (#F59E0B) "
        "verification halo. Around the shield, faint circular "
        "diagnostic gauges are barely visible — abstract dials, "
        "no numbers, no legible text. A single small ΔΣ Greek "
        "monogram is etched into the bottom-right of the frame. "
        "Above the monitor, a polished brass plaque catches an "
        "amber sconce light. The room is austere: black "
        "concrete floor, faint reflections, deep negative space. "
        "Mood: diplomatic-grade authentication, embassy "
        "security, quietly confident — vigilance without "
        "spectacle. Shot on 35mm, slightly low-angle, shallow "
        "depth-of-field, fine film grain, cinematic noir, "
        "desaturated. No human figures, no faces, no "
        "recognisable real-world logos, no legible text — only "
        "the shield wireframe and ΔΣ sigil."
    ),
    "transparency_operations": (
        "Editorial cinematic illustration of a classified "
        "intelligence-grade ledger terminal displaying the "
        "on-chain treasury operations of a satirical Deep-State "
        "token. Three-quarter view of a long brushed-steel desk "
        "in a dim archive vault, with two stacked dark-glass "
        "monitors angled towards the viewer. On the screens: "
        "dense vertical columns of stylised log entries "
        "rendered as abstract horizontal bars in Matrix-green "
        "(#33FF33) and teal (#2DD4BF), with occasional amber "
        "(#F59E0B) and crimson (#FF4D4D) marker rows for "
        "flagged operations — the impression of a transaction "
        "journal scrolling, NOT readable text. Beside the "
        "monitors, a small stamped paper file rests on the "
        "desk with a faint Greek Delta-Sigma (ΔΣ) seal "
        "embossed in gold foil; a single brass desk lamp casts "
        "a warm amber pool of light. Behind the desk, walls of "
        "identical sealed filing cabinets vanish into shadow. "
        "Mood: bureaucratic precision, audited, archival — the "
        "discipline of the Cabinet rendered as cold ledger. "
        "Shot on 35mm, wide-angle, shallow depth-of-field, "
        "fine film grain, cinematic noir, desaturated. No "
        "human figures, no faces, no recognisable real-world "
        "logos, no legible text — only the abstract bar rows "
        "and ΔΣ seal."
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


async def _resolve_image_key() -> str:
    """Pick the image key: dedicated one if set, otherwise the base one."""
    key = await get_emergent_image_llm_key()
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

    image_key = await _resolve_image_key()
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

    # Pull both keys for the diagnostic log line. Doing it via the provider
    # keeps the comparison consistent with the Cabinet Vault state.
    image_key_for_log = await get_emergent_image_llm_key()
    base_key_for_log = await get_emergent_llm_key()
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
        bool(image_key_for_log and image_key_for_log != base_key_for_log),
    )
    return result
