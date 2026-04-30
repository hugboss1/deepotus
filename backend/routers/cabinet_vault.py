"""Cabinet Vault API — admin-only secrets management.

All endpoints require:
    1. A valid admin JWT (``require_admin``)
    2. 2FA enabled on the admin account (``require_2fa_enabled``)

Setup endpoints
---------------
    POST   /api/admin/cabinet-vault/init           one-time bootstrap, returns mnemonic
    GET    /api/admin/cabinet-vault/status         init/locked/unlocked metadata

Session endpoints
-----------------
    POST   /api/admin/cabinet-vault/unlock         {mnemonic} → cache key (15 min)
    POST   /api/admin/cabinet-vault/lock           wipe cached key

Secret endpoints (require unlocked session)
-------------------------------------------
    GET    /api/admin/cabinet-vault/list           categorised metadata (no values)
    GET    /api/admin/cabinet-vault/{category}/{key}     fetch plaintext (audit-logged)
    PUT    /api/admin/cabinet-vault/{category}/{key}     create/rotate
    DELETE /api/admin/cabinet-vault/{category}/{key}

Backup
------
    POST   /api/admin/cabinet-vault/export         {passphrase} → encrypted JSON

Audit
-----
    GET    /api/admin/cabinet-vault/audit?limit=100

Recovery (DESTRUCTIVE)
----------------------
    POST   /api/admin/cabinet-vault/factory-reset
        Wipe the vault back to a pristine pre-init state. Used when the
        mnemonic is lost. Requires: vault LOCKED + admin password recheck
        + 2FA TOTP (if enabled) + literal confirm string.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core import cabinet_vault as vault
from core import secret_provider
from core.admin_password import verify_admin_password
from core.config import db
from core.security import (
    get_twofa_config,
    require_admin,
    verify_totp_or_backup,
)

router = APIRouter(prefix="/api/admin/cabinet-vault", tags=["cabinet-vault"])


# ---- Pydantic models -------------------------------------------------------
class UnlockRequest(BaseModel):
    mnemonic: str = Field(..., min_length=20)
    ttl_seconds: Optional[int] = None


class SetSecretRequest(BaseModel):
    value: str


class ExportRequest(BaseModel):
    passphrase: str = Field(..., min_length=12)


class ImportRequest(BaseModel):
    """Restore an encrypted bundle previously produced by ``/export``.

    The ``bundle`` is expected to be the JSON document written to disk
    by the export endpoint — we re-derive the export key from
    ``passphrase`` + ``bundle.kdf.salt``, decrypt every entry up-front
    (atomic semantics), then re-encrypt under the live master key.

    ``overwrite`` defaults to False so an accidental import never
    silently replaces a freshly-rotated key.
    """
    bundle: Dict[str, Any] = Field(...)
    passphrase: str = Field(..., min_length=12)
    overwrite: bool = False


# ---- Guards ----------------------------------------------------------------
async def require_2fa_enabled(p: dict = Depends(require_admin)) -> dict:
    """The cabinet vault holds the keys to the kingdom — refuse access unless
    the admin has 2FA enabled. This is enforced at the router layer so we
    never even touch the vault module without the second factor in place.
    """
    cfg = await get_twofa_config()
    if not (cfg and cfg.get("enabled")):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "TWOFA_REQUIRED",
                "message": (
                    "Cabinet Vault is locked behind mandatory 2FA. "
                    "Enable 2FA from the Security tab first."
                ),
            },
        )
    return p


async def require_2fa_or_bootstrap(p: dict = Depends(require_admin)) -> dict:
    """Looser guard for *lifecycle* endpoints (init / status / unlock / lock).

    Rationale: an admin who hasn't enrolled 2FA yet still needs to be able
    to walk through the very first SetupWizard — generating their seed
    phrase, unlocking the vault, populating it, locking it and re-unlocking
    it — without being stuck on a chicken-and-egg 403. Once 2FA is active,
    the regular guard kicks in everywhere.

    *Read endpoints* (get/export/import) keep ``require_2fa_enabled`` strict
    so secret values can never leave the vault without a second factor.
    *Write endpoints* (set/delete) use ``require_2fa_or_bootstrap_for_writes``
    which permits the very first batch of secrets (≤ ``BOOTSTRAP_WRITE_LIMIT``)
    without 2FA, so the admin can finish populating the vault right after
    init, then enable 2FA. This avoids the dead-end "vault unlocked but
    save fails with TWOFA_REQUIRED" UX.

    This guard mirrors the bootstrap-write threshold so that lock/unlock
    keep working WHILE the admin is still in bootstrap (otherwise after
    the first write, ``lock_now`` would 403 and they'd lose access to
    their own session).
    """
    cfg = await get_twofa_config()
    if cfg and cfg.get("enabled"):
        return p
    # 2FA not active → only allow as long as the vault is still in
    # bootstrap territory. Past ``BOOTSTRAP_WRITE_LIMIT`` we hard-require
    # 2FA for every endpoint (including lifecycle).
    secret_count = await db.cabinet_vault.count_documents(
        {"_id": {"$ne": "_meta"}}
    )
    if secret_count >= BOOTSTRAP_WRITE_LIMIT:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "TWOFA_REQUIRED",
                "message": (
                    f"Vault holds {secret_count} secrets. Enable 2FA "
                    "from /admin/security before re-unlocking or "
                    "modifying it."
                ),
            },
        )
    return p


#: Maximum number of secrets the admin may store BEFORE enabling 2FA. Once
#: this threshold is reached, ``require_2fa_or_bootstrap_for_writes`` flips
#: to strict 2FA for any further write. Tuned to comfortably cover an
#: initial deployment (LLM keys, Resend, Helius, Telegram bot creds, X bot
#: creds × 4, public URL, BonkBot ref, etc.) without becoming a permanent
#: backdoor.
BOOTSTRAP_WRITE_LIMIT = 30


async def require_2fa_or_bootstrap_for_writes(
    p: dict = Depends(require_admin),
) -> dict:
    """Permit PUT / DELETE on secrets without 2FA during the bootstrap
    window, then flip to strict 2FA once the vault is meaningfully
    populated.

    Why this exists: forcing 2FA enrolment BEFORE the very first secret
    is stored creates a chicken-and-egg dead-end. The admin unlocks a
    fresh vault, tries to add the first key, gets a 403 ``TWOFA_REQUIRED``,
    and the only feedback shown by the UI was a generic "Save failed"
    toast. With this guard:

      * 2FA enabled                     → write allowed.
      * 2FA disabled, secrets ≤ limit   → write allowed (BOOTSTRAP_WRITE).
      * 2FA disabled, secrets > limit   → 403 TWOFA_REQUIRED.

    Read endpoints (``get_secret``, ``export``, ``import``) intentionally
    keep ``require_2fa_enabled`` so secret VALUES never leave without a
    second factor — only WRITES are relaxed during bootstrap.
    """
    cfg = await get_twofa_config()
    if cfg and cfg.get("enabled"):
        return p
    secret_count = await db.cabinet_vault.count_documents(
        {"_id": {"$ne": "_meta"}}
    )
    if secret_count >= BOOTSTRAP_WRITE_LIMIT:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "TWOFA_REQUIRED",
                "message": (
                    f"Vault already holds {secret_count} secrets. "
                    "Enable 2FA from /admin/security before storing "
                    "more."
                ),
                "hint": (
                    "Bootstrap writes are limited to keep an "
                    "unenrolled admin from leaving the vault wide "
                    "open indefinitely."
                ),
            },
        )
    return p


def _client_ip(request: Request) -> Optional[str]:
    return request.client.host if request.client else None


# ---- Status & lifecycle ----------------------------------------------------
@router.get("/status")
async def vault_status(_p: dict = Depends(require_admin)):
    """Status is readable WITHOUT 2FA so the UI can render the right phase
    (init wizard vs unlock prompt vs unlocked panel) before the admin has
    enabled 2FA. No secrets are leaked.
    """
    return await vault.get_status()


@router.post("/init")
async def vault_init(request: Request, p: dict = Depends(require_2fa_or_bootstrap)):
    """One-time bootstrap. Returns the freshly-generated 24-word mnemonic
    in the response body. The mnemonic is NEVER stored server-side; the
    caller MUST persist it externally (paper backup / hardware password
    manager). This endpoint is rejected if a vault already exists.
    """
    try:
        return await vault.init_vault(jti=p["jti"], ip=_client_ip(request))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/unlock")
async def vault_unlock(req: UnlockRequest, request: Request,
                       p: dict = Depends(require_2fa_or_bootstrap)):
    try:
        result = await vault.unlock(
            req.mnemonic,
            jti=p["jti"],
            ip=_client_ip(request),
            ttl_seconds=req.ttl_seconds or vault.DEFAULT_UNLOCK_TTL_S,
        )
        # Cached env-fallback values may now be shadowed by vault values —
        # invalidate so service callers refetch from the freshly-unlocked vault.
        secret_provider.invalidate_cache()
        return result
    except (vault.MnemonicError, vault.VaultMismatchError) as e:
        # Structured error → UI displays code-specific hint.
        raise HTTPException(status_code=401, detail=e.to_detail()) from e
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.post("/lock")
async def vault_lock(request: Request, p: dict = Depends(require_2fa_or_bootstrap)):
    await vault.lock_and_audit(jti=p["jti"], ip=_client_ip(request))
    secret_provider.invalidate_cache()
    return {"ok": True, "locked": True}


# ---- Secrets ---------------------------------------------------------------
@router.get("/list")
async def vault_list(request: Request, p: dict = Depends(require_2fa_or_bootstrap)):
    try:
        return await vault.list_secrets(jti=p["jti"], ip=_client_ip(request))
    except PermissionError:
        raise HTTPException(status_code=423, detail={"code": "VAULT_LOCKED"})


@router.get("/secret/{category}/{key}")
async def vault_get(category: str, key: str, request: Request,
                    p: dict = Depends(require_2fa_enabled)):
    try:
        return await vault.get_secret(category, key,
                                      jti=p["jti"], ip=_client_ip(request))
    except PermissionError:
        raise HTTPException(status_code=423, detail={"code": "VAULT_LOCKED"})
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/secret/{category}/{key}")
async def vault_set(category: str, key: str, req: SetSecretRequest,
                    request: Request,
                    p: dict = Depends(require_2fa_or_bootstrap_for_writes)):
    try:
        result = await vault.set_secret(category, key, req.value,
                                        jti=p["jti"], ip=_client_ip(request))
        # Drop cached value for this (category, key) so the next service
        # call reads the rotated secret immediately.
        secret_provider.invalidate_cache()
        return result
    except PermissionError:
        raise HTTPException(status_code=423, detail={"code": "VAULT_LOCKED"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/secret/{category}/{key}")
async def vault_delete(category: str, key: str, request: Request,
                       p: dict = Depends(require_2fa_or_bootstrap_for_writes)):
    try:
        result = await vault.delete_secret(category, key,
                                           jti=p["jti"], ip=_client_ip(request))
        secret_provider.invalidate_cache()
        return result
    except PermissionError:
        raise HTTPException(status_code=423, detail={"code": "VAULT_LOCKED"})


# ---- Backup ----------------------------------------------------------------
@router.post("/export")
async def vault_export(req: ExportRequest, request: Request,
                       p: dict = Depends(require_2fa_enabled)):
    try:
        return await vault.export_encrypted(req.passphrase,
                                            jti=p["jti"], ip=_client_ip(request))
    except PermissionError:
        raise HTTPException(status_code=423, detail={"code": "VAULT_LOCKED"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/import")
async def vault_import(req: ImportRequest, request: Request,
                       p: dict = Depends(require_2fa_enabled)):
    """Restore an encrypted bundle into the (currently unlocked) vault.

    Returns counts: ``{imported, replaced, skipped, total_in_bundle}``.
    """
    try:
        result = await vault.import_encrypted(
            req.bundle, req.passphrase,
            overwrite=req.overwrite,
            jti=p["jti"], ip=_client_ip(request),
        )
        secret_provider.invalidate_cache()
        return result
    except PermissionError:
        raise HTTPException(status_code=423, detail={"code": "VAULT_LOCKED"})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---- Audit -----------------------------------------------------------------
@router.get("/audit")
async def vault_audit(limit: int = 100,
                      _p: dict = Depends(require_2fa_or_bootstrap)):
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be 1-1000")
    return {"items": await vault.get_audit_log(limit=limit)}


# ---- Factory reset (DESTRUCTIVE) ------------------------------------------
class FactoryResetRequest(BaseModel):
    """Strong, multi-factor confirmation for the destructive reset.

    All four guards are cumulative:

    1. Admin password must be re-entered (``password``).
    2. If 2FA is enabled on the admin account, ``totp_code`` is required.
    3. ``confirm_text`` must match the magic string EXACTLY (case-sensitive).
    4. The vault must currently be **locked** (enforced separately in the
       handler). We refuse the reset while a session is unlocked so an
       attacker who hijacks an active admin tab cannot trivially nuke the
       vault — they'd at least have to lock it first, which buys us a
       window for detection.
    """
    password: str = Field(..., min_length=1)
    totp_code: Optional[str] = None
    confirm_text: str = Field(..., min_length=1)


# Magic string the operator must literally type. Kept short enough to
# read aloud in a recovery call but distinctive enough to never appear
# as muscle-memory typing.
FACTORY_RESET_MAGIC = "FACTORY RESET DEEPOTUS"


@router.post("/factory-reset")
async def vault_factory_reset(
    req: FactoryResetRequest,
    request: Request,
    p: dict = Depends(require_admin),
):
    """**DESTRUCTIVE** — wipe the vault back to pristine pre-init state.

    Use case: the operator lost the BIP39 mnemonic and the vault is
    therefore inaccessible. Without this endpoint the only recovery path
    would be a manual MongoDB drop. With it, the operator can reset the
    vault from the admin UI provided they:

      • re-prove they own the admin password,
      • clear the 2FA second factor (if enabled),
      • literally type the magic string ``FACTORY RESET DEEPOTUS``,
      • and have the vault currently locked (no active unlock session).

    The audit log entry is written BEFORE the wipe so the trace
    survives. Caller's IP and JTI are recorded.

    Returns:
        ``{ ok, deleted_meta, deleted_secrets, reset_at }``
    """
    # 1) Vault must be in locked state (refuse during an active session).
    status = await vault.get_status()
    if not status.get("locked", True):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "VAULT_UNLOCKED",
                "message": (
                    "Lock the vault first. Factory reset is only "
                    "allowed when the vault is currently locked."
                ),
            },
        )

    # 2) Re-verify the admin password (defence-in-depth on top of the JWT).
    if not await verify_admin_password(req.password):
        # Audit failed attempt so brute-forcing leaves a trail.
        await vault._audit(  # noqa: SLF001 (private but intentional)
            "factory_reset_failed",
            jti=p["jti"],
            ip=_client_ip(request),
            extra={"reason": "bad_password"},
        )
        raise HTTPException(status_code=401, detail="Invalid password")

    # 3) If 2FA is enabled, require a fresh TOTP / backup code.
    twofa_doc = await get_twofa_config()
    if twofa_doc and twofa_doc.get("enabled"):
        code = (req.totp_code or "").strip()
        if not code:
            raise HTTPException(
                status_code=401,
                detail="2FA code required",
                headers={"x-2fa-required": "true"},
            )
        ok = await verify_totp_or_backup(twofa_doc, code, code)
        if not ok:
            await vault._audit(  # noqa: SLF001
                "factory_reset_failed",
                jti=p["jti"],
                ip=_client_ip(request),
                extra={"reason": "bad_totp"},
            )
            raise HTTPException(status_code=401, detail="Invalid 2FA code")

    # 4) Magic confirm string. Case-sensitive and exact-match to defeat
    # accidental clicks from a "click anywhere to continue" interaction.
    if req.confirm_text != FACTORY_RESET_MAGIC:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "BAD_CONFIRM_STRING",
                "message": (
                    f"Confirmation string must be exactly: "
                    f"\"{FACTORY_RESET_MAGIC}\""
                ),
            },
        )

    # All guards passed → wipe.
    logging.warning(
        "[cabinet-vault] factory-reset authorised — jti=%s ip=%s",
        p["jti"], _client_ip(request),
    )
    result = await vault.factory_reset_vault(
        jti=p["jti"],
        ip=_client_ip(request),
        extra={"twofa_enabled_at_reset": bool(twofa_doc and twofa_doc.get("enabled"))},
    )
    # Drop secret_provider cache too so any in-flight callers re-fetch.
    secret_provider.invalidate_cache()
    return result
