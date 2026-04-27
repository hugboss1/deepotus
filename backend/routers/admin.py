"""Admin-only endpoints (JWT + optional 2FA).

Covers:
    - /admin/login
    - /admin/whitelist  (CRUD + export + blacklist transition)
    - /admin/chat-logs
    - /admin/evolution
    - /admin/blacklist  (CRUD + bulk import)
    - /admin/sessions   (list + revoke + rotate-secret)
    - /admin/2fa/...
    - /admin/email-events
    - /admin/test-email

Note: vault admin endpoints live in `routers.vault` (same admin prefix
but grouped by domain for clarity).
"""

from __future__ import annotations

import asyncio
import csv as csv_module
import io
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import pyotp
import resend
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from core.admin_password import (
    change_admin_password,
    verify_admin_password,
)
from core.config import (
    PUBLIC_BASE_URL,
    RESEND_API_KEY,
    SENDER_EMAIL,
    TWOFA_ISSUER,
    db,
)
from core.models import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminSessionItem,
    AdminSessionList,
    AdminTestEmailRequest,
    AdminTestEmailResponse,
    BlacklistAddRequest,
    BlacklistImportRequest,
    BlacklistImportResponse,
    BlacklistItem,
    BlacklistList,
    ChatLogItem,
    EmailEventItem,
    EvolutionResponse,
    PaginatedChatLogs,
    PaginatedEmailEvents,
    PaginatedWhitelist,
    RotateSecretResponse,
    SimpleOk,
    TwoFADisableRequest,
    TwoFASetupResponse,
    TwoFAStatusResponse,
    TwoFAVerifyRequest,
    WhitelistItem,
)
from core.security import (
    generate_backup_codes,
    get_twofa_config,
    hash_backup_code,
    issue_admin_jwt,
    qr_png_b64,
    rate_limit_check,
    rate_limit_reset,
    require_admin,
    rotate_jwt_secret,
    verify_totp_or_backup,
)
from email_templates import email_subject, render_welcome_email
from routers.public_stats import compute_evolution

router = APIRouter(prefix="/api/admin", tags=["admin"])

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


# ---------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------
@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(req: AdminLoginRequest, request: Request):
    rate_limit_check(request)
    if not req.password or not await verify_admin_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # 2FA enforcement
    twofa = await get_twofa_config()
    if twofa.get("enabled"):
        if not req.totp_code and not req.backup_code:
            raise HTTPException(
                status_code=401,
                detail="2FA required",
                headers={"X-2FA-Required": "true"},
            )
        ok = await verify_totp_or_backup(twofa, req.totp_code, req.backup_code)
        if not ok:
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    rate_limit_reset(request)
    token, jti, exp = await issue_admin_jwt(request)
    return AdminLoginResponse(token=token, expires_at=exp.isoformat(), jti=jti)


# ---------------------------------------------------------------------
# Whitelist CRUD
# ---------------------------------------------------------------------
def _item_from_whitelist_row(r) -> WhitelistItem:
    return WhitelistItem(
        id=r["_id"],
        email=r["email"],
        lang=r.get("lang", "fr"),
        position=int(r.get("position", 0)),
        created_at=r.get("created_at", ""),
        email_sent=bool(r.get("email_sent", False)),
        email_sent_at=r.get("email_sent_at"),
        email_status=r.get("email_status"),
    )


@router.get("/whitelist", response_model=PaginatedWhitelist)
async def admin_whitelist(
    _p: dict = Depends(require_admin),
    limit: int = 50,
    skip: int = 0,
):
    limit = max(1, min(limit, 500))
    skip = max(0, skip)
    cursor = db.whitelist.find({}).sort("position", 1).skip(skip).limit(limit)
    rows = await cursor.to_list(length=limit)
    total = await db.whitelist.count_documents({})
    return PaginatedWhitelist(
        items=[_item_from_whitelist_row(r) for r in rows],
        total=total,
        limit=limit,
        skip=skip,
    )


@router.delete("/whitelist/{entry_id}", response_model=SimpleOk)
async def admin_whitelist_delete(entry_id: str, _p: dict = Depends(require_admin)):
    res = await db.whitelist.delete_one({"_id": entry_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return SimpleOk(ok=True, message="Deleted.")


@router.post("/whitelist/{entry_id}/blacklist", response_model=SimpleOk)
async def admin_whitelist_blacklist(
    entry_id: str,
    _p: dict = Depends(require_admin),
    cooldown_days: Optional[int] = None,
):
    entry = await db.whitelist.find_one({"_id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    email_lc = entry["email"].lower().strip()
    setter = {
        "_id": entry_id,
        "email": email_lc,
        "blacklisted_at": datetime.now(timezone.utc).isoformat(),
        "source_entry_id": entry_id,
        "reason": "blacklisted from admin whitelist",
    }
    if cooldown_days and cooldown_days > 0:
        cd = datetime.now(timezone.utc) + timedelta(days=int(cooldown_days))
        setter["cooldown_until"] = cd.isoformat()
    await db.blacklist.update_one(
        {"email": email_lc},
        {"$set": setter},
        upsert=True,
    )
    await db.whitelist.delete_one({"_id": entry_id})
    return SimpleOk(ok=True, message="Email blacklisted and removed.")


@router.get("/whitelist/export", response_class=PlainTextResponse)
async def admin_whitelist_export(_p: dict = Depends(require_admin)):
    """Return the ENTIRE whitelist as CSV. Adds Content-Disposition for download."""
    cursor = db.whitelist.find({}).sort("position", 1)
    rows = await cursor.to_list(length=1000000)
    buf = io.StringIO()
    w = csv_module.writer(buf)
    w.writerow(
        ["position", "email", "lang", "created_at", "email_sent", "email_status"]
    )
    for r in rows:
        w.writerow(
            [
                r.get("position", ""),
                r.get("email", ""),
                r.get("lang", "fr"),
                r.get("created_at", ""),
                "yes" if r.get("email_sent") else "no",
                r.get("email_status", ""),
            ]
        )
    return PlainTextResponse(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="deepotus_whitelist_full.csv"'
        },
    )


# ---------------------------------------------------------------------
# Chat logs
# ---------------------------------------------------------------------
@router.get("/chat-logs", response_model=PaginatedChatLogs)
async def admin_chat_logs(
    _p: dict = Depends(require_admin),
    limit: int = 50,
    skip: int = 0,
):
    limit = max(1, min(limit, 500))
    skip = max(0, skip)
    cursor = db.chat_logs.find({}).sort("created_at", -1).skip(skip).limit(limit)
    rows = await cursor.to_list(length=limit)
    items = [
        ChatLogItem(
            id=r["_id"],
            session_id=r.get("session_id", ""),
            lang=r.get("lang", "fr"),
            user_message=r.get("user_message", ""),
            reply=r.get("reply", ""),
            created_at=r.get("created_at", ""),
        )
        for r in rows
    ]
    total = await db.chat_logs.count_documents({})
    return PaginatedChatLogs(items=items, total=total, limit=limit, skip=skip)


# ---------------------------------------------------------------------
# Evolution chart
# ---------------------------------------------------------------------
@router.get("/evolution", response_model=EvolutionResponse)
async def admin_evolution(_p: dict = Depends(require_admin), days: int = 30):
    series = await compute_evolution(days)
    return EvolutionResponse(days=len(series), series=series)


# ---------------------------------------------------------------------
# Blacklist CRUD
# ---------------------------------------------------------------------
@router.get("/blacklist", response_model=BlacklistList)
async def admin_blacklist_list(
    _p: dict = Depends(require_admin),
    limit: int = 200,
    skip: int = 0,
):
    limit = max(1, min(limit, 1000))
    skip = max(0, skip)
    cursor = db.blacklist.find({}).sort("blacklisted_at", -1).skip(skip).limit(limit)
    rows = await cursor.to_list(length=limit)
    items = [
        BlacklistItem(
            id=str(r.get("_id", r.get("email"))),
            email=r.get("email", ""),
            blacklisted_at=r.get("blacklisted_at", ""),
            source_entry_id=r.get("source_entry_id"),
            reason=r.get("reason"),
            cooldown_until=r.get("cooldown_until"),
        )
        for r in rows
    ]
    total = await db.blacklist.count_documents({})
    return BlacklistList(items=items, total=total)


@router.post("/blacklist", response_model=SimpleOk)
async def admin_blacklist_add(
    req: BlacklistAddRequest, _p: dict = Depends(require_admin)
):
    email_lc = req.email.lower().strip()
    await db.whitelist.delete_one({"email": email_lc})
    entry_id = f"manual-{uuid.uuid4().hex[:12]}"
    setter = {
        "_id": entry_id,
        "email": email_lc,
        "blacklisted_at": datetime.now(timezone.utc).isoformat(),
        "reason": req.reason or "manually added by admin",
    }
    if req.cooldown_days and req.cooldown_days > 0:
        cd = datetime.now(timezone.utc) + timedelta(days=int(req.cooldown_days))
        setter["cooldown_until"] = cd.isoformat()
    await db.blacklist.update_one(
        {"email": email_lc},
        {"$set": setter},
        upsert=True,
    )
    msg = "Blacklisted."
    if setter.get("cooldown_until"):
        msg = f"Blacklisted until {setter['cooldown_until']}."
    return SimpleOk(ok=True, message=msg)


def _parse_csv_candidates(
    csv_text: str, default_reason: Optional[str]
) -> Tuple[List[Tuple[str, str]], List[str]]:
    """Parse the first column of a CSV as an email list (+ optional 2nd-column reason)."""
    out: List[Tuple[str, str]] = []
    errors: List[str] = []
    try:
        reader = csv_module.reader(io.StringIO(csv_text))
        for row in reader:
            if not row:
                continue
            email = (row[0] or "").strip().lower()
            # skip header row or empty cell
            if not email or email == "email":
                continue
            reason = ""
            if len(row) > 1:
                reason = (row[1] or "").strip()
            out.append((email, reason or default_reason or "bulk import"))
    except Exception as e:
        errors.append(f"CSV parse error: {e}")
    return out, errors


def _normalize_email_list(
    emails: List[str], default_reason: Optional[str]
) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    for email in emails:
        e = (email or "").strip().lower()
        if not e:
            continue
        out.append((e, default_reason or "bulk import"))
    return out


def _compute_cooldown_iso(cooldown_days: Optional[int]) -> Optional[str]:
    if cooldown_days and cooldown_days > 0:
        return (
            datetime.now(timezone.utc) + timedelta(days=int(cooldown_days))
        ).isoformat()
    return None


async def _insert_blacklist_entry(
    email: str, reason: str, now_iso: str, cooldown_iso: Optional[str]
) -> str:
    """Insert one blacklist row + drop any matching whitelist entry. Returns entry_id."""
    entry_id = f"imp-{uuid.uuid4().hex[:12]}"
    doc: Dict[str, object] = {
        "_id": entry_id,
        "email": email,
        "blacklisted_at": now_iso,
        "reason": reason,
        "source": "bulk_import",
    }
    if cooldown_iso:
        doc["cooldown_until"] = cooldown_iso
    await db.blacklist.insert_one(doc)
    await db.whitelist.delete_one({"email": email})
    return entry_id


@router.post("/blacklist/import", response_model=BlacklistImportResponse)
async def admin_blacklist_import(
    req: BlacklistImportRequest, _p: dict = Depends(require_admin)
):
    """Bulk import emails to blacklist.

    Accepts either:
      - csv_text: raw CSV where first column is email (optional 2nd column reason)
      - emails: plain list of emails

    Up to 5000 emails per call.
    """
    candidates: List[Tuple[str, str]] = []
    errors: List[str] = []

    if req.csv_text and req.csv_text.strip():
        parsed, parse_errors = _parse_csv_candidates(req.csv_text, req.reason)
        candidates.extend(parsed)
        errors.extend(parse_errors)

    if req.emails:
        candidates.extend(_normalize_email_list(req.emails, req.reason))

    total_rows = len(candidates)
    if total_rows == 0:
        return BlacklistImportResponse(
            imported=0,
            skipped_invalid=0,
            skipped_existing=0,
            total_rows=0,
            errors=errors,
        )

    if total_rows > 5000:
        raise HTTPException(
            status_code=413,
            detail="Too many rows (max 5000 per import). Split your file.",
        )

    imported = 0
    skipped_invalid = 0
    skipped_existing = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    cooldown_iso = _compute_cooldown_iso(req.cooldown_days)

    for email, reason in candidates:
        if not EMAIL_RE.match(email):
            skipped_invalid += 1
            continue
        if await db.blacklist.find_one({"email": email}):
            skipped_existing += 1
            continue
        await _insert_blacklist_entry(email, reason, now_iso, cooldown_iso)
        imported += 1

    return BlacklistImportResponse(
        imported=imported,
        skipped_invalid=skipped_invalid,
        skipped_existing=skipped_existing,
        total_rows=total_rows,
        errors=errors,
    )


@router.delete("/blacklist/{entry_id}", response_model=SimpleOk)
async def admin_blacklist_remove(entry_id: str, _p: dict = Depends(require_admin)):
    res = await db.blacklist.delete_one({"_id": entry_id})
    if res.deleted_count == 0:
        res = await db.blacklist.delete_one({"email": entry_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Blacklist entry not found")
    return SimpleOk(ok=True, message="Removed from blacklist.")


# ---------------------------------------------------------------------
# Sessions / JWT rotation
# ---------------------------------------------------------------------
@router.get("/sessions", response_model=AdminSessionList)
async def admin_sessions(payload: dict = Depends(require_admin), limit: int = 100):
    cur_jti = payload.get("jti")
    limit = max(1, min(limit, 500))
    rows = (
        await db.admin_sessions.find({})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(length=limit)
    )
    items = [
        AdminSessionItem(
            jti=r["_id"],
            created_at=r.get("created_at", ""),
            last_seen_at=r.get("last_seen_at"),
            expires_at=r.get("expires_at"),
            revoked=bool(r.get("revoked", False)),
            ip=r.get("ip"),
            user_agent=r.get("user_agent"),
            secret_version=r.get("secret_version"),
            is_current=(r["_id"] == cur_jti),
        )
        for r in rows
    ]
    total = await db.admin_sessions.count_documents({})
    return AdminSessionList(items=items, total=total)


@router.delete("/sessions/{jti}", response_model=SimpleOk)
async def admin_revoke_session(jti: str, payload: dict = Depends(require_admin)):
    res = await db.admin_sessions.update_one(
        {"_id": jti},
        {
            "$set": {
                "revoked": True,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return SimpleOk(ok=True, message="Session revoked.")


@router.post("/sessions/revoke-others", response_model=SimpleOk)
async def admin_revoke_others(payload: dict = Depends(require_admin)):
    cur_jti = payload.get("jti")
    res = await db.admin_sessions.update_many(
        {"_id": {"$ne": cur_jti}, "revoked": {"$ne": True}},
        {
            "$set": {
                "revoked": True,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return SimpleOk(ok=True, message=f"Revoked {res.modified_count} session(s).")


@router.post("/rotate-secret", response_model=RotateSecretResponse)
async def admin_rotate_secret(payload: dict = Depends(require_admin)):
    info = await rotate_jwt_secret()
    # Revoke ALL sessions (including current). The caller will be logged out.
    res = await db.admin_sessions.update_many(
        {"revoked": {"$ne": True}},
        {
            "$set": {
                "revoked": True,
                "revoked_at": datetime.now(timezone.utc).isoformat(),
                "revoked_reason": "jwt_secret_rotated",
            }
        },
    )
    return RotateSecretResponse(
        ok=True,
        rotated_at=info["rotated_at"],
        revoked_sessions=res.modified_count,
        message="Secret rotated. All sessions revoked. Please re-login.",
    )


# ---------------------------------------------------------------------
# 2FA
# ---------------------------------------------------------------------
@router.get("/2fa/status", response_model=TwoFAStatusResponse)
async def admin_2fa_status(_p: dict = Depends(require_admin)):
    doc = await get_twofa_config()
    return TwoFAStatusResponse(
        enabled=bool(doc.get("enabled", False)),
        setup_pending=bool(doc.get("setup_pending", False)),
        backup_codes_remaining=len(doc.get("backup_codes_hashes", []) or []),
        enabled_at=doc.get("enabled_at"),
    )


@router.post("/2fa/setup", response_model=TwoFASetupResponse)
async def admin_2fa_setup(_p: dict = Depends(require_admin)):
    """Start a 2FA setup: generate secret + QR + backup codes.
    The secret is stored with `setup_pending=true` until the admin verifies a code.
    """
    secret = pyotp.random_base32()
    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name="admin@deepotus",
        issuer_name=TWOFA_ISSUER,
    )
    qr_b64 = qr_png_b64(uri)
    codes_plain = generate_backup_codes(10)
    codes_hashed = [hash_backup_code(c) for c in codes_plain]
    await db.config.update_one(
        {"_id": "admin_2fa"},
        {
            "$set": {
                "_id": "admin_2fa",
                "secret": secret,
                "setup_pending": True,
                "enabled": False,
                "backup_codes_hashes": codes_hashed,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        },
        upsert=True,
    )
    return TwoFASetupResponse(
        secret=secret,
        otpauth_uri=uri,
        qr_png_base64=qr_b64,
        backup_codes=codes_plain,
    )


@router.post("/2fa/verify", response_model=SimpleOk)
async def admin_2fa_verify(
    req: TwoFAVerifyRequest, _p: dict = Depends(require_admin)
):
    doc = await get_twofa_config()
    if not doc or not doc.get("secret"):
        raise HTTPException(status_code=400, detail="No 2FA setup in progress.")
    ok = False
    try:
        totp = pyotp.TOTP(doc["secret"])
        ok = totp.verify(req.code.strip(), valid_window=1)
    except Exception:
        ok = False
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid code.")

    await db.config.update_one(
        {"_id": "admin_2fa"},
        {
            "$set": {
                "enabled": True,
                "setup_pending": False,
                "enabled_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return SimpleOk(ok=True, message="2FA enabled.")


@router.post("/2fa/disable", response_model=SimpleOk)
async def admin_2fa_disable(
    req: TwoFADisableRequest, _p: dict = Depends(require_admin)
):
    if not await verify_admin_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    doc = await get_twofa_config()
    if not doc or not doc.get("enabled"):
        return SimpleOk(ok=True, message="2FA already disabled.")
    # Require a valid TOTP or backup code to disable
    ok = await verify_totp_or_backup(doc, req.code, req.code)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    await db.config.update_one(
        {"_id": "admin_2fa"},
        {
            "$set": {
                "enabled": False,
                "setup_pending": False,
                "secret": None,
                "backup_codes_hashes": [],
                "disabled_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return SimpleOk(ok=True, message="2FA disabled.")


# ---------------------------------------------------------------------
# Password rotation
# ---------------------------------------------------------------------
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    totp_code: Optional[str] = None  # required iff 2FA is enabled


class PasswordChangeResponse(BaseModel):
    ok: bool
    rotated_at: str
    message: str


class PasswordStatusResponse(BaseModel):
    using_db_override: bool
    rotated_at: Optional[str] = None
    rotation_count: int = 0
    twofa_enabled: bool


@router.get("/password/status", response_model=PasswordStatusResponse)
async def admin_password_status(_p: dict = Depends(require_admin)):
    """Lightweight metadata so the UI can show 'last rotated on …'."""
    doc = await db.admin_credentials.find_one({"_id": "primary"})
    twofa = await get_twofa_config()
    return PasswordStatusResponse(
        using_db_override=bool(doc and doc.get("password_hash")),
        rotated_at=(doc or {}).get("rotated_at"),
        rotation_count=int((doc or {}).get("rotation_count", 0)),
        twofa_enabled=bool(twofa and twofa.get("enabled")),
    )


@router.post("/password/change", response_model=PasswordChangeResponse)
async def admin_password_change(
    req: PasswordChangeRequest,
    p: dict = Depends(require_admin),
):
    """Rotate the admin password.

    Requires:
      1. The CURRENT password to be re-verified (defence in depth — even if
         the JWT is stolen, the attacker still can't rotate the password
         without knowing the current one).
      2. A valid TOTP code (or backup code) IF 2FA is enabled.
      3. The new password to satisfy the strength policy
         (12+ chars, alpha + digit + special, not equal to env-var bootstrap).

    On success, the new bcrypt hash is persisted in MongoDB and used by
    every subsequent /login. The JWT secret is NOT rotated automatically;
    existing sessions stay valid (the admin can manually rotate via the
    Sessions panel if they suspect compromise).
    """
    # 1) Re-verify current password
    if not await verify_admin_password(req.current_password):
        raise HTTPException(status_code=401, detail="Invalid current password")
    # 2) If 2FA is on, require a fresh TOTP / backup code
    twofa_doc = await get_twofa_config()
    if twofa_doc and twofa_doc.get("enabled"):
        if not req.totp_code or not req.totp_code.strip():
            raise HTTPException(
                status_code=401,
                detail="2FA code required",
                headers={"x-2fa-required": "true"},
            )
        ok = await verify_totp_or_backup(twofa_doc, req.totp_code, req.totp_code)
        if not ok:
            raise HTTPException(status_code=401, detail="Invalid 2FA code")
    # 3) Persist the new password
    try:
        result = await change_admin_password(
            req.new_password,
            rotated_by_jti=p.get("jti"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return PasswordChangeResponse(
        ok=True,
        rotated_at=result["rotated_at"],
        message="Password rotated. Existing sessions stay valid.",
    )


# ---------------------------------------------------------------------
# Email events drill-down
# ---------------------------------------------------------------------
@router.get("/email-events", response_model=PaginatedEmailEvents)
async def admin_email_events(
    _p: dict = Depends(require_admin),
    type: Optional[str] = None,
    recipient: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    limit = max(1, min(limit, 500))
    skip = max(0, skip)
    q: Dict[str, object] = {}
    if type:
        q["type"] = type
    if recipient:
        q["recipient"] = recipient.lower().strip()

    cursor = db.email_events.find(q).sort("received_at", -1).skip(skip).limit(limit)
    rows = await cursor.to_list(length=limit)
    items = [
        EmailEventItem(
            id=str(r.get("_id", "")),
            type=r.get("type", "unknown"),
            email_id=r.get("email_id"),
            recipient=r.get("recipient"),
            received_at=r.get("received_at", ""),
            summary=(r.get("raw") or {}).get("data", {}).get("subject")
            or r.get("type"),
        )
        for r in rows
    ]
    total = await db.email_events.count_documents(q)

    # Count per type (for filter chips)
    type_counts: Dict[str, int] = {}
    try:
        pipeline = [
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        tc = await db.email_events.aggregate(pipeline).to_list(length=50)
        for r in tc:
            type_counts[r["_id"] or "unknown"] = int(r.get("count", 0))
    except Exception:
        pass

    return PaginatedEmailEvents(
        items=items,
        total=total,
        limit=limit,
        skip=skip,
        type_counts=type_counts,
    )


# ---------------------------------------------------------------------
# Dedicated test email (does NOT touch whitelist)
# ---------------------------------------------------------------------
@router.post("/test-email", response_model=AdminTestEmailResponse)
async def admin_test_email(
    req: AdminTestEmailRequest, _p: dict = Depends(require_admin)
):
    """Send a one-off transactional test email through Resend.

    Does not create a whitelist entry. Purely for delivery / webhook validation.
    """
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY not configured")

    lang = (req.lang or "fr").lower()
    if lang not in ("fr", "en"):
        lang = "fr"

    recipient = req.email.lower().strip()
    try:
        html = render_welcome_email(
            lang=lang,
            email=recipient,
            position=0,
            base_url=PUBLIC_BASE_URL,
        )
        base_subject = email_subject(lang)
        subject = f"[TEST] {base_subject}"
        params = {
            "from": SENDER_EMAIL,
            "to": [recipient],
            "subject": subject,
            "html": html,
            "tags": [
                {"name": "category", "value": "admin_test"},
                {"name": "lang", "value": lang},
            ],
        }
        res = await asyncio.to_thread(resend.Emails.send, params)
        email_id = None
        if isinstance(res, dict):
            email_id = res.get("id")
        elif hasattr(res, "get"):
            email_id = res.get("id")

        try:
            await db.email_events.insert_one(
                {
                    "_id": str(uuid.uuid4()),
                    "type": "admin.test.sent",
                    "email_id": email_id,
                    "recipient": recipient,
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "raw": {
                        "source": "admin_test_endpoint",
                        "lang": lang,
                        "subject": subject,
                    },
                }
            )
        except Exception:
            logging.exception("Failed to persist admin.test.sent trace")

        logging.info(
            f"[admin/test-email] sent to={recipient} id={email_id} lang={lang}"
        )
        return AdminTestEmailResponse(
            ok=True,
            email_id=email_id,
            recipient=recipient,
            message="Test email dispatched to Resend.",
        )
    except Exception as e:
        logging.exception(f"[admin/test-email] failed for {recipient}: {e}")
        raise HTTPException(status_code=502, detail=f"Resend error: {str(e)[:300]}")
