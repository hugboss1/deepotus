"""Founder-side endpoints (Sprint 16).

Two surfaces:

  * ``POST /api/admin/founder/disclose-buy`` — admin trigger that pushes
    a transparency tweet/telegram post about a personal founder buy of
    $DEEPOTUS through the existing Propaganda Engine. Per the Tokenomics
    & Treasury Policy §6 the Cabinet pre-commits to publishing every
    founder buy within 30 minutes — this is the technical implementation
    of that promise.

  * ``GET /api/access-terminals`` — public, anonymous endpoint that
    returns the affiliate referral URLs (BonkBot / Trojan) the landing
    uses for its "Access Secured Terminals" panel. Living source of
    truth so the affiliate links can be rotated by the admin without
    a frontend redeploy.

Auth:
  * ``disclose-buy`` requires admin JWT (no 2FA — the message goes
    through the propaganda *approval* queue which itself enforces 2FA on
    final dispatch).
  * ``access-terminals`` is fully public.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core import propaganda_engine
from core.security import require_admin
from core.secret_provider import (
    get_bonkbot_ref_url,
    get_trojan_ref_url,
)

public_router = APIRouter(prefix="/api", tags=["founder"])
admin_router = APIRouter(prefix="/api/admin/founder", tags=["founder-admin"])


# =====================================================================
# Public — Access Secured Terminals (Sprint 16.3)
# =====================================================================
@public_router.get("/access-terminals")
async def get_access_terminals() -> Dict[str, Any]:
    """Return the affiliate URLs used by the landing page.

    Empty values are filtered out so the frontend doesn't render a
    broken button when a referral hasn't been provisioned yet (Trojan
    is intentionally optional at first deploy).

    The response shape is intentionally tiny so the landing can fetch
    it once at mount and cache aggressively.
    """
    bonkbot = await get_bonkbot_ref_url()
    trojan = await get_trojan_ref_url()
    items = []
    if bonkbot:
        items.append(
            {
                "id": "bonkbot",
                "label": "BonkBot",
                "url": bonkbot,
                "tagline": "Telegram-native sniper. Standard issue at the Cabinet.",
                "platform": "telegram",
            }
        )
    if trojan:
        items.append(
            {
                "id": "trojan",
                "label": "Trojan",
                "url": trojan,
                "tagline": "Multi-DEX router. Cabinet-approved.",
                "platform": "telegram",
            }
        )
    return {"items": items, "count": len(items)}


# =====================================================================
# Admin — Founder Buy Disclosure (Sprint 16.2)
# =====================================================================
class DiscloseBuyPayload(BaseModel):
    amount_sol: float = Field(..., ge=0.001, le=10000.0)
    wallet: str = Field(..., min_length=4, max_length=64)
    mc_usd: float = Field(default=0.0, ge=0.0, le=1_000_000_000_000.0)
    tx_signature: Optional[str] = Field(default=None, max_length=128)
    note: Optional[str] = Field(default=None, max_length=80)
    language: Optional[str] = Field(default=None, pattern="^(en|fr)$")


@admin_router.post("/disclose-buy")
async def disclose_buy(
    payload: DiscloseBuyPayload,
    request: Request,
    admin=Depends(require_admin),
) -> Dict[str, Any]:
    """Generate a Cabinet-style disclosure post via the Propaganda
    Engine.

    The post lands in the propaganda *approval* queue (status
    ``proposed``) — the founder still has to approve+dispatch through
    the standard 2FA-protected flow before it actually publishes to X
    and Telegram. That two-step ensures a typo in the wallet pubkey or
    tx_signature never goes live unintentionally.

    Returns the generated queue item so the admin UI can surface a
    "review now" CTA.
    """
    res = await propaganda_engine.fire(
        trigger_key="founder_buy",
        manual=True,
        payload_override={
            "founder_amount_sol": float(payload.amount_sol),
            "founder_wallet": payload.wallet.strip(),
            "founder_mc_usd": float(payload.mc_usd or 0),
            "tx_signature": (payload.tx_signature or "").strip(),
            "founder_note": (payload.note or "").strip(),
        },
        locale_override=payload.language,
        jti=getattr(admin, "jti", None) if hasattr(admin, "jti") else None,
        ip=(request.client.host if request and request.client else None),
    )

    if not res or not res.get("ok"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "propaganda_fire_failed",
                "reason": (res or {}).get("reason") or "unknown",
            },
        )

    item = res.get("queue_item") or {}
    return {
        "ok": True,
        "queue_item_id": item.get("id"),
        "rendered": (item.get("rendered_content") or "")[:500],
        "language": item.get("language"),
        "platforms": item.get("platforms", []),
        "status": item.get("status"),
        "review_url": "/admin/propaganda?tab=queue",
        "llm_used": bool(res.get("llm_used")),
    }
