"""Secure secret storage helpers (Fernet AES-128-CBC + HMAC-SHA256).

Used by the bot admin to store user-supplied LLM API keys (OpenAI,
Anthropic, Google Gemini) so they never live in plaintext anywhere
except in transient memory during a single LLM call.

Threat model — what this module defends against:
    1. Mongo dump / read-only DB access
       → ciphertext is useless without the KEK; KEK lives in env only.
    2. Server logs / stack traces
       → encrypt() / decrypt() never log the plaintext.
    3. Admin GET endpoints
       → only `mask_for_display()` output is ever serialised.

What this module does NOT defend against:
    - Root access to the running process (memory inspection, env vars).
      Mitigation = Render / hosting platform isolation + small attack
      surface (we never echo the KEK over any HTTP route).

Public API:
    encrypt(plaintext: str) -> str            # base64 ciphertext
    decrypt(ciphertext_b64: str) -> str
    mask_for_display(plaintext: str) -> str   # "sk-...A1B2"
    fingerprint(plaintext: str) -> str        # short, stable, non-secret
    detect_provider(plaintext: str) -> str
    is_kek_configured() -> bool
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import secrets
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("deepotus.secrets_vault")

# ---------------------------------------------------------------------
# KEK (Key Encryption Key) bootstrap
# ---------------------------------------------------------------------
KEK_ENV_VAR = "SECRETS_KEK_KEY"


def _load_or_generate_kek() -> bytes:
    """Return a 32-byte URL-safe Fernet key.

    Resolution order:
        1. `SECRETS_KEK_KEY` env var (production / persistent)
        2. ephemeral generated key on first import (dev only)

    In ephemeral mode we log a LOUD warning so it's obvious the key
    won't survive a container restart — encrypted secrets stored under
    that ephemeral KEK become unreadable after a redeploy.
    """
    env_val = (os.environ.get(KEK_ENV_VAR) or "").strip()
    if env_val:
        try:
            # Validate by attempting to instantiate Fernet — raises if bad.
            Fernet(env_val.encode("utf-8"))
            return env_val.encode("utf-8")
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "[secrets_vault] %s is set but invalid (%s) — falling back to "
                "ephemeral key. PLEASE FIX YOUR ENV before storing real keys.",
                KEK_ENV_VAR,
                exc,
            )

    # Dev-only fallback. Stable across this process lifetime, lost on restart.
    ephemeral = Fernet.generate_key()
    logger.warning(
        "[secrets_vault] %s is not configured. Generated EPHEMERAL key "
        "(stored in process memory only). DO NOT store real LLM keys yet — "
        "any restart will corrupt them. Set %s in your env to enable "
        "persistent encrypted storage.",
        KEK_ENV_VAR,
        KEK_ENV_VAR,
    )
    return ephemeral


_KEK: bytes = _load_or_generate_kek()
_FERNET = Fernet(_KEK)

# Track whether we're running in the dangerous ephemeral mode so the
# admin endpoints can refuse to write real secrets in that case.
_KEK_IS_EPHEMERAL: bool = not bool(os.environ.get(KEK_ENV_VAR, "").strip())


# ---------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------
def is_kek_configured() -> bool:
    """True iff a persistent SECRETS_KEK_KEY env var is set."""
    return not _KEK_IS_EPHEMERAL


def encrypt(plaintext: str) -> str:
    """Return a URL-safe base64 ciphertext.

    Raises ValueError if the input is empty (protects against accidental
    storage of empty strings as "successfully encrypted").
    """
    if not plaintext:
        raise ValueError("Refusing to encrypt empty plaintext")
    token = _FERNET.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")  # base64-urlsafe ASCII


def decrypt(ciphertext_b64: str) -> str:
    """Reverse `encrypt`. Raises InvalidToken on tamper / wrong KEK."""
    if not ciphertext_b64:
        raise ValueError("Refusing to decrypt empty ciphertext")
    try:
        out = _FERNET.decrypt(ciphertext_b64.encode("utf-8"))
    except InvalidToken as exc:
        raise InvalidToken(
            "Stored secret cannot be decrypted with the current KEK. "
            "Either the KEK was rotated, the ciphertext was tampered, or "
            "the secret was written in ephemeral mode and the process has "
            "since restarted."
        ) from exc
    return out.decode("utf-8")


def mask_for_display(plaintext: str) -> str:
    """Build a UI-safe label (first 3 + last 4 chars) — NEVER logs full key.

    Examples:
        "sk-abc1234567890XYZ"  -> "sk-...0XYZ"
        "AIzaSyA1B2C3..."      -> "AIz...A1B2"
        "short"                -> "***"
    """
    if not plaintext:
        return "—"
    cleaned = plaintext.strip()
    if len(cleaned) < 8:
        return "***"  # too short to safely mask
    return f"{cleaned[:3]}...{cleaned[-4:]}"


def fingerprint(plaintext: str) -> str:
    """Stable SHA-256 short fingerprint for *equality checking*, never displayed.

    Useful for the UI to detect "you're trying to set the same key again"
    without ever roundtripping the plaintext.
    """
    if not plaintext:
        return ""
    h = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
    return h[:12]


# ---------------------------------------------------------------------
# Provider detection — minimal pattern-based, NEVER calls the network
# ---------------------------------------------------------------------
_PROVIDER_PATTERNS = {
    # OpenAI keys: project/legacy/service-account variants
    "openai": re.compile(r"^sk-(proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{20,}$"),
    # Anthropic Console keys (legacy Claude.ai keys excluded)
    "anthropic": re.compile(r"^sk-ant-[A-Za-z0-9_\-]{20,}$"),
    # Google AI Studio (Gemini API)
    "gemini": re.compile(r"^AIza[0-9A-Za-z_\-]{30,}$"),
}


def detect_provider(plaintext: str) -> Optional[str]:
    """Return "openai" | "anthropic" | "gemini" or None.

    A None return means the key shape doesn't match any of the
    supported providers — the admin endpoint should reject it with
    a 400 so we never store something we can't actually use.
    """
    if not plaintext:
        return None
    cleaned = plaintext.strip()
    # Anthropic check FIRST since `sk-ant-` would also match `sk-…`.
    if _PROVIDER_PATTERNS["anthropic"].match(cleaned):
        return "anthropic"
    if _PROVIDER_PATTERNS["openai"].match(cleaned):
        return "openai"
    if _PROVIDER_PATTERNS["gemini"].match(cleaned):
        return "gemini"
    return None


def assert_provider_match(claimed: str, plaintext: str) -> None:
    """Refuse to store an OpenAI key under the Anthropic slot, etc."""
    detected = detect_provider(plaintext)
    if detected is None:
        raise ValueError(
            "Key format does not match any supported provider "
            "(OpenAI / Anthropic / Google Gemini)."
        )
    if detected != claimed:
        raise ValueError(
            f"Key format looks like a {detected} key, but you are storing "
            f"it under the {claimed} slot. Refusing to mismatch."
        )


# ---------------------------------------------------------------------
# Constant-time helpers (defensive)
# ---------------------------------------------------------------------
def constant_time_equals(a: str, b: str) -> bool:
    """Compare two short strings without timing leaks."""
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    return secrets.compare_digest(a, b)


# Sanity probe at import-time to surface broken installs early.
try:
    _probe = encrypt("__probe__")
    assert decrypt(_probe) == "__probe__"
except Exception as exc:  # noqa: BLE001
    raise RuntimeError(f"secrets_vault self-test failed: {exc}") from exc
