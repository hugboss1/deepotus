"""Ecosystem-facing router (Sprint 20).

Public, unauthenticated endpoints used by the new ``/ecosysteme`` page:

  * ``POST /api/ecosystem/genesis``
      Subscribe to the Genesis list (waiting-list for the secret
      project + Roman / Mobile game waitlists).

  * ``GET  /api/ecosystem/board-game/counter``
      Returns the live founder counter snapshot + current price tier.

  * ``POST /api/ecosystem/b2b-inquiry``
      White-label inquiry intake (Video Generator royaltie 25%).

Admin router lives in ``routers/admin_orders.py`` to keep concerns
separated.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from core import b2b_inquiries, genesis, stripe_checkout

router = APIRouter(prefix="/api/ecosystem", tags=["ecosystem"])


# ---------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------
class GenesisPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    source: str = Field(default="genesis_generic", max_length=40)
    locale: str = Field(default="fr", pattern=r"^(fr|en)$")


class GenesisAck(BaseModel):
    ok: bool = True
    source: str


class BoardgameCounter(BaseModel):
    sold: int
    next_number: int
    founder_limit: int
    is_founder: bool
    current_price_eur: float
    current_tier: str


class B2BPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    company: Optional[str] = Field(default=None, max_length=160)
    message: str = Field(..., min_length=10, max_length=4000)
    locale: str = Field(default="fr", pattern=r"^(fr|en)$")


class B2BAck(BaseModel):
    ok: bool = True
    inquiry_id: str


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
def _hash_ip(req: Request) -> Optional[str]:
    """Cheap IP hash for soft de-dup / abuse detection. Best-effort."""
    ip = req.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        req.client.host if req.client else ""
    )
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:24]


@router.post("/genesis", response_model=GenesisAck)
async def genesis_subscribe(payload: GenesisPayload, request: Request) -> GenesisAck:
    ip_hash = _hash_ip(request)
    doc = await genesis.subscribe(
        email=payload.email,
        source=payload.source,
        locale=payload.locale,
        ip_hash=ip_hash,
    )
    return GenesisAck(ok=True, source=doc["source"])


@router.get("/board-game/counter", response_model=BoardgameCounter)
async def boardgame_counter() -> BoardgameCounter:
    snap = await stripe_checkout.get_boardgame_counter_snapshot()
    return BoardgameCounter(**snap)


@router.post("/b2b-inquiry", response_model=B2BAck)
async def b2b_inquiry(payload: B2BPayload) -> B2BAck:
    doc = await b2b_inquiries.create_inquiry(
        name=payload.name,
        email=payload.email,
        company=payload.company,
        message=payload.message,
        locale=payload.locale,
    )
    return B2BAck(ok=True, inquiry_id=doc["_id"])


__all__ = ["router"]
