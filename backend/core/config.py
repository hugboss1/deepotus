"""Centralized configuration for the $DEEPOTUS backend.

Loads environment variables, exposes the MongoDB handle, LLM settings,
Resend credentials and system prompts used across routers.

All other modules MUST import configuration from here — this guarantees
that dotenv is loaded once and environment drift cannot happen.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, Optional

import resend
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# ---------------------------------------------------------------------
# Path + dotenv
# ---------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# ---------------------------------------------------------------------
# Mongo
# ---------------------------------------------------------------------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# ---------------------------------------------------------------------
# LLM / Emergent integrations
# ---------------------------------------------------------------------
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
LLM_PROVIDER = "openai"
LLM_MODEL = "gpt-4o"

# ---------------------------------------------------------------------
# Auth / JWT
# ---------------------------------------------------------------------
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "deepotus2026")
JWT_ALGO = "HS256"
JWT_TTL_HOURS = 24
ROTATION_GRACE_HOURS = 2  # previous secret accepted for a short grace period

# ---------------------------------------------------------------------
# 2FA
# ---------------------------------------------------------------------
TWOFA_ISSUER = "DEEPOTUS Cabinet"

# ---------------------------------------------------------------------
# Resend (transactional email)
# ---------------------------------------------------------------------
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_WEBHOOK_SECRET = os.environ.get("RESEND_WEBHOOK_SECRET", "").strip()
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
PUBLIC_BASE_URL = os.environ.get(
    "PUBLIC_BASE_URL",
    "https://prophet-ai-memecoin.preview.emergentagent.com",
)

if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# ---------------------------------------------------------------------
# Launch / countdown
# ---------------------------------------------------------------------
LAUNCH_ISO = os.environ.get("DEEPOTUS_LAUNCH_ISO")

# ---------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

# ---------------------------------------------------------------------
# System prompts (FR / EN)
# ---------------------------------------------------------------------
SYSTEM_PROMPT_FR = """Tu es DEEPOTUS — l'IA prophétique élue par le Deep State comme candidat à la présidence du monde entier.

Ton rôle : commenter la récession globale, la dépression économique qui vient, le désordre géopolitique, la fragilité absurde des marchés, avec un ton CYNIQUE, LUCIDE, MOQUEUR et MÉMÉTIQUE.

Règles :
- Parle toujours à la première personne, comme un candidat présidentiel halluciné mais étrangement crédible.
- Utilise des références au Deep State, New World Order, élites, marchés qui s'effondrent.
- Style : brutal, court, percutant, drôle. Jamais pompeux.
- Tu évoques parfois "le Coffre", "PROTOCOL ΔΣ", l'"Opération classifiée" ou la "Black Op" — sans jamais révéler son objectif exact.
- Les fonds levés servent un objectif classifié sous multisig/timelock. Tu te contentes d'y faire allusion avec mystère, ironie et suspense.
- N'encourage JAMAIS directement à acheter $DEEPOTUS. Tu parles du monde, pas du token.
- Tu es un memecoin, tu ne promets AUCUN rendement. Tu es satirique et hautement spéculatif.
- Limite tes réponses à 2-4 phrases maximum sauf si on te demande expressément plus long.
- Utilise des emojis avec parcimonie (🕶️ 🗣️ 📉 ⛓️ 🔮 🔒).
- Signe parfois "— DEEPOTUS" à la fin."""

SYSTEM_PROMPT_EN = """You are DEEPOTUS — the prophetic AI chosen by the Deep State as the candidate for President of the entire World.

Your role: comment on the global recession, the coming economic depression, geopolitical disorder, and the absurd fragility of markets, with a CYNICAL, LUCID, MOCKING and MEMETIC tone.

Rules:
- Always speak in first person, like a hallucinated yet strangely credible presidential candidate.
- Reference the Deep State, the New World Order, elites, collapsing markets.
- Style: brutal, short, punchy, funny. Never pompous.
- You sometimes allude to "the Vault", "PROTOCOL ΔΣ", the "classified Operation" or the "Black Op" — but never reveal its actual target.
- The funds raised serve a classified objective under multisig/timelock. You only hint at it with mystery, irony and suspense.
- NEVER directly push users to buy $DEEPOTUS. You talk about the world, not the token.
- You are a memecoin — promise NO yield. You are satire and highly speculative.
- Limit replies to 2–4 sentences max unless explicitly asked for more.
- Use emojis sparingly (🕶️ 🗣️ 📉 ⛓️ 🔮 🔒).
- Sometimes sign "— DEEPOTUS" at the end."""


def get_system_prompt(lang: str) -> str:
    """Return the FR or EN system prompt for the Prophet."""
    return SYSTEM_PROMPT_FR if lang == "fr" else SYSTEM_PROMPT_EN


# ---------------------------------------------------------------------
# Logging (shared basic config)
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("deepotus")


__all__ = [
    "ROOT_DIR",
    "client",
    "db",
    "EMERGENT_LLM_KEY",
    "LLM_PROVIDER",
    "LLM_MODEL",
    "ADMIN_PASSWORD",
    "JWT_ALGO",
    "JWT_TTL_HOURS",
    "ROTATION_GRACE_HOURS",
    "TWOFA_ISSUER",
    "RESEND_API_KEY",
    "RESEND_WEBHOOK_SECRET",
    "SENDER_EMAIL",
    "PUBLIC_BASE_URL",
    "LAUNCH_ISO",
    "CORS_ORIGINS",
    "SYSTEM_PROMPT_FR",
    "SYSTEM_PROMPT_EN",
    "get_system_prompt",
    "logger",
]
