"""Regression test — Sprint LAUNCH (pre-mint day audit).

Pins the FastAPI route ordering for ``/api/admin/wallet-registry/*``
endpoints. A previous bug had the generic ``PUT /{slot}`` route
declared before the literal ``PUT /mint-address`` route, which made
FastAPI match the literal path against the slot regex (``[a-z_]{2,32}``)
and fail with a 422 ``loc: ["path", "slot"]``. Symptom in prod was:
the admin pasted a valid mint address, the form indicated "saved",
but ``/transparency`` stayed mint-less because the call never reached
``set_mint_address()``.

These tests inspect the registered routes on ``admin_router`` and
assert the literal route is declared first. If a future contributor
moves the literal route below the wildcard, this test fails loudly.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from routers import wallet_registry as wr_router  # noqa: E402


def _route_paths(router):  # type: ignore[no-untyped-def]
    """Extract route paths in declaration order. We only care about
    routes mounted directly on this APIRouter — sub-mounts (none here)
    would need recursion."""
    return [r.path for r in router.routes]


def test_mint_address_routes_declared_before_slot_wildcard() -> None:
    """The two literal routes (PUT + DELETE /mint-address) MUST be
    declared BEFORE the generic PUT /{slot} on the admin router."""
    paths = _route_paths(wr_router.admin_router)
    mint_path = "/api/admin/wallet-registry/mint-address"
    slot_path = "/api/admin/wallet-registry/{slot}"

    put_mint_idx = paths.index(mint_path)
    slot_idx = paths.index(slot_path)

    assert put_mint_idx < slot_idx, (
        f"PUT {mint_path} ({put_mint_idx}) must precede PUT {slot_path} ({slot_idx}). "
        f"Declared paths: {paths}"
    )


def test_admin_router_exposes_mint_endpoints() -> None:
    """Smoke check — ensures the literal endpoints actually exist.
    Catches silent removal during refactors."""
    paths = _route_paths(wr_router.admin_router)
    assert "/api/admin/wallet-registry/mint-address" in paths
    assert "/api/admin/wallet-registry/{slot}" in paths
    assert "/api/admin/wallet-registry" in paths  # GET listing endpoint


def test_mint_address_payload_accepts_solana_base58() -> None:
    """Pydantic schema check — the payload must accept a 32-44 char
    base58 string (Solana mint format) without complaining. This was
    NOT the cause of the production bug but it's a useful trip-wire
    if someone tightens the validation too far."""
    from routers.wallet_registry import MintAddressPayload
    # USDC mainnet — exactly 44 base58 chars.
    real_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    payload = MintAddressPayload(address=real_mint)
    assert payload.address == real_mint
