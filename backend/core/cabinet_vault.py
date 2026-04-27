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
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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
def _derive_key(mnemonic_phrase: str, salt: bytes) -> bytes:
    """PBKDF2-HMAC-SHA512 → 256-bit AES-GCM key."""
    seed_bytes = Mnemonic.to_seed(mnemonic_phrase.strip(), passphrase="DEEPOTUS")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA512(),
        length=KDF_KEY_LEN,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(seed_bytes)


def _verify_mnemonic(words: str) -> None:
    """Raise ValueError if the phrase is not a valid BIP39 mnemonic."""
    m = Mnemonic("english")
    cleaned = " ".join(words.lower().split())
    if not m.check(cleaned):
        raise ValueError("Invalid BIP39 mnemonic — checksum or wordlist mismatch.")


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
    """Verify the mnemonic, derive the key, cache it, return session metadata."""
    meta = await db.cabinet_vault.find_one({"_id": META_DOC_ID})
    if not meta:
        raise ValueError("Vault not initialised — call /init first.")
    _verify_mnemonic(mnemonic_phrase)
    salt = base64.b64decode(meta["salt"])
    derived = _derive_key(mnemonic_phrase, salt)
    # Defence-in-depth: verify by decrypting the verifier blob.
    try:
        _decrypt(derived, meta["verifier"], aad=b"verifier")
    except Exception as e:
        await _audit("unlock_failed", jti=jti, ip=ip)
        raise ValueError("Mnemonic does not match this vault.") from e
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


def lock() -> None:
    _state.clear()


async def lock_and_audit(*, jti: str, ip: Optional[str] = None) -> None:
    _state.clear()
    await _audit("lock", jti=jti, ip=ip)


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


# ---- Internals -------------------------------------------------------------
def _doc_id(category: str, key: str) -> str:
    return f"secret:{category}:{key}"
