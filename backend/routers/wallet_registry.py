"""Wallet Registry HTTP surface — Sprint Transparency & Trust.

Public:
    GET  /api/transparency/wallets                       - Public snapshot

Admin (JWT-only, no 2FA — this is metadata, not money):
    GET   /api/admin/wallet-registry                     - Read all 5 slots
    PUT   /api/admin/wallet-registry/{slot}              - Upsert one slot
    PUT   /api/admin/wallet-registry/mint-address        - Set the mint address
    DELETE /api/admin/wallet-registry/mint-address       - Clear the mint address

Why JWT-only and not 2FA-gated?
  These endpoints write **public metadata only** — pubkeys, lock URLs,
  the mint address. Nothing about them attracts buyers (they're
  already on-chain). 2FA is reserved for actions that move money or
  publish to social platforms (Cabinet Vault writes, propaganda
  approvals). Adding a second factor here would just slow down the
  pre-mint frenzy without measurable security benefit — every value
  written here is independently verifiable on-chain by anyone.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from core import wallet_registry
from core.security import require_admin

# Public router — no auth, mounted under /api
public_router = APIRouter(
    prefix="/api/transparency",
    tags=["transparency-public"],
)

# Admin router — JWT required
admin_router = APIRouter(
    prefix="/api/admin/wallet-registry",
    tags=["wallet-registry-admin"],
)


# ---------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------
class WalletPatch(BaseModel):
    """Partial update for one slot. Every field is optional; ``None``
    leaves the existing value in place, ``""`` clears it."""

    address: Optional[str] = Field(default=None, max_length=64)
    lock_url: Optional[str] = Field(default=None, max_length=300)
    label: Optional[str] = Field(default=None, max_length=80)


class MintAddressPayload(BaseModel):
    address: str = Field(..., max_length=64)


# ---------------------------------------------------------------------
# Public — what the /transparency page consumes
# ---------------------------------------------------------------------
@public_router.get("/wallets")
async def public_wallets() -> Dict[str, Any]:
    """Public registry snapshot.

    Returns the 5 wallets in canonical order + the mint address +
    pre-derived RugCheck URL. Always returns a fully-populated shape
    even on a fresh DB (empty strings for unset slots) so the
    front-end can render a stable layout without null checks.
    """
    return await wallet_registry.public_snapshot()


# ---------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------
@admin_router.get("")
async def admin_list(_admin: Dict[str, Any] = Depends(require_admin)) -> Dict[str, Any]:
    wallets = await wallet_registry.get_all_wallets()
    mint = await wallet_registry.get_mint_address()
    return {
        "wallets": wallets,
        "mint_address": mint,
        "rugcheck_url": f"https://rugcheck.xyz/tokens/{mint}" if mint else "",
    }


@admin_router.put("/{slot}")
async def admin_upsert(
    payload: WalletPatch,
    slot: str = Path(..., pattern=r"^[a-z_]{2,32}$"),
    admin: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    if slot not in wallet_registry.WALLET_SLOTS:
        raise HTTPException(
            status_code=400,
            detail=f"unknown slot {slot!r} — expected one of {wallet_registry.WALLET_SLOTS}",
        )
    try:
        result = await wallet_registry.upsert_wallet(
            slot,
            address=payload.address,
            lock_url=payload.lock_url,
            label=payload.label,
            actor_jti=str(admin.get("jti") or ""),
        )
    except ValueError as exc:
        # Surface validation errors as 422 so the admin UI can
        # display them inline next to the offending field.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "wallet": result}


@admin_router.put("/mint-address")
async def admin_set_mint(
    payload: MintAddressPayload,
    admin: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    try:
        addr = await wallet_registry.set_mint_address(
            payload.address,
            actor_jti=str(admin.get("jti") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "ok": True,
        "mint_address": addr,
        "rugcheck_url": f"https://rugcheck.xyz/tokens/{addr}" if addr else "",
    }


@admin_router.delete("/mint-address")
async def admin_clear_mint(
    admin: Dict[str, Any] = Depends(require_admin),
) -> Dict[str, Any]:
    """Clear the mint address — used to revert if the wrong value was
    pasted before launch. Once the real mint is live this should
    never be called; we keep it for symmetry + recovery."""
    addr = await wallet_registry.set_mint_address(
        "",
        actor_jti=str(admin.get("jti") or ""),
    )
    return {"ok": True, "mint_address": addr}
