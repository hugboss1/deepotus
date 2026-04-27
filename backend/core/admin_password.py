"""Admin password management.

By default, the active admin password is the env-var ``ADMIN_PASSWORD`` set
at deploy time. To allow runtime rotation **without redeploy**, this module
adds a DB-backed override:

    Collection: ``admin_credentials``
    Doc shape:  { _id: "primary", password_hash: "$2b$12$...",
                  rotated_at: "<iso>", rotated_by: "<jti>" }

When a hash is present, it takes precedence over the env var. Resetting the
DB doc reverts the system to the env-var fallback, so a forgotten password
can always be recovered by the env-var owner.

Hash: bcrypt with cost 12 (constant-time verification, recommended OWASP).
"""

from __future__ import annotations

import logging
import secrets as _secrets
from datetime import datetime, timezone
from typing import Optional

import bcrypt

from core.config import ADMIN_PASSWORD, db

CRED_DOC_ID = "primary"
BCRYPT_COST = 12


async def get_active_password_hash() -> Optional[str]:
    """Return the bcrypt hash currently in DB, or None if not yet set."""
    doc = await db.admin_credentials.find_one({"_id": CRED_DOC_ID})
    if not doc:
        return None
    h = doc.get("password_hash")
    return h if isinstance(h, str) and h else None


async def verify_admin_password(plain: str) -> bool:
    """Verify ``plain`` against the active admin password.

    Order of precedence:
        1. If a bcrypt hash is stored in DB → check against it.
        2. Otherwise fall back to ``secrets.compare_digest`` against the
           env var ``ADMIN_PASSWORD``.

    Always uses constant-time comparison to avoid timing leaks.
    """
    if not plain:
        return False
    db_hash = await get_active_password_hash()
    if db_hash:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), db_hash.encode("utf-8"))
        except (ValueError, TypeError):
            logging.exception("bcrypt verify failed; falling back to env var")
            # If the stored hash is corrupted, fall through to env-var check
            # rather than locking the admin out completely.
    return _secrets.compare_digest(plain, ADMIN_PASSWORD or "")


def _validate_new_password(new_password: str) -> None:
    """Enforce a minimum-strength policy.

    Raises ValueError with a human-readable message if the policy fails.
    Policy:
      - 12+ characters
      - at least 1 letter, 1 digit, 1 special
      - not the literal env var (cannot reuse the bootstrap password)
    """
    if not new_password or len(new_password) < 12:
        raise ValueError("Password must be at least 12 characters.")
    has_alpha = any(c.isalpha() for c in new_password)
    has_digit = any(c.isdigit() for c in new_password)
    has_special = any(not c.isalnum() for c in new_password)
    if not (has_alpha and has_digit and has_special):
        raise ValueError(
            "Password must contain at least one letter, one digit, and one special character.",
        )
    if ADMIN_PASSWORD and _secrets.compare_digest(new_password, ADMIN_PASSWORD):
        raise ValueError(
            "New password cannot be identical to the bootstrap env-var password.",
        )


async def change_admin_password(
    new_password: str,
    *,
    rotated_by_jti: Optional[str] = None,
) -> dict:
    """Hash and persist a new admin password.

    Caller is responsible for verifying the CURRENT password (and 2FA, if
    enabled) BEFORE calling this. We do not re-check here.
    """
    _validate_new_password(new_password)
    new_hash = bcrypt.hashpw(
        new_password.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_COST),
    ).decode("utf-8")
    now = datetime.now(timezone.utc).isoformat()
    await db.admin_credentials.update_one(
        {"_id": CRED_DOC_ID},
        {
            "$set": {
                "password_hash": new_hash,
                "rotated_at": now,
                "rotated_by": rotated_by_jti or "unknown",
            },
            "$inc": {"rotation_count": 1},
        },
        upsert=True,
    )
    return {"ok": True, "rotated_at": now}


async def reset_admin_password() -> dict:
    """Drop the DB override → env-var ``ADMIN_PASSWORD`` becomes active again.

    Use only as a recovery path (e.g. forgotten password); the env-var owner
    can always regain access by removing the DB doc.
    """
    res = await db.admin_credentials.delete_one({"_id": CRED_DOC_ID})
    return {"ok": True, "removed": res.deleted_count}
