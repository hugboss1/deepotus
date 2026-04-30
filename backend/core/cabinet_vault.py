"""Cabinet Vault — seed-derived secrets manager.

Single source of truth for ALL deployment secrets (LLM keys, Resend, Helius,
Telegram, X, trading bot referrals, site config, etc.). The vault is locked
by default; unlocking requires the BIP39 seed phrase chosen at setup.

Cryptographic stack
-------------------
- **Mnemonic**  : BIP39 24 words (256-bit entropy) generated server-side at
  setup time. Shown ONCE to the admin and never persisted.
- **KDF**       : PBKDF2-HMAC-SHA512, 300 000 iterations (OWASP 2023+),
  salt = vault_id (a per-install random 16-byte value, persisted).
- **Cipher**    : AES-256-GCM with a unique 96-bit nonce per secret.
  GCM auth tag protects against tampering.
- **Storage**   : MongoDB collection ``cabinet_vault`` (one doc per secret
  + one ``_meta`` doc per vault).

Threat model
------------
✓ DB-only compromise          → useless without the seed.
✓ Server-only compromise      → useless if vault is currently locked
                                 (master key only in RAM, TTL 15 min).
✓ Server compromise + active  → secrets leak for the duration of the
   unlock session                unlock window. Mitigations: TTL, audit
                                 log, manual lock from UI.
✗ Compromised admin device    → keylogger captures the seed at unlock
                                 time. Out of scope; rotate mnemonic.

Usage
-----
1. ``init_vault(mnemonic_words=...)``     → creates the vault, returns vault_id.
2. ``unlock(mnemonic, ttl=900)``          → caches derived key in RAM.
3. ``set_secret(category, key, value)``   → encrypts & persists.
4. ``get_secret(category, key)``          → decrypts via cached key.
5. ``list_secrets()``                     → metadata only (values masked).
6. ``lock()``                             → wipes the cached key.
7. ``export_encrypted(passphrase)``       → returns a re-encrypted dump.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
import secrets
import time
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from mnemonic import Mnemonic

from core.config import db

# ---- Constants -------------------------------------------------------------
META_DOC_ID = "_meta"
KDF_ITERATIONS = 300_000
KDF_KEY_LEN = 32  # 256-bit key for AES-256-GCM
SALT_LEN = 16
NONCE_LEN = 12  # AES-GCM standard
DEFAULT_UNLOCK_TTL_S = 900  # 15 minutes
MNEMONIC_STRENGTH = 256  # → 24 words

# ---- Categorised secret schema --------------------------------------------
# This mirrors the inventory we surface in the admin UI. Any (category, key)
# combination is accepted at runtime; the schema is purely informational.
KNOWN_CATEGORIES: Dict[str, List[str]] = {
    "auth": ["JWT_SECRET", "ADMIN_PASSWORD_NOTES"],
    "llm_emergent": ["EMERGENT_LLM_KEY", "EMERGENT_IMAGE_LLM_KEY"],
    "llm_custom": ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"],
    "email_resend": ["RESEND_API_KEY", "SENDER_EMAIL", "RESEND_WEBHOOK_SECRET"],
    "solana_helius": [
        "HELIUS_API_KEY",
        "HELIUS_WEBHOOK_AUTH",
        "DEEPOTUS_MINT_ADDRESS",
        "DEEPOTUS_POOL_ADDRESS",
    ],
    "telegram": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
    "x_twitter": [
        "X_API_KEY",
        "X_API_SECRET",
        "X_BEARER_TOKEN",
        "X_ACCESS_TOKEN",
        "X_ACCESS_SECRET",
        "X_KOL_HANDLES",
    ],
    "trading_refs": [
        "BONKBOT_REF_URL",
        "MAESTRO_REF_URL",
        "TROJAN_REF_URL",
        "PHOTON_REF_URL",
    ],
    "site": [
        "PUBLIC_BASE_URL",
        "REACT_APP_SITE_URL",
        "CORS_ORIGINS",
        "DEEPOTUS_LAUNCH_ISO",
    ],
    "database": ["MONGO_URL", "DB_NAME"],
}


# ---- In-memory unlock session ---------------------------------------------
@dataclass
class _UnlockedSession:
    key: bytes  # 256-bit master key (AES-GCM)
    unlocked_at: float  # epoch s
    expires_at: float
    unlocked_by_jti: str

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class _VaultState:
    """Process-local singleton holding the derived key for the unlocked session.

    Cleared on lock(), TTL expiry, or service restart. NEVER persisted.
    """

    def __init__(self) -> None:
        self._session: Optional[_UnlockedSession] = None

    def set(self, session: _UnlockedSession) -> None:
        self._session = session

    def get(self) -> Optional[_UnlockedSession]:
        if self._session and self._session.is_expired():
            logging.info("[cabinet-vault] session TTL expired → auto-lock")
            self._session = None
        return self._session

    def clear(self) -> None:
        self._session = None


_state = _VaultState()


# ---- KDF -------------------------------------------------------------------
#: Unicode codepoints that should be treated as word separators even though
#: ``str.isspace()`` returns False for them. Zero-width characters (often
#: pasted invisibly from rich-text editors) and typographic hyphens/dashes
#: (em-dash, en-dash, minus, hyphen) are common offenders when a user
#: copies a mnemonic out of a screenshot or a styled web page.
_FORCE_SPACE_CODEPOINTS = frozenset({
    "\u200b",  # ZERO WIDTH SPACE
    "\u200c",  # ZERO WIDTH NON-JOINER
    "\u200d",  # ZERO WIDTH JOINER
    "\ufeff",  # ZERO WIDTH NO-BREAK SPACE / BOM
    "\u2060",  # WORD JOINER
    "\u00ad",  # SOFT HYPHEN
    "\u2010",  # HYPHEN
    "\u2011",  # NON-BREAKING HYPHEN
    "\u2012",  # FIGURE DASH
    "\u2013",  # EN DASH
    "\u2014",  # EM DASH
    "\u2015",  # HORIZONTAL BAR
    "\u2212",  # MINUS SIGN
    "-",       # plain ASCII hyphen — also a separator in lists
    "_",       # underscore — sometimes pasted as a word separator
    "/",       # forward slash
    ",",       # comma
    ";",       # semicolon
    ".",       # period (rare, but copy-pasted lists sometimes have it)
})


def _normalize_mnemonic(words: str) -> str:
    """Aggressively normalise a user-pasted mnemonic before validation.

    Why: copying the seed phrase from a screenshot, password manager or
    web page often introduces:

      * NFC/NFKC composed characters that BIP39 wordlists don't carry
        (the wordlist is plain ASCII).
      * NBSP (``\\u00A0``), thin space (``\\u2009``), zero-width space
        (``\\u200B``), ideographic space (``\\u3000``).
      * Smart quotes / em-dashes pasted as separators (``— —``).
      * Trailing line breaks, tabs, multiple spaces.
      * Case shifts (BIP39 wordlist is lowercase).

    This function applies NFKD decomposition, replaces every Unicode
    whitespace AND every typographic separator (em-dash, zero-width,
    hyphen, …) with a single ASCII space, strips out everything that
    isn't a lowercase ASCII letter or a space, and collapses runs of
    spaces. The output is safe to feed to ``Mnemonic("english").check``.
    """
    # NFKD decomposition splits accented chars into base + combining;
    # the subsequent ASCII filter drops the combining marks. This means
    # someone who typed "ɑ" instead of "a" will still validate.
    s = unicodedata.normalize("NFKD", words)
    s = s.lower()
    out_chars: List[str] = []
    for ch in s:
        if ch.isspace() or ch in _FORCE_SPACE_CODEPOINTS:
            out_chars.append(" ")
        elif ch.isalpha() and ord(ch) < 128:
            out_chars.append(ch)
        # Everything else (digits, punctuation, emoji, combining marks)
        # is silently dropped — BIP39 has no use for them.
    s = "".join(out_chars)
    # Collapse runs of whitespace.
    return " ".join(s.split())


def _derive_key(mnemonic_phrase: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA512 → 256-bit AES-GCM key."""
    seed_bytes = Mnemonic.to_seed(_normalize_mnemonic(mnemonic_phrase),
                                  passphrase="DEEPOTUS")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=KDF_KEY_LEN,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(seed_bytes)


def _verify_mnemonic(words: str) -> str:
    """Validate a BIP39 mnemonic and return the normalised form.

    Raises ``MnemonicError`` (a structured subclass of ``ValueError``)
    pinpointing the actual failure so the UI can render an actionable
    message instead of a generic "invalid mnemonic". Three classes of
    failure are surfaced:

      * ``wrong_length``      — wrong number of words (must be 12, 15,
                                 18, 21 or 24; we expect 24).
      * ``unknown_words``     — at least one word is NOT in the BIP39
                                 wordlist (typo, OCR mistake, autocorrect).
                                 The first up-to-3 unknowns are listed.
      * ``bad_checksum``      — every word is valid but the checksum
                                 fails: usually a missing or transposed
                                 word, never a wrong-vault situation.
    """
    cleaned = _normalize_mnemonic(words)
    parts = cleaned.split()
    expected = MNEMONIC_STRENGTH // 32 * 3  # 24 for 256-bit entropy
    if len(parts) != expected:
        raise MnemonicError(
            code="wrong_length",
            message=(
                f"Mnemonic must be exactly {expected} words "
                f"(got {len(parts)})."
            ),
            hint=(
                "Tip: paste from your offline backup. Empty lines, page "
                "headers and screenshot artefacts can swallow words."
            ),
        )

    m = Mnemonic("english")
    wordlist = set(m.wordlist)
    unknown = [w for w in parts if w not in wordlist]
    if unknown:
        sample = ", ".join(unknown[:3])
        more = "" if len(unknown) <= 3 else f" (+{len(unknown) - 3} more)"
        raise MnemonicError(
            code="unknown_words",
            message=(
                f"Word(s) not in the BIP39 English wordlist: {sample}{more}."
            ),
            hint=(
                "Tip: BIP39 only uses lowercase a–z. Paste through a "
                "plain-text editor first to strip smart quotes, "
                "non-breaking spaces or autocorrect substitutions."
            ),
        )

    if not m.check(cleaned):
        raise MnemonicError(
            code="bad_checksum",
            message=(
                "All 24 words are valid BIP39 words, but the checksum "
                "fails — at least one word is in the wrong position."
            ),
            hint=(
                "Tip: re-read your backup left-to-right; pairs like "
                "rabbit/rabbit-hole or hand/handle are easy to swap."
            ),
        )
    return cleaned


class MnemonicError(ValueError):
    """Structured error for mnemonic validation failures.

    Subclasses ``ValueError`` so existing `except ValueError` handlers
    (in routers/cabinet_vault.py) keep working transparently. New code
    can reach into ``.code`` / ``.message`` / ``.hint`` to render an
    actionable message in the UI.
    """

    def __init__(self, *, code: str, message: str, hint: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint

    def to_detail(self) -> Dict[str, str]:
        out = {"code": self.code, "message": self.message}
        if self.hint:
            out["hint"] = self.hint
        return out


# ---- Crypto helpers --------------------------------------------------------
def _encrypt(key: bytes, plaintext: str, *, aad: bytes = b"") -> Dict[str, str]:
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_LEN)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), aad)
    return {
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "ciphertext": base64.b64encode(ct).decode("ascii"),
    }


def _decrypt(key: bytes, blob: Dict[str, str], *, aad: bytes = b"") -> str:
    aesgcm = AESGCM(key)
    nonce = base64.b64decode(blob["nonce"])
    ct = base64.b64decode(blob["ciphertext"])
    pt = aesgcm.decrypt(nonce, ct, aad)
    return pt.decode("utf-8")


# ---- Audit log -------------------------------------------------------------
async def _audit(action: str, *, jti: str, ip: Optional[str] = None,
                 category: Optional[str] = None, key: Optional[str] = None,
                 extra: Optional[Dict[str, Any]] = None) -> None:
    """Persist an audit entry. Never stores secret values."""
    entry = {
        "_id": str(uuid.uuid4()),
        "action": action,
        "at": datetime.now(timezone.utc).isoformat(),
        "jti": jti,
        "ip": ip,
        "category": category,
        "key": key,
        "extra": extra or {},
    }
    await db.cabinet_vault_audit.insert_one(entry)


# ---- Vault lifecycle -------------------------------------------------------
async def is_initialised() -> bool:
    return bool(await db.cabinet_vault.find_one({"_id": META_DOC_ID}))


async def get_status() -> Dict[str, Any]:
    """Public-ish status surface for the UI:
       initialised + locked + (unlock metadata if currently unlocked).
    """
    meta = await db.cabinet_vault.find_one({"_id": META_DOC_ID}) or {}
    sess = _state.get()
    return {
        "initialised": bool(meta),
        "locked": sess is None,
        "unlocked_at": (
            datetime.fromtimestamp(time.time() - (time.monotonic() - sess.unlocked_at), tz=timezone.utc).isoformat()
            if sess else None
        ),
        "expires_in_seconds": (
            max(0, int(sess.expires_at - time.monotonic())) if sess else None
        ),
        "vault_created_at": meta.get("created_at"),
        "secret_count": await db.cabinet_vault.count_documents({"_id": {"$ne": META_DOC_ID}}),
    }


async def init_vault(*, jti: str, ip: Optional[str] = None) -> Dict[str, Any]:
    """Create a brand-new vault. Returns the freshly-generated mnemonic.

    Raises ValueError if a vault already exists (use ``reinit_vault`` instead).
    """
    if await is_initialised():
        raise ValueError("Vault already initialised — refusing to overwrite.")
    m = Mnemonic("english")
    phrase = m.generate(strength=MNEMONIC_STRENGTH)
    salt = secrets.token_bytes(SALT_LEN)
    # Verifier blob: encrypt a known constant so we can later detect a wrong
    # mnemonic at unlock time without leaking actual secrets.
    derived = _derive_key(phrase, salt)
    verifier = _encrypt(derived, "DEEPOTUS_VAULT_OK", aad=b"verifier")
    # Wipe the local copy of the key — it'll be re-derived at unlock.
    derived = b"\x00" * KDF_KEY_LEN  # noqa: F841
    now = datetime.now(timezone.utc).isoformat()
    await db.cabinet_vault.update_one(
        {"_id": META_DOC_ID},
        {
            "$set": {
                "salt": base64.b64encode(salt).decode("ascii"),
                "verifier": verifier,
                "kdf": {
                    "algo": "PBKDF2-HMAC-SHA512",
                    "iterations": KDF_ITERATIONS,
                    "key_len": KDF_KEY_LEN,
                },
                "cipher": "AES-256-GCM",
                "mnemonic_words": MNEMONIC_STRENGTH // 32 * 3,  # 24 for 256
                "created_at": now,
                "created_by_jti": jti,
            }
        },
        upsert=True,
    )
    await _audit("init", jti=jti, ip=ip, extra={"mnemonic_words": 24})
    return {
        "mnemonic": phrase,  # SHOWN ONCE — the API layer is responsible for not logging this
        "vault_created_at": now,
        "instructions": (
            "Write these 24 words down on paper or store them in a hardware "
            "password manager. They are NEVER stored on the server. Without "
            "them you will permanently lose access to every secret stored in "
            "the vault. The Deep State will not bail you out."
        ),
    }


async def unlock(mnemonic_phrase: str, *, jti: str, ip: Optional[str] = None,
                 ttl_seconds: int = DEFAULT_UNLOCK_TTL_S) -> Dict[str, Any]:
    """Verify the mnemonic, derive the key, cache it, return session metadata.

    Failure surfaces three structured errors via ``MnemonicError`` /
    ``VaultMismatchError`` so the UI can render the right hint instead
    of a generic "Unlock failed":

      * ``wrong_length`` / ``unknown_words`` / ``bad_checksum``
            — phrase fails BIP39 validation (typo, missing word, …).
      * ``vault_mismatch``
            — phrase is structurally valid but does not match THIS
              vault's verifier blob. Strong signal that the vault was
              re-initialised between the time the user wrote the seed
              down and the unlock attempt. The "factory reset" flow
              produces exactly this situation if used on a vault that
              already had a real seed.
    """
    meta = await db.cabinet_vault.find_one({"_id": META_DOC_ID})
    if not meta:
        raise ValueError("Vault not initialised — call /init first.")
    cleaned = _verify_mnemonic(mnemonic_phrase)  # raises MnemonicError
    salt = base64.b64decode(meta["salt"])
    derived = _derive_key(cleaned, salt)
    # Defence-in-depth: verify by decrypting the verifier blob.
    try:
        _decrypt(derived, meta["verifier"], aad=b"verifier")
    except Exception as e:
        await _audit("unlock_failed", jti=jti, ip=ip,
                     extra={"reason": "vault_mismatch"})
        raise VaultMismatchError() from e
    sess = _UnlockedSession(
        key=derived,
        unlocked_at=time.monotonic(),
        expires_at=time.monotonic() + ttl_seconds,
        unlocked_by_jti=jti,
    )
    _state.set(sess)
    await _audit("unlock", jti=jti, ip=ip, extra={"ttl_seconds": ttl_seconds})
    return {
        "ok": True,
        "expires_in_seconds": ttl_seconds,
    }


class VaultMismatchError(ValueError):
    """Mnemonic is structurally valid but does not match this vault.

    Distinct from ``MnemonicError`` because the user's input is fine —
    it just doesn't unlock THIS instance. Most common cause:
    factory_reset_vault() was called between init and the unlock attempt,
    producing a brand-new ``salt`` + ``verifier`` so the old seed no
    longer derives the right key.
    """

    code = "vault_mismatch"
    message = (
        "Mnemonic is a valid BIP39 phrase but does not match this vault."
    )
    hint = (
        "If you ran a factory reset (or re-initialised the vault), the "
        "previous seed is permanently invalidated. The new seed printed "
        "after the reset is the only one that will unlock this vault."
    )

    def __init__(self):
        super().__init__(self.message)

    def to_detail(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message, "hint": self.hint}


def lock() -> None:
    _state.clear()


async def lock_and_audit(*, jti: str, ip: Optional[str] = None) -> None:
    _state.clear()
    await _audit("lock", jti=jti, ip=ip)


# ---- Factory reset (DESTRUCTIVE) ------------------------------------------
async def factory_reset_vault(
    *,
    jti: str,
    ip: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Wipe the vault back to a pristine pre-init state.

    *DESTRUCTIVE*: removes the meta doc + every encrypted secret. The
    audit log is kept (we even append a final ``factory_reset`` entry
    BEFORE the wipe so the trace survives) so post-mortem investigation
    is still possible.

    Caller is responsible for enforcing strong guards at the router
    layer (admin password recheck, 2FA, confirm string, vault-locked
    state). This module function only performs the destructive write
    and the audit trail — it does NOT verify auth/permissions.

    Returns counts for the UI to display:
        {
          "ok": true,
          "deleted_meta": 1,
          "deleted_secrets": <int>,
          "reset_at": <iso>,
        }
    """
    # Snapshot counts BEFORE deletion (for the audit + UI feedback)
    secret_count = await db.cabinet_vault.count_documents(
        {"_id": {"$ne": META_DOC_ID}}
    )
    had_meta = await is_initialised()
    now = datetime.now(timezone.utc).isoformat()

    # Audit FIRST so the trace exists even if the wipe partially fails.
    await _audit(
        "factory_reset",
        jti=jti,
        ip=ip,
        extra={
            "secret_count_at_reset": secret_count,
            "had_meta": had_meta,
            "reset_at": now,
            **(extra or {}),
        },
    )

    # Drop the in-memory unlocked session (defensive — router should
    # already refuse the call when unlocked, but belt-and-braces).
    _state.clear()

    # Wipe everything in cabinet_vault (meta + secrets). Audit log is
    # explicitly preserved.
    res = await db.cabinet_vault.delete_many({})

    logging.warning(
        "[cabinet-vault] FACTORY RESET executed by jti=%s ip=%s "
        "(deleted=%d, had_meta=%s, secrets=%d)",
        jti, ip, res.deleted_count, had_meta, secret_count,
    )

    return {
        "ok": True,
        "deleted_meta": 1 if had_meta else 0,
        "deleted_secrets": secret_count,
        "reset_at": now,
    }


def _require_unlocked() -> _UnlockedSession:
    sess = _state.get()
    if not sess:
        raise PermissionError("VAULT_LOCKED")
    return sess


# ---- Secret CRUD -----------------------------------------------------------
async def set_secret(category: str, key: str, value: str, *,
                     jti: str, ip: Optional[str] = None) -> Dict[str, Any]:
    """Encrypt & persist a secret. Overwrites existing value for (cat, key)."""
    if not category or not key:
        raise ValueError("category and key are required.")
    sess = _require_unlocked()
    aad = f"{category}/{key}".encode("utf-8")
    blob = _encrypt(sess.key, value, aad=aad)
    doc_id = _doc_id(category, key)
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.cabinet_vault.find_one({"_id": doc_id})
    rotation_count = (existing or {}).get("rotation_count", 0) + (1 if existing else 0)
    await db.cabinet_vault.update_one(
        {"_id": doc_id},
        {
            "$set": {
                "category": category,
                "key": key,
                "blob": blob,
                "updated_at": now,
                "updated_by_jti": jti,
                "rotation_count": rotation_count,
                "value_length": len(value),
                "value_fingerprint": hashlib.sha256(value.encode("utf-8")).hexdigest()[:12],
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
    await _audit("set" if existing else "create", jti=jti, ip=ip,
                 category=category, key=key,
                 extra={"value_length": len(value)})
    return {"ok": True, "rotation_count": rotation_count}


async def get_secret(category: str, key: str, *,
                     jti: str, ip: Optional[str] = None) -> Dict[str, Any]:
    """Decrypt & return a single secret. Audit-logged."""
    sess = _require_unlocked()
    doc_id = _doc_id(category, key)
    doc = await db.cabinet_vault.find_one({"_id": doc_id})
    if not doc:
        raise KeyError(f"{category}/{key} not found")
    aad = f"{category}/{key}".encode("utf-8")
    try:
        plaintext = _decrypt(sess.key, doc["blob"], aad=aad)
    except Exception as e:
        await _audit("get_failed", jti=jti, ip=ip, category=category, key=key)
        raise ValueError("Decryption failed — wrong key or tampered data") from e
    await _audit("get", jti=jti, ip=ip, category=category, key=key)
    return {
        "category": category,
        "key": key,
        "value": plaintext,
        "updated_at": doc.get("updated_at"),
        "rotation_count": doc.get("rotation_count", 0),
    }


async def delete_secret(category: str, key: str, *,
                        jti: str, ip: Optional[str] = None) -> Dict[str, Any]:
    _require_unlocked()
    doc_id = _doc_id(category, key)
    res = await db.cabinet_vault.delete_one({"_id": doc_id})
    if res.deleted_count:
        await _audit("delete", jti=jti, ip=ip, category=category, key=key)
    return {"ok": True, "deleted": res.deleted_count}


# ---- Silent service-internal getter ----------------------------------------
async def get_secret_silent(category: str, key: str) -> Optional[str]:
    """Read a secret WITHOUT audit logging — used by internal backend services
    (LLM router, email service, Helius client) that need to resolve API keys
    on every request.

    Returns ``None`` instead of raising when:
      * the vault is currently locked,
      * the (category, key) entry does not exist,
      * decryption fails for any reason.

    The audit log would otherwise be flooded with ``get`` events on each
    HTTP request — *human* admin reveals are still audited via
    :func:`get_secret`.
    """
    sess = _state.get()
    if not sess:
        return None
    doc = await db.cabinet_vault.find_one({"_id": _doc_id(category, key)})
    if not doc or "blob" not in doc:
        return None
    aad = f"{category}/{key}".encode("utf-8")
    try:
        return _decrypt(sess.key, doc["blob"], aad=aad)
    except Exception:  # noqa: BLE001 — never raise inside service layer
        return None


def is_unlocked() -> bool:
    """Cheap check used by the secret-provider cache to short-circuit
    Mongo reads when the vault is locked anyway."""
    return _state.get() is not None


async def list_secrets(*, jti: str, ip: Optional[str] = None) -> Dict[str, Any]:
    """Return metadata for all secrets — never the plaintext values.

    Output is grouped by category; each entry has fingerprint + length so
    the UI can render a masked preview without unlocking the value.
    """
    _require_unlocked()
    cursor = db.cabinet_vault.find({"_id": {"$ne": META_DOC_ID}})
    by_cat: Dict[str, List[Dict[str, Any]]] = {c: [] for c in KNOWN_CATEGORIES}
    async for doc in cursor:
        cat = doc.get("category", "uncategorised")
        by_cat.setdefault(cat, []).append({
            "key": doc.get("key"),
            "updated_at": doc.get("updated_at"),
            "rotation_count": doc.get("rotation_count", 0),
            "value_length": doc.get("value_length", 0),
            "value_fingerprint": doc.get("value_fingerprint"),
        })
    # Annotate KNOWN keys that haven't been set yet so the UI can prompt.
    for cat, known_keys in KNOWN_CATEGORIES.items():
        present_keys = {e["key"] for e in by_cat.get(cat, [])}
        missing = [k for k in known_keys if k not in present_keys]
        for k in missing:
            by_cat.setdefault(cat, []).append({
                "key": k,
                "updated_at": None,
                "rotation_count": 0,
                "value_length": 0,
                "value_fingerprint": None,
                "_unset": True,
            })
    await _audit("list", jti=jti, ip=ip,
                 extra={"total": sum(len(v) for v in by_cat.values())})
    return {"categories": by_cat, "schema": KNOWN_CATEGORIES}


# ---- Audit log surface -----------------------------------------------------
async def get_audit_log(limit: int = 100) -> List[Dict[str, Any]]:
    cursor = db.cabinet_vault_audit.find({}).sort("at", -1).limit(limit)
    return [doc async for doc in cursor]


# ---- Encrypted backup / restore -------------------------------------------
async def export_encrypted(passphrase: str, *,
                           jti: str, ip: Optional[str] = None) -> Dict[str, Any]:
    """Re-encrypt all secrets with a separate passphrase-derived key.

    The exported blob is portable: it can be stored cold (USB / paper print
    of QR / encrypted file) and restored later via ``import_encrypted``.
    Crucially, the export does NOT contain the mnemonic.
    """
    sess = _require_unlocked()
    if not passphrase or len(passphrase) < 12:
        raise ValueError("Export passphrase must be at least 12 characters.")
    salt = secrets.token_bytes(SALT_LEN)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(), length=KDF_KEY_LEN, salt=salt,
        iterations=KDF_ITERATIONS,
    )
    export_key = kdf.derive(passphrase.encode("utf-8"))
    payload: Dict[str, Any] = {"format": "deepotus-vault-v1", "secrets": []}
    cursor = db.cabinet_vault.find({"_id": {"$ne": META_DOC_ID}})
    async for doc in cursor:
        category = doc["category"]
        key = doc["key"]
        aad = f"{category}/{key}".encode("utf-8")
        plain = _decrypt(sess.key, doc["blob"], aad=aad)
        re_blob = _encrypt(export_key, plain, aad=aad)
        payload["secrets"].append({
            "category": category, "key": key, "blob": re_blob,
            "updated_at": doc.get("updated_at"),
        })
    await _audit("export", jti=jti, ip=ip,
                 extra={"secret_count": len(payload["secrets"])})
    return {
        "format": "deepotus-vault-v1",
        "kdf": {"algo": "PBKDF2-HMAC-SHA512", "iterations": KDF_ITERATIONS,
                "salt": base64.b64encode(salt).decode("ascii")},
        "secrets": payload["secrets"],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


async def import_encrypted(
    bundle: Dict[str, Any], passphrase: str, *,
    overwrite: bool = False, jti: str, ip: Optional[str] = None,
) -> Dict[str, Any]:
    """Restore secrets from a previously-exported encrypted bundle.

    The export bundle was re-encrypted under a passphrase-derived key
    (see :func:`export_encrypted`). Here we reverse that:

      1. Validate ``bundle["format"]`` and KDF params.
      2. Re-derive the export key from the passphrase + bundle salt.
      3. For each entry:
           - decrypt with the export key (verifies passphrase + integrity),
           - re-encrypt with the *currently unlocked* vault master key,
           - store under (category, key).
      4. Audit-log the global outcome (counts, never the values).

    Conflict policy
    ---------------
    By default we **skip** entries whose ``(category, key)`` already
    exists in the live vault to avoid clobbering newer rotations. Pass
    ``overwrite=True`` to force replace. Either way, conflicts are
    counted in the response so the UI can warn the admin.

    Failures
    --------
    Any individual decrypt failure aborts the whole import (atomic
    semantics) — partial restores are dangerous.
    """
    sess = _require_unlocked()
    if not isinstance(bundle, dict) or bundle.get("format") != "deepotus-vault-v1":
        raise ValueError("Unsupported bundle format. Expected deepotus-vault-v1.")
    if not passphrase or len(passphrase) < 12:
        raise ValueError("Import passphrase must be at least 12 characters.")

    kdf_meta = bundle.get("kdf") or {}
    salt_b64 = kdf_meta.get("salt")
    iterations = int(kdf_meta.get("iterations") or KDF_ITERATIONS)
    if not salt_b64:
        raise ValueError("Bundle is missing kdf.salt — refusing to import.")
    try:
        salt = base64.b64decode(salt_b64)
    except Exception as e:
        raise ValueError("Bundle kdf.salt is not valid base64.") from e

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(), length=KDF_KEY_LEN, salt=salt,
        iterations=iterations,
    )
    import_key = kdf.derive(passphrase.encode("utf-8"))

    secrets_in: List[Dict[str, Any]] = bundle.get("secrets") or []
    if not isinstance(secrets_in, list):
        raise ValueError("Bundle.secrets must be an array.")

    # ---- Pre-flight: decrypt EVERY entry up-front so a wrong passphrase
    # is detected before we touch the live vault. Atomicity over speed.
    decrypted: List[Tuple[str, str, str, Optional[str]]] = []
    for entry in secrets_in:
        category = (entry or {}).get("category")
        key = (entry or {}).get("key")
        blob = (entry or {}).get("blob")
        if not category or not key or not isinstance(blob, dict):
            raise ValueError("Malformed entry in bundle.secrets.")
        aad = f"{category}/{key}".encode("utf-8")
        try:
            plain = _decrypt(import_key, blob, aad=aad)
        except Exception as e:  # noqa: BLE001
            await _audit("import_failed", jti=jti, ip=ip,
                         extra={"reason": "decrypt", "category": category,
                                "key": key})
            raise ValueError(
                "Decryption failed — wrong passphrase or tampered bundle."
            ) from e
        decrypted.append((category, key, plain, entry.get("updated_at")))

    # ---- Apply: encrypt with vault master key + persist.
    imported, skipped, replaced = 0, 0, 0
    for category, key, plain, _src_updated_at in decrypted:
        doc_id = _doc_id(category, key)
        existing = await db.cabinet_vault.find_one({"_id": doc_id})
        if existing and not overwrite:
            skipped += 1
            continue
        aad = f"{category}/{key}".encode("utf-8")
        new_blob = _encrypt(sess.key, plain, aad=aad)
        now = datetime.now(timezone.utc).isoformat()
        rotation_count = (existing or {}).get("rotation_count", 0) + (1 if existing else 0)
        await db.cabinet_vault.update_one(
            {"_id": doc_id},
            {
                "$set": {
                    "category": category,
                    "key": key,
                    "blob": new_blob,
                    "updated_at": now,
                    "updated_by_jti": jti,
                    "rotation_count": rotation_count,
                    "value_length": len(plain),
                    "value_fingerprint": hashlib.sha256(plain.encode("utf-8")).hexdigest()[:12],
                    "imported_from_backup_at": now,
                },
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        if existing:
            replaced += 1
        else:
            imported += 1

    await _audit(
        "import", jti=jti, ip=ip,
        extra={
            "imported": imported,
            "replaced": replaced,
            "skipped": skipped,
            "overwrite": overwrite,
        },
    )
    return {
        "ok": True,
        "imported": imported,
        "replaced": replaced,
        "skipped": skipped,
        "total_in_bundle": len(decrypted),
    }


# ---- Internals -------------------------------------------------------------
def _doc_id(category: str, key: str) -> str:
    return f"secret:{category}:{key}"
