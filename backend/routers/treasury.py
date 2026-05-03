"""Treasury operations router (Sprint 15 scaffold).

Public ``GET /api/treasury/operations`` + ``GET /api/treasury/burns``
power the Transparency page on the landing site. The admin counterpart
``POST /api/admin/treasury/operations`` lets the operator log on-chain
operations (buybacks, distributions, burns, locks) by hand — until the
chain-side ingestion (Phase 15.B) parses them automatically from
Helius webhooks.

Mongo collection: ``treasury_operations``
-----------------------------------------
::

    {
        "_id": "<uuid4>",
        "type": "BUYBACK | DISTRIBUTION | BURN | LOCK",
        "amount_sol": float | None,
        "amount_tokens": int | None,
        "signature": "<solana tx signature>",
        "description": "<free-form, max 280 chars>",
        "wallet_from": "<solana base58>",
        "wallet_to": "<solana base58 | None>",
        "logged_at": "<ISO 8601 UTC>",
        "logged_by_jti": "<admin session id>",
    }

Why a free-text ``description`` field?
    Treasury ops are operator-driven for now. We want to surface the
    "why" of each operation (e.g. "monthly community distribution to
    top 50 holders") on the public page without inventing a rigid
    taxonomy that we'd have to evolve every time a new policy lands.
    Server-side validation caps the length so it never becomes a
    long-form paragraph.
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from core.config import db
from core.security import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["treasury"])
admin_router = APIRouter(prefix="/api/admin/treasury", tags=["treasury-admin"])

#: Tx signatures on Solana are base58, 87–88 chars; we accept 60+ as
#: the sweet spot (some wallets pad differently). Defensive only —
#: we don't *verify* the sig is valid on-chain here.
_SIG_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{60,90}$")
#: Solana wallet addresses — same alphabet, 32-44 chars.
_WALLET_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")

OperationType = Literal["BUYBACK", "DISTRIBUTION", "BURN", "LOCK"]


class TreasuryOp(BaseModel):
    """Body for ``POST /admin/treasury/operations``.

    At least ONE of ``amount_sol`` / ``amount_tokens`` must be set;
    we don't enforce both because BURN events are tokens-only and
    BUYBACK/LOCK events may be SOL-only at log time (token side
    settled separately).
    """

    type: OperationType
    amount_sol: Optional[float] = Field(default=None, ge=0)
    amount_tokens: Optional[int] = Field(default=None, ge=0)
    signature: str = Field(..., min_length=60, max_length=120)
    description: str = Field(..., min_length=4, max_length=280)
    wallet_from: str = Field(..., min_length=32, max_length=44)
    wallet_to: Optional[str] = Field(default=None, min_length=32, max_length=44)

    @field_validator("signature")
    @classmethod
    def _sig_shape(cls, v: str) -> str:
        if not _SIG_RE.match(v):
            raise ValueError("signature must be a base58 Solana tx signature")
        return v

    @field_validator("wallet_from", "wallet_to")
    @classmethod
    def _wallet_shape(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not _WALLET_RE.match(v):
            raise ValueError("wallet must be a base58 Solana address")
        return v


def _serialise(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Drop Mongo-specific keys + normalise field names for JSON."""
    return {
        "id": doc.get("_id"),
        "type": doc.get("type"),
        "amount_sol": doc.get("amount_sol"),
        "amount_tokens": doc.get("amount_tokens"),
        "signature": doc.get("signature"),
        "description": doc.get("description"),
        "wallet_from": doc.get("wallet_from"),
        "wallet_to": doc.get("wallet_to"),
        "logged_at": doc.get("logged_at"),
    }


# ---------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------
@router.get("/treasury/operations")
async def list_treasury_operations(
    limit: int = Query(default=50, ge=1, le=500),
    type: Optional[OperationType] = Query(
        default=None,
        description="Filter by op type (BUYBACK | DISTRIBUTION | BURN | LOCK).",
    ),
) -> Dict[str, Any]:
    """Public list of recent treasury operations.

    Sorted newest-first. ``logged_by_jti`` is intentionally NOT exposed
    — it's an internal audit field. Tx signatures + amounts are public
    on-chain anyway, so surfacing them here is fine and is the point
    of the Transparency page.
    """
    query: Dict[str, Any] = {}
    if type:
        query["type"] = type
    cursor = db.treasury_operations.find(query).sort("logged_at", -1).limit(limit)
    items = [_serialise(doc) async for doc in cursor]
    return {"items": items, "count": len(items)}


@router.get("/treasury/burns")
async def burn_summary() -> Dict[str, Any]:
    """Aggregated burn counter — total tokens destroyed, last burn date,
    burn count. Used by the homepage burn widget. Returns zeroes when
    no burn has been logged yet so the UI can render a "first burn at
    J+30" placeholder."""
    cursor = db.treasury_operations.find({"type": "BURN"}).sort("logged_at", -1)
    burns: List[Dict[str, Any]] = [_serialise(doc) async for doc in cursor]
    total_tokens = sum((b.get("amount_tokens") or 0) for b in burns)
    last = burns[0] if burns else None
    return {
        "total_burned_tokens": total_tokens,
        "burn_count": len(burns),
        "last_burn_at": (last or {}).get("logged_at"),
        "last_burn_signature": (last or {}).get("signature"),
        "last_burn_description": (last or {}).get("description"),
    }


# ---------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------
@admin_router.get("/operations")
async def admin_list_operations(
    limit: int = Query(default=200, ge=1, le=1000),
    p: dict = Depends(require_admin),  # noqa: ARG001 — admin gate
) -> Dict[str, Any]:
    cursor = db.treasury_operations.find({}).sort("logged_at", -1).limit(limit)
    items = []
    async for doc in cursor:
        out = _serialise(doc)
        out["logged_by_jti"] = doc.get("logged_by_jti")  # admin sees the audit
        items.append(out)
    return {"items": items, "count": len(items)}


@admin_router.post("/operations")
async def admin_log_operation(
    op: TreasuryOp,
    p: dict = Depends(require_admin),
) -> Dict[str, Any]:
    """Log a new treasury operation. Idempotency is provided by the
    on-chain signature: we refuse to insert a row whose signature
    already exists — operators sometimes click twice."""
    existing = await db.treasury_operations.find_one(
        {"signature": op.signature},
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "DUPLICATE_SIGNATURE",
                "message": "Operation with this signature is already logged.",
                "existing_id": existing.get("_id"),
            },
        )
    if op.amount_sol is None and op.amount_tokens is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "AMOUNT_REQUIRED",
                "message": "Provide at least amount_sol or amount_tokens.",
            },
        )

    doc = {
        "_id": str(uuid.uuid4()),
        "type": op.type,
        "amount_sol": op.amount_sol,
        "amount_tokens": op.amount_tokens,
        "signature": op.signature,
        "description": op.description,
        "wallet_from": op.wallet_from,
        "wallet_to": op.wallet_to,
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "logged_by_jti": p.get("jti"),
    }
    await db.treasury_operations.insert_one(doc)
    logger.info(
        "[treasury] %s logged sig=%s tokens=%s sol=%s by jti=%s",
        op.type, op.signature[:12], op.amount_tokens, op.amount_sol,
        p.get("jti"),
    )
    return {"ok": True, "id": doc["_id"], "operation": _serialise(doc)}


@admin_router.delete("/operations/{op_id}")
async def admin_delete_operation(
    op_id: str,
    p: dict = Depends(require_admin),
) -> Dict[str, Any]:
    """Soft-delete by hard-removal. Treasury ops can be removed if the
    operator made a typo and re-logged the same on-chain event with
    correct metadata; the on-chain signature is the source of truth."""
    res = await db.treasury_operations.delete_one({"_id": op_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="not found")
    logger.info("[treasury] operation %s deleted by jti=%s", op_id, p.get("jti"))
    return {"ok": True, "deleted_id": op_id}


# Re-exports so server.py can do ``from routers import treasury``
__all__ = ["router", "admin_router"]
