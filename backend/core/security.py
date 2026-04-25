"""Security helpers: JWT lifecycle, rate limiting, admin dependency, 2FA.

The JWT secret is persisted in Mongo so it survives restarts and can be
rotated at will. A short grace window lets tokens signed with the previous
secret stay valid during rotation.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Dict, List, Optional

import jwt
import pyotp
import qrcode
from fastapi import Header, HTTPException, Request

from core.config import (
    JWT_ALGO,
    JWT_TTL_HOURS,
    ROTATION_GRACE_HOURS,
    db,
)

# ---------------------------------------------------------------------
# JWT SECRET management (DB-backed, rotatable)
# ---------------------------------------------------------------------
_JWT_CACHE: Dict[str, Optional[str]] = {
    "current": None,
    "previous": None,
    "rotated_at": None,
}


async def ensure_jwt_secrets() -> dict:
    """Load JWT secrets from DB; initialize from env or random on first run."""
    import os

    doc = await db.config.find_one({"_id": "jwt_secrets"})
    if not doc:
        current = os.environ.get("JWT_SECRET", secrets.token_urlsafe(48))
        doc = {
            "_id": "jwt_secrets",
            "current": current,
            "previous": None,
            "rotated_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.config.insert_one(doc)
    _JWT_CACHE["current"] = doc["current"]
    _JWT_CACHE["previous"] = doc.get("previous")
    _JWT_CACHE["rotated_at"] = doc.get("rotated_at")
    return doc


async def rotate_jwt_secret() -> dict:
    """Generate a fresh JWT signing secret, demoting the previous one."""
    new_secret = secrets.token_urlsafe(48)
    now_iso = datetime.now(timezone.utc).isoformat()
    doc = await db.config.find_one({"_id": "jwt_secrets"}) or {}
    prev = doc.get("current")  # move current to previous
    await db.config.update_one(
        {"_id": "jwt_secrets"},
        {
            "$set": {
                "current": new_secret,
                "previous": prev,
                "rotated_at": now_iso,
                "previous_invalid_after": (
                    datetime.now(timezone.utc)
                    + timedelta(hours=ROTATION_GRACE_HOURS)
                ).isoformat(),
            }
        },
        upsert=True,
    )
    _JWT_CACHE["current"] = new_secret
    _JWT_CACHE["previous"] = prev
    _JWT_CACHE["rotated_at"] = now_iso
    return {
        "rotated_at": now_iso,
        "previous_valid_until": _JWT_CACHE["rotated_at"],
    }


# ---------------------------------------------------------------------
# Rate limiter (in-memory per IP)
# ---------------------------------------------------------------------
RATE_LIMIT_WINDOW = 600
RATE_LIMIT_MAX = 5
_login_attempts: Dict[str, deque] = defaultdict(deque)


def client_ip(request: Request) -> str:
    xf = request.headers.get("x-forwarded-for")
    if xf:
        return xf.split(",")[0].strip()
    xr = request.headers.get("x-real-ip")
    if xr:
        return xr.strip()
    return request.client.host if request.client else "unknown"


def rate_limit_check(request: Request) -> None:
    ip = client_ip(request)
    now = time.time()
    q = _login_attempts[ip]
    while q and (now - q[0]) > RATE_LIMIT_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT_MAX:
        retry_after = int(RATE_LIMIT_WINDOW - (now - q[0]))
        raise HTTPException(
            status_code=429,
            detail=f"Too many login attempts. Retry in {retry_after}s.",
            headers={"Retry-After": str(max(1, retry_after))},
        )
    q.append(now)


def rate_limit_reset(request: Request) -> None:
    _login_attempts.pop(client_ip(request), None)


# ---------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------
async def issue_admin_jwt(
    request: Optional[Request] = None,
) -> tuple[str, str, datetime]:
    await ensure_jwt_secrets()
    jti = secrets.token_urlsafe(12)
    iat = datetime.now(timezone.utc)
    exp = iat + timedelta(hours=JWT_TTL_HOURS)
    payload = {
        "sub": "deepotus-admin",
        "role": "admin",
        "iat": int(iat.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
    }
    secret = _JWT_CACHE["current"]
    token = jwt.encode(payload, secret, algorithm=JWT_ALGO)

    session_doc = {
        "_id": jti,
        "created_at": iat.isoformat(),
        "last_seen_at": iat.isoformat(),
        "expires_at": exp.isoformat(),
        "revoked": False,
        "ip": client_ip(request) if request else None,
        "user_agent": (request.headers.get("user-agent", "") if request else "")[:300],
        "secret_version": "current",
    }
    await db.admin_sessions.insert_one(session_doc)
    return token, jti, exp


async def _previous_grace_active() -> bool:
    """Check the DB-stored expiry for the previous JWT secret.

    Returns True iff the previous secret has not exceeded its rotation
    grace window. Any malformed/missing date is treated as "still valid"
    so legacy data does not lock admins out unexpectedly.
    """
    doc = await db.config.find_one({"_id": "jwt_secrets"})
    piva = (doc or {}).get("previous_invalid_after")
    if not piva:
        return True
    try:
        expiry = datetime.fromisoformat(piva.replace("Z", "+00:00"))
    except ValueError:
        return True  # corrupt timestamp → don't pre-emptively reject
    return datetime.now(timezone.utc) <= expiry


def _try_decode(token: str, secret: str) -> dict:
    """Decode the JWT against `secret`. Raises on failure."""
    return jwt.decode(token, secret, algorithms=[JWT_ALGO])


async def verify_admin_jwt(token: str) -> dict:
    """Verify a JWT against the active and (if any) previous secret.

    Loop is flat with early returns — no nested conditionals — and
    surfaces ExpiredSignatureError specifically so callers can map it
    to the right HTTP status.
    """
    await ensure_jwt_secrets()
    last_err: Optional[Exception] = None

    # Try the current secret first.
    current = _JWT_CACHE.get("current")
    if current:
        try:
            return _try_decode(token, current)
        except Exception as e:  # noqa: BLE001
            last_err = e

    # Fall back to the previous secret if it is still inside its grace window.
    previous = _JWT_CACHE.get("previous")
    if previous and await _previous_grace_active():
        try:
            return _try_decode(token, previous)
        except Exception as e:  # noqa: BLE001
            last_err = e

    if isinstance(last_err, jwt.ExpiredSignatureError):
        raise last_err
    raise jwt.InvalidTokenError(str(last_err) if last_err else "Invalid token")


async def require_admin(
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None),
) -> dict:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(None, 1)[1].strip()
    elif x_admin_token:
        token = x_admin_token.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = await verify_admin_jwt(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    jti = payload.get("jti")
    if jti:
        sess = await db.admin_sessions.find_one({"_id": jti})
        if sess and sess.get("revoked"):
            raise HTTPException(status_code=401, detail="Session revoked")
        if sess:
            await db.admin_sessions.update_one(
                {"_id": jti},
                {
                    "$set": {
                        "last_seen_at": datetime.now(timezone.utc).isoformat()
                    }
                },
            )
    return payload


# ---------------------------------------------------------------------
# 2FA helpers
# ---------------------------------------------------------------------
async def get_twofa_config() -> dict:
    doc = await db.config.find_one({"_id": "admin_2fa"})
    return doc or {}


def hash_backup_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def generate_backup_codes(n: int = 10) -> List[str]:
    out: List[str] = []
    for _ in range(n):
        raw = secrets.token_hex(5)  # 10 chars
        out.append(f"{raw[:5]}-{raw[5:]}".upper())
    return out


def qr_png_b64(uri: str) -> str:
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


async def verify_totp_or_backup(
    twofa_cfg: dict,
    code: Optional[str],
    backup_code: Optional[str],
) -> bool:
    """Return True if the provided code or backup_code matches."""
    secret = twofa_cfg.get("secret")
    if not secret:
        return False
    if code:
        try:
            totp = pyotp.TOTP(secret)
            if totp.verify(code.strip(), valid_window=1):
                return True
        except Exception:
            pass
    if backup_code:
        bch = hash_backup_code(backup_code)
        codes = set(twofa_cfg.get("backup_codes_hashes", []))
        if bch in codes:
            codes.remove(bch)
            await db.config.update_one(
                {"_id": "admin_2fa"},
                {"$set": {"backup_codes_hashes": list(codes)}},
            )
            return True
    return False
