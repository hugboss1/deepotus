"""PROTOCOL ΔΣ vault endpoints.

Two routers cohabit in this module:
    - `router` (prefix `/api/vault`) public vault state + report-purchase
    - `admin_router` (prefix `/api/admin/vault`) admin cracks + config

Domain logic (state, events, dexscreener polling) lives in the top-level
`vault` and `dexscreener` modules.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

import vault as vault_mod
from core.config import db
from core.models import VaultCrackPublicRequest
from core.security import require_admin

router = APIRouter(prefix="/api/vault", tags=["vault"])
admin_router = APIRouter(prefix="/api/admin/vault", tags=["vault-admin"])


# ---------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------
@router.get("/state", response_model=vault_mod.VaultStateResponse)
async def vault_state_public():
    """Public snapshot of the classified vault. Never reveals the target combination."""
    return await vault_mod.get_public_state(db)


@router.post("/report-purchase", response_model=vault_mod.VaultStateResponse)
async def vault_report_purchase(req: VaultCrackPublicRequest, request: Request):
    """Best-effort public endpoint for wallet integrations. Clamped and rate-implied.
    For now it is primarily used by the demo UI. Real Solana indexing will replace it.
    """
    clamped = min(int(req.tokens), 50_000)
    agent = (req.agent_code or "").strip() or None
    if agent and not agent.startswith("GUEST-"):
        agent = f"GUEST-{agent[:16]}"
    _ev, state = await vault_mod.apply_crack(
        db,
        tokens=clamped,
        kind="purchase",
        agent_code=agent,
        note=f"reported by client ({request.client.host if request.client else 'unknown'})",
    )
    return state


# ---------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------
@admin_router.get("/state", response_model=vault_mod.VaultAdminStateResponse)
async def vault_state_admin(_p: dict = Depends(require_admin)):
    return await vault_mod.get_admin_state(db)


@admin_router.post("/crack", response_model=vault_mod.VaultAdminStateResponse)
async def vault_crack_admin(
    req: vault_mod.VaultCrackRequest, _p: dict = Depends(require_admin)
):
    await vault_mod.apply_crack(
        db,
        tokens=int(req.tokens),
        kind="admin_crack",
        agent_code=(req.agent_code or "ADMIN-0001"),
        note=req.note or "manual admin crack",
    )
    return await vault_mod.get_admin_state(db)


@admin_router.post("/config", response_model=vault_mod.VaultAdminStateResponse)
async def vault_config_admin(
    req: vault_mod.VaultConfigUpdate, _p: dict = Depends(require_admin)
):
    return await vault_mod.update_config(db, req)


@admin_router.post("/dex-config", response_model=vault_mod.VaultAdminStateResponse)
async def vault_dex_config_admin(
    req: vault_mod.VaultDexConfigUpdate, _p: dict = Depends(require_admin)
):
    return await vault_mod.update_dex_config(db, req)


@admin_router.post("/dex-poll", response_model=dict)
async def vault_dex_poll_now_admin(_p: dict = Depends(require_admin)):
    """Force a single DexScreener poll immediately (for testing/debugging)."""
    import dexscreener as dex_mod

    result = await dex_mod.dex_poll_once(db, vault_mod)
    return result
