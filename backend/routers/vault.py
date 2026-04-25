"""PROTOCOL ΔΣ vault endpoints.

Two routers cohabit in this module:
    - `router` (prefix `/api/vault`) public vault state + report-purchase
    - `admin_router` (prefix `/api/admin/vault`) admin cracks + config

Domain logic (state, events, dexscreener polling, helius indexer) lives in
the top-level `vault`, `dexscreener`, and `helius` modules.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

import helius as helius_mod
import vault as vault_mod
from core.config import HELIUS_API_KEY, PUBLIC_BASE_URL, db
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



# ---------------------------------------------------------------------
# Helius admin endpoints (NEW — replaces DexScreener approximation)
# ---------------------------------------------------------------------
class HeliusConfigRequest(BaseModel):
    """Configure which Solana mint + pool the Helius indexer should track."""

    mint: Optional[str] = Field(None, max_length=64)
    pool_address: Optional[str] = Field(None, max_length=64)
    # Bearer value Helius will send back on every webhook. Rotate by calling
    # /helius-register again with a new value.
    webhook_auth: Optional[str] = Field(None, max_length=128)


class HeliusRegisterRequest(HeliusConfigRequest):
    register_webhook: bool = True


@admin_router.get("/helius-status", response_model=dict)
async def helius_status(_p: dict = Depends(require_admin)):
    """Return current Helius configuration and the list of active webhooks."""
    vs = await db.vault_state.find_one({"_id": "protocol_delta_sigma"}) or {}
    existing = await helius_mod.list_webhooks(HELIUS_API_KEY) if HELIUS_API_KEY else []
    return {
        "api_key_configured": bool(HELIUS_API_KEY),
        "mint": vs.get("dex_token_address"),
        "pool_address": vs.get("helius_pool_address"),
        "webhook_id": vs.get("helius_webhook_id"),
        "webhook_url": f"{PUBLIC_BASE_URL}/api/webhooks/helius",
        "helius_webhooks": existing,
        "dex_mode": vs.get("dex_mode"),
    }


@admin_router.post("/helius-config", response_model=dict)
async def helius_config(
    req: HeliusConfigRequest, _p: dict = Depends(require_admin)
):
    """Persist mint + pool_address + webhook_auth on vault_state."""
    update = {}
    if req.mint is not None:
        update["dex_token_address"] = req.mint.strip() or None
    if req.pool_address is not None:
        update["helius_pool_address"] = req.pool_address.strip() or None
    # Note: webhook_auth is stored in env var (HELIUS_WEBHOOK_AUTH), not DB,
    # because it's a secret. We just record that one was set.
    if req.webhook_auth is not None:
        update["helius_webhook_auth_set"] = bool(req.webhook_auth.strip())
    if not update:
        raise HTTPException(status_code=400, detail="Nothing to update")
    await db.vault_state.update_one(
        {"_id": "protocol_delta_sigma"}, {"$set": update}, upsert=True
    )
    return {"ok": True, "updated": list(update.keys())}


@admin_router.post("/helius-register", response_model=dict)
async def helius_register(
    req: HeliusRegisterRequest, _p: dict = Depends(require_admin)
):
    """Register our /api/webhooks/helius callback with Helius for the given mint.

    Must be called once after the admin has added HELIUS_API_KEY + set a
    HELIUS_WEBHOOK_AUTH env var. Persists the returned webhookID so we can
    delete/update it later.
    """
    if not HELIUS_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="HELIUS_API_KEY not configured. Add it to backend/.env first.",
        )
    mint = (req.mint or "").strip()
    if not mint:
        # fallback to stored config
        vs = await db.vault_state.find_one({"_id": "protocol_delta_sigma"}) or {}
        mint = (vs.get("dex_token_address") or "").strip()
    if not mint:
        raise HTTPException(status_code=400, detail="No mint provided or configured")

    # Import lazily to pick up any hot-reloaded env var
    from core.config import HELIUS_WEBHOOK_AUTH

    callback_url = f"{PUBLIC_BASE_URL}/api/webhooks/helius"
    try:
        res = await helius_mod.register_webhook(
            api_key=HELIUS_API_KEY,
            webhook_url=callback_url,
            mint=mint,
            auth_header=HELIUS_WEBHOOK_AUTH or None,
            transaction_types=["SWAP"],
            webhook_type="enhanced",
        )
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Helius registration failed: {str(e)[:300]}"
        )

    webhook_id = res.get("webhookID") or res.get("id")

    # Auto-enable demo mode when the tracked mint is our well-known demo token
    # (BONK). Real $DEEPOTUS launch → this flag stays False so the real
    # on-chain token amount drives the vault.
    from dexscreener import DEMO_TOKEN_ADDRESS

    demo_mode = mint == DEMO_TOKEN_ADDRESS

    await db.vault_state.update_one(
        {"_id": "protocol_delta_sigma"},
        {
            "$set": {
                "dex_token_address": mint,
                "helius_pool_address": (req.pool_address or "").strip() or None,
                "helius_webhook_id": webhook_id,
                "helius_demo_mode": demo_mode,
                "dex_mode": "helius",  # disable the dex approximation
            }
        },
        upsert=True,
    )
    return {
        "ok": True,
        "webhook_id": webhook_id,
        "callback_url": callback_url,
        "mint": mint,
        "demo_mode": demo_mode,
    }


@admin_router.post("/helius-catchup", response_model=dict)
async def helius_catchup(_p: dict = Depends(require_admin)):
    """Pull the last 50 SWAP txns from Helius and ingest any we haven't seen."""
    if not HELIUS_API_KEY:
        raise HTTPException(status_code=400, detail="HELIUS_API_KEY not configured")
    vs = await db.vault_state.find_one({"_id": "protocol_delta_sigma"}) or {}
    mint = (vs.get("dex_token_address") or "").strip()
    pool = (vs.get("helius_pool_address") or "").strip() or None
    demo_tokens_per_buy: Optional[int] = None
    if vs.get("helius_demo_mode"):
        demo_tokens_per_buy = int(vs.get("tokens_per_micro") or 10_000)
    if not mint:
        raise HTTPException(status_code=400, detail="No mint configured")
    return await helius_mod.catch_up_from_helius(
        db,
        vault_mod,
        HELIUS_API_KEY,
        mint,
        pool=pool,
        demo_tokens_per_buy=demo_tokens_per_buy,
    )


@admin_router.delete("/helius-webhook/{webhook_id}", response_model=dict)
async def helius_delete_webhook(
    webhook_id: str, _p: dict = Depends(require_admin)
):
    """Remove a previously-registered Helius webhook."""
    if not HELIUS_API_KEY:
        raise HTTPException(status_code=400, detail="HELIUS_API_KEY not configured")
    ok = await helius_mod.delete_webhook(HELIUS_API_KEY, webhook_id)
    if ok:
        await db.vault_state.update_one(
            {"_id": "protocol_delta_sigma"},
            {"$unset": {"helius_webhook_id": ""}},
        )
    return {"ok": ok}
