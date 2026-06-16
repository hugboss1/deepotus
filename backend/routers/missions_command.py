"""Mission config + participation routers (Sprint 21).

Three concerns, three routers, all mounted under a single import for
brevity (kept in this file because the surface is small and they
share types).

* ``GET  /api/mission-config``
      Public, no auth. Frontend hook calls this on every page load.
* ``POST /api/mission-participations``
      Public, no auth. Body: ``{mission_id, email, wallet?, locale?}``.
      Records the row, then fires a fire-and-forget email send.
* ``PUT  /api/admin/mission-config``
      Admin (JWT). Partial patch — only the keys in the body are updated.
* ``GET  /api/admin/mission-config/snapshot``
      Admin (JWT). Returns the full config + participation counts.
* ``GET  /api/admin/mission-participations``
      Admin (JWT). Lists last 200 (filterable by ``mission_id``).
* ``POST /api/admin/mission-participations/{id}/resend``
      Admin (JWT). Re-trigger the email for a failed/missed row.
"""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from core import (
    mission_config,
    mission_emails,
    mission_illustrations,
    mission_participations,
)
from core.config import logger
from core.security import require_admin

# ---------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------
class ConfigOut(BaseModel):
    """Public-safe view of the mission config singleton."""

    giveaway_draw_date_iso: str
    giveaway_snapshot_date_iso: str
    giveaway_reward_sol: float
    giveaway_winners_count: int
    giveaway_min_invites: int
    giveaway_min_holding_usd: float
    extraction_chamber_title_fr: Optional[str] = None
    extraction_chamber_title_en: Optional[str] = None
    extraction_chamber_subtitle_fr: Optional[str] = None
    extraction_chamber_subtitle_en: Optional[str] = None
    extraction_chamber_body_fr: Optional[str] = None
    extraction_chamber_body_en: Optional[str] = None
    missions: Dict[str, Dict[str, Any]]
    emails_enabled: bool
    emails_helius_auto_send: bool
    emails_sender_name: str
    updated_at: Optional[datetime] = None
    updated_by: Optional[str] = None


class ParticipationPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    mission_id: str = Field(..., min_length=1, max_length=40)
    email: EmailStr
    wallet_address: Optional[str] = Field(default=None, max_length=64)
    locale: str = Field(default="fr", pattern=r"^(fr|en)$")


class ParticipationAck(BaseModel):
    ok: bool = True
    participation_id: str
    email_queued: bool


# ---------------------------------------------------------------------
# Public router
# ---------------------------------------------------------------------
public_router = APIRouter(tags=["missions-command"])


def _hash_ip(req: Request) -> Optional[str]:
    ip = req.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        req.client.host if req.client else ""
    )
    if not ip:
        return None
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:24]


@public_router.get("/api/mission-config", response_model=ConfigOut)
async def get_mission_config_public() -> ConfigOut:
    cfg = await mission_config.get_config()
    return ConfigOut(
        giveaway_draw_date_iso=cfg["giveaway_draw_date_iso"],
        giveaway_snapshot_date_iso=cfg["giveaway_snapshot_date_iso"],
        giveaway_reward_sol=float(cfg["giveaway_reward_sol"]),
        giveaway_winners_count=int(cfg["giveaway_winners_count"]),
        giveaway_min_invites=int(cfg["giveaway_min_invites"]),
        giveaway_min_holding_usd=float(cfg["giveaway_min_holding_usd"]),
        extraction_chamber_title_fr=cfg.get("extraction_chamber_title_fr"),
        extraction_chamber_title_en=cfg.get("extraction_chamber_title_en"),
        extraction_chamber_subtitle_fr=cfg.get("extraction_chamber_subtitle_fr"),
        extraction_chamber_subtitle_en=cfg.get("extraction_chamber_subtitle_en"),
        extraction_chamber_body_fr=cfg.get("extraction_chamber_body_fr"),
        extraction_chamber_body_en=cfg.get("extraction_chamber_body_en"),
        missions=cfg.get("missions", {}),
        emails_enabled=bool(cfg.get("emails_enabled", True)),
        emails_helius_auto_send=bool(cfg.get("emails_helius_auto_send", False)),
        emails_sender_name=str(cfg.get("emails_sender_name", "")),
        updated_at=cfg.get("updated_at"),
        updated_by=cfg.get("updated_by"),
    )


@public_router.post("/api/mission-participations", response_model=ParticipationAck)
async def submit_participation(
    payload: ParticipationPayload, request: Request
) -> ParticipationAck:
    if payload.mission_id not in mission_config.VALID_MISSION_IDS:
        raise HTTPException(status_code=400, detail="unknown mission_id")
    cfg = await mission_config.get_config()
    ip_hash = _hash_ip(request)
    doc = await mission_participations.record_participation(
        mission_id=payload.mission_id,
        email=payload.email,
        wallet_address=payload.wallet_address,
        locale=payload.locale,
        source="form",
        ip_hash=ip_hash,
    )

    # Fire-and-forget email if globally enabled.
    email_queued = False
    if cfg.get("emails_enabled", True):
        # Resolve CTA URL: per-mission override or default to Telegram.
        per_mission = (cfg.get("missions") or {}).get(payload.mission_id, {})
        cta_url = per_mission.get("cta_url") or "https://t.me/deepotus"
        asyncio.create_task(
            mission_emails.send_mission_email(
                participation_id=doc["_id"],
                mission_id=payload.mission_id,
                to_email=payload.email,
                locale=payload.locale,
                cta_url=cta_url,
            )
        )
        email_queued = True

    return ParticipationAck(
        ok=True,
        participation_id=doc["_id"],
        email_queued=email_queued,
    )


# ---------------------------------------------------------------------
# Admin router
# ---------------------------------------------------------------------
admin_router = APIRouter(
    prefix="/api/admin",
    tags=["missions-command-admin"],
    dependencies=[Depends(require_admin)],
)


class UpdateConfigPayload(BaseModel):
    """Loose schema — we forward any allowed key to the core.
    Validation is enforced server-side by ``mission_config._coerce_field``.
    """

    model_config = ConfigDict(extra="allow")


@admin_router.get("/mission-config/snapshot")
async def admin_config_snapshot() -> Dict[str, Any]:
    cfg = await mission_config.get_config()
    counts = await mission_participations.count_by_mission()
    illustrations = await mission_illustrations.list_illustrations()
    return {
        "config": cfg,
        "participation_counts": counts,
        "illustrations": illustrations,
    }


@admin_router.put("/mission-config")
async def admin_update_config(payload: UpdateConfigPayload) -> Dict[str, Any]:
    try:
        patch = payload.model_dump(exclude_unset=True)
        # Strip ``_id`` / audit fields if present.
        for k in ("_id", "updated_at", "updated_by"):
            patch.pop(k, None)
        merged = await mission_config.update_config(patch, actor="admin")
        return {"ok": True, "config": merged}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@admin_router.post("/mission-config/illustrations/{mission_id}/regenerate")
async def admin_regenerate_illustration(
    mission_id: str, force: bool = True
) -> Dict[str, Any]:
    try:
        out = await mission_illustrations.generate_mission_illustration(
            mission_id, force=force
        )
        return {"ok": True, **out}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@admin_router.get("/mission-participations")
async def admin_list_participations(
    mission_id: Optional[str] = None, limit: int = 200
) -> Dict[str, Any]:
    rows = await mission_participations.list_participations(
        mission_id=mission_id, limit=limit
    )
    # Serialise datetimes for JSON
    def _ser(d: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(d)
        for k in ("created_at", "updated_at", "email_sent_at"):
            if isinstance(out.get(k), datetime):
                out[k] = out[k].isoformat()
        return out
    return {"participations": [_ser(r) for r in rows], "count": len(rows)}


@admin_router.post("/mission-participations/{participation_id}/resend")
async def admin_resend_email(participation_id: str) -> Dict[str, Any]:
    # Find the row
    from core.config import db
    doc = await db.mission_participations.find_one({"_id": participation_id})
    if not doc:
        raise HTTPException(status_code=404, detail="participation not found")
    cfg = await mission_config.get_config()
    if not cfg.get("emails_enabled", True):
        raise HTTPException(status_code=409, detail="emails_disabled_globally")
    per_mission = (cfg.get("missions") or {}).get(doc["mission_id"], {})
    cta_url = per_mission.get("cta_url") or "https://t.me/deepotus"
    res = await mission_emails.send_mission_email(
        participation_id=participation_id,
        mission_id=doc["mission_id"],
        to_email=doc["email"],
        locale=doc.get("locale", "fr"),
        cta_url=cta_url,
    )
    return {"ok": bool(res.get("ok")), "detail": res}


__all__ = ["public_router", "admin_router"]
