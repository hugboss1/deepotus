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
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core import cabinet_vault as vault
from core import secret_provider
from core.config import db
from core.security import get_twofa_config, require_admin

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
    phrase and unlocking the vault — without being stuck on a chicken-and-egg
    403. Once 2FA is active, the regular guard kicks in everywhere.

    *CRUD endpoints* (set/get/delete/export/import) keep ``require_2fa_enabled``
    so the second factor is strictly required before any secret is read or
    persisted. We further refuse this loose mode if the vault already
    contains real secrets: an existing vault must be protected by 2FA before
    we let anyone re-unlock it via this endpoint.
    """
    cfg = await get_twofa_config()
    if cfg and cfg.get("enabled"):
        return p
    # 2FA not active → only allow when vault is in a fresh / bootstrap state.
    # We tolerate the presence of `_meta` (initialised but no secrets) so the
    # admin can finish the setup → first unlock → then enable 2FA → then start
    # writing secrets.
    secret_count = await db.cabinet_vault.count_documents(
        {"_id": {"$ne": "_meta"}}
    )
    if secret_count > 0:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "TWOFA_REQUIRED",
                "message": (
                    "This vault already holds secrets. Enable 2FA "
                    "before re-unlocking it."
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
                    request: Request, p: dict = Depends(require_2fa_enabled)):
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
                       p: dict = Depends(require_2fa_enabled)):
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
