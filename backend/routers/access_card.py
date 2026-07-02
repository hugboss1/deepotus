"""Level 2 Access Card system — the sarcastic deep-state gatekeeper.

Flow:
    1. Visitor fails Level 1 → CRT Terminal popup asks for clearance.
    2. Visitor POST /access-card/request with email + display_name.
    3. Backend generates a PNG access card + emails it.
    4. Visitor types the accreditation number on /classified-vault gate
       (armored door keypad) → POST /access-card/verify.
    5. We return a short-lived session token (X-Session-Token header).
    6. Subsequent GET /access-card/status confirms the session.
"""

from __future__ import annotations

import asyncio
import base64 as b64mod
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import resend
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pymongo.errors import DuplicateKeyError

import access_card as access_card_mod
from core import genesis_promotion
from core.config import db
from core.secret_provider import (
    get_public_base_url,
    get_resend_api_key,
    get_sender_email,
)
from core.security import require_admin
from core.vault_seal import get_sealed_status, raise_if_sealed
from email_templates import (
    access_card_subject,
    genesis_broadcast_subject,
    render_access_card_email,
    render_genesis_broadcast_email,
)
from pydantic import BaseModel, EmailStr, Field

router = APIRouter(prefix="/api/access-card", tags=["access-card"])
admin_router = APIRouter(prefix="/api/admin/access-card", tags=["access-card-admin"])


async def send_access_card_email(
    email: str,
    *,
    lang: str,
    card_doc: dict,
    base_url: str,
) -> bool:
    """Render + send the Level 02 access card email (Mail #2).

    Shared by the public /request flow and the admin genesis promotion.
    Returns True when Resend accepted the email, False otherwise (missing
    key, render/attach failure, API error) — callers use this to decide
    whether the recipient can be considered served.
    """
    api_key = await get_resend_api_key()
    if not api_key:
        logging.warning("[access-card] Resend key missing; skipping email")
        return False
    resend.api_key = api_key
    sender = await get_sender_email()
    accred = card_doc["accreditation_number"]
    dn = card_doc["display_name"]
    try:
        html = render_access_card_email(
            lang=lang,
            display_name=dn,
            accreditation_number=accred,
            issued_at=card_doc["issued_at"][:10],
            expires_at=card_doc["expires_at"][:10],
            base_url=base_url,
            card_cid="access-card",
        )
        subject = access_card_subject(lang)
        # Attach the card image as inline CID
        with open(card_doc["card_path"], "rb") as fh:
            card_b64 = b64mod.b64encode(fh.read()).decode("ascii")
        params = {
            "from": sender,
            "to": [email],
            "subject": subject,
            "html": html,
            "attachments": [
                {
                    "filename": f"deepstate-access-card-{accred}.png",
                    "content": card_b64,
                    "content_id": "access-card",
                }
            ],
            "tags": [
                {"name": "category", "value": "access_card_level2"},
                {"name": "lang", "value": lang},
            ],
        }
        res = await asyncio.to_thread(resend.Emails.send, params)
        eid = (res or {}).get("id") if isinstance(res, dict) else None
        await db.email_events.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "type": "access_card.sent",
                "email_id": eid,
                "recipient": email,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "raw": {
                    "accreditation_number": accred,
                    "display_name": dn,
                    "lang": lang,
                },
            }
        )
        logging.info(f"[access-card] sent to={email} accred={accred} id={eid}")
        return True
    except Exception:
        logging.exception(f"[access-card] email failed for {email}")
        return False


@router.post(
    "/request",
    response_model=access_card_mod.AccessCardResponse,
)
async def access_card_request(
    req: access_card_mod.AccessCardRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Publicly callable: visitor asks for a Level 2 access card.

    Defense in depth: if the classified vault is currently sealed (mint not
    yet live OR admin override), refuse with 403 VAULT_SEALED so even a
    bypass of the frontend cannot trigger the email-2 / accreditation flow
    pre-genesis. Use the /api/access-card/genesis-broadcast endpoint
    instead during seal mode.
    """
    await raise_if_sealed(db, action="request_accreditation")

    email = req.email.lower().strip()

    # Check blacklist (reuse existing collection)
    bl = await db.blacklist.find_one({"email": email})
    if bl:
        raise HTTPException(status_code=403, detail="Agent revoked")

    wl = await db.whitelist.find_one({"email": email})
    whitelisted = bool(wl)

    display_name = (req.display_name or "").strip() or None
    # Sprint 17.5 — x_handle (optional) propagates from the popup form
    # all the way to the clearance ledger so Welcome Signal +
    # Interaction Bot have a usable target. Strip leading @ and trim
    # to the X 15-char limit just to be defensive.
    raw_handle = (req.x_handle or "").strip().lstrip("@")
    x_handle: Optional[str] = raw_handle[:15] if raw_handle else None

    base_url = await get_public_base_url()
    card_doc = await access_card_mod.create_or_refresh_card(
        db,
        email=email,
        display_name=display_name,
        whitelisted=whitelisted,
        base_url=base_url,
        x_handle=x_handle,
    )

    # Mirror the x_handle (and email) into clearance_levels so the
    # Welcome Signal selector can find this Agent. We do this OUTSIDE
    # the access_card path so the clearance row is created/refreshed
    # whether the user is on the genesis broadcast path or the regular
    # accreditation path. Errors here are logged but never raised —
    # accreditation must succeed even if the ledger sync fails.
    if x_handle:
        try:
            from core import clearance_levels as _clr  # local import — keeps cold-start light

            await _clr.upsert_x_handle(email=email, x_handle=x_handle, source="terminal")
        except Exception:  # noqa: BLE001
            logging.exception("[access-card] x_handle mirror to clearance_levels failed")

    # Send the email in the background
    dn = card_doc["display_name"]
    expires_at_iso = card_doc.get("expires_at")

    async def _send_email(lang: str = "fr"):
        await send_access_card_email(
            email, lang=lang, card_doc=card_doc, base_url=base_url
        )

    # Infer language from Accept-Language header best-effort
    lang = "fr"
    al = (request.headers.get("accept-language") or "").lower()
    if al.startswith("en"):
        lang = "en"
    background_tasks.add_task(_send_email, lang)

    return access_card_mod.AccessCardResponse(
        ok=True,
        email=email,
        # SECURITY: never leak the accreditation number to the public terminal
        # response — the visitor must read their email to obtain it. This is
        # the whole point of the email-gated flow.
        accreditation_number=None,
        display_name=dn,
        message="Access card dispatched. Check your inbox to retrieve the credentials.",
        card_url=None,
        requires_email_step=True,
        expires_at=expires_at_iso,
    )


@router.post(
    "/verify",
    response_model=access_card_mod.AccessCardVerifyResponse,
)
async def access_card_verify(req: access_card_mod.AccessCardVerifyRequest):
    await raise_if_sealed(db, action="verify_accreditation")

    raw = (req.accreditation_number or "").strip().upper()
    raw = "".join(c for c in raw if c.isalnum() or c == "-")
    if not raw:
        raise HTTPException(status_code=400, detail="missing accreditation_number")

    card = await access_card_mod.find_card_by_accred(db, raw)
    if not card:
        return access_card_mod.AccessCardVerifyResponse(
            ok=False,
            message="Accreditation not recognized.",
        )
    try:
        exp = datetime.fromisoformat(card["expires_at"].replace("Z", "+00:00"))
        if exp < datetime.now(timezone.utc):
            return access_card_mod.AccessCardVerifyResponse(
                ok=False,
                accreditation_number=raw,
                message="Accreditation expired.",
            )
    except Exception:
        pass

    session = await access_card_mod.create_session(
        db, accred=raw, display_name=card.get("display_name")
    )
    return access_card_mod.AccessCardVerifyResponse(
        ok=True,
        accreditation_number=raw,
        display_name=card.get("display_name"),
        session_token=session["_id"],
        issued_at=session["issued_at"],
        expires_at=session["expires_at"],
        message="Clearance confirmed. Access granted.",
    )


@router.get("/status")
async def access_card_status(request: Request):
    """Check if the current X-Session-Token header is a valid access session."""
    token = request.headers.get("x-session-token") or request.headers.get(
        "x-access-session"
    )
    session = await access_card_mod.validate_session(db, token or "")
    if not session:
        return {"ok": False}
    return {
        "ok": True,
        "accreditation_number": session["accreditation_number"],
        "display_name": session.get("display_name"),
        "expires_at": session["expires_at"],
    }


@router.get("/image/{accred}")
async def access_card_image(accred: str):
    """Serve an access card PNG by accreditation number. Intentionally public —
    the accreditation number IS the secret (like a Bearer token)."""
    accred = accred.strip().upper()
    card = await access_card_mod.find_card_by_accred(db, accred)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    path = Path(card["card_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Card image missing")
    return FileResponse(path, media_type="image/png")



# ---------------------------------------------------------------------
# Genesis Broadcast — pre-launch subscription (Mail #1)
# Used when classified vault is SEALED. Captures emails as Genesis
# subscribers; the regular accreditation flow (Mail #2) re-opens
# automatically once the vault flips to LIVE.
# ---------------------------------------------------------------------
class GenesisBroadcastRequest(BaseModel):
    email: EmailStr
    display_name: str | None = Field(default=None, max_length=64)
    lang: str | None = Field(default=None, pattern=r"^(fr|en)$")


class GenesisBroadcastResponse(BaseModel):
    ok: bool
    email: EmailStr
    display_name: str
    message: str
    launch_eta: str | None = None
    already_subscribed: bool = False
    position: int | None = None


@router.post("/genesis-broadcast", response_model=GenesisBroadcastResponse)
async def genesis_broadcast_request(
    req: GenesisBroadcastRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Capture a Genesis broadcast subscriber while the vault is SEALED.

    This endpoint is only meaningful pre-mint:
        - sealed=True → record the subscriber and queue Mail #1.
        - sealed=False → 410 Gone, redirect the client to /access-card/request
          (the regular Level-2 accreditation flow has re-opened).

    On admin override Force-Live, this endpoint also returns 410 so we don't
    capture stale subscribers when the vault is artificially open.
    """
    status_obj = await get_sealed_status(db)
    if not status_obj["sealed"]:
        raise HTTPException(
            status_code=410,
            detail={
                "code": "VAULT_LIVE",
                "message": (
                    "The classified vault has opened. Use /access-card/request "
                    "to receive your Level 02 accreditation directly."
                ),
            },
        )

    email = req.email.lower().strip()

    # Honor blacklist (same as access-card/request)
    bl = await db.blacklist.find_one({"email": email})
    if bl:
        raise HTTPException(status_code=403, detail="Agent revoked")

    display_name = (req.display_name or "").strip() or email.split("@")[0]

    # Idempotent upsert with ordered position (helps narrative "in arrival order")
    existing = await db.genesis_subscribers.find_one({"email": email})
    if existing:
        already = True
        position = existing.get("position", 0)
    else:
        already = False
        count = await db.genesis_subscribers.count_documents({})
        position = count + 1
        doc = genesis_promotion.build_genesis_subscriber_doc(
            email=email,
            display_name=display_name,
            position=position,
            lang=req.lang or "fr",
            ip=request.client.host if request.client else None,
            ua=request.headers.get("user-agent"),
        )
        try:
            await db.genesis_subscribers.insert_one(doc)
        except DuplicateKeyError:
            # Concurrent double-submit, or legacy collision on the ecosystem
            # (email_hash, source) unique index — treat as already subscribed.
            logging.warning("[genesis] duplicate subscriber insert for %s", email)
            already = True

    # Send Mail #1 in the background (idempotent: only resend if NOT already)
    lang = req.lang or "fr"
    al = (request.headers.get("accept-language") or "").lower()
    if not req.lang and al.startswith("en"):
        lang = "en"

    async def _send_mail_1():
        if already:
            logging.info(f"[genesis] {email} already subscribed, no mail re-sent")
            return
        api_key = await get_resend_api_key()
        if not api_key:
            logging.warning("[genesis] Resend key missing; skipping email")
            return
        resend.api_key = api_key
        sender = await get_sender_email()
        try:
            html = render_genesis_broadcast_email(
                lang=lang,
                display_name=display_name,
                base_url=await get_public_base_url(),
                launch_eta=status_obj.get("launch_eta"),
            )
            subject = genesis_broadcast_subject(lang)
            params = {
                "from": sender,
                "to": [email],
                "subject": subject,
                "html": html,
                "tags": [
                    {"name": "category", "value": "genesis_broadcast"},
                    {"name": "lang", "value": lang},
                ],
            }
            res = await asyncio.to_thread(resend.Emails.send, params)
            eid = (res or {}).get("id") if isinstance(res, dict) else None
            await db.email_events.insert_one(
                {
                    "_id": str(uuid.uuid4()),
                    "type": "genesis_broadcast.sent",
                    "email_id": eid,
                    "recipient": email,
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "raw": {
                        "display_name": display_name,
                        "lang": lang,
                        "position": position,
                    },
                }
            )
            logging.info(f"[genesis] sent to={email} pos=#{position} id={eid}")
        except Exception:
            logging.exception(f"[genesis] mail #1 failed for {email}")

    background_tasks.add_task(_send_mail_1)

    return GenesisBroadcastResponse(
        ok=True,
        email=email,
        display_name=display_name,
        message=(
            "Genesis subscription archived. Watch your inbox — Mail #1 just left "
            "the Cabinet, Mail #2 will follow at mint."
        ),
        launch_eta=status_obj.get("launch_eta"),
        already_subscribed=already,
        position=position,
    )


# ---------------------------------------------------------------------
# Admin — Genesis promotion (Mail #2 backfill after the vault unseals)
# ---------------------------------------------------------------------
async def _promotion_create_card(*, email: str, display_name: str, whitelisted: bool):
    base_url = await get_public_base_url()
    return await access_card_mod.create_or_refresh_card(
        db,
        email=email,
        display_name=display_name,
        whitelisted=whitelisted,
        base_url=base_url,
        x_handle=None,
    )


async def _promotion_send_email(*, email: str, lang: str, card_doc: dict) -> bool:
    base_url = await get_public_base_url()
    return await send_access_card_email(
        email, lang=lang, card_doc=card_doc, base_url=base_url
    )


class GenesisPromoteRequest(BaseModel):
    dry_run: bool = False
    limit: Optional[int] = Field(default=None, ge=1, le=5000)
    # Staff QA escape hatch: run even while the vault is sealed.
    force: bool = False


@admin_router.get("/genesis/pending", response_model=dict)
async def genesis_promotion_pending(_p: dict = Depends(require_admin)):
    """List subscribers still awaiting their Level 02 card (read-only).

    Works even while the vault is sealed so the admin can size the backlog
    before mint-day.
    """
    return await genesis_promotion.promote_pending(
        db,
        create_card=_promotion_create_card,
        send_email=_promotion_send_email,
        dry_run=True,
        force=True,
    )


@admin_router.post("/genesis/promote", response_model=dict)
async def genesis_promotion_run(
    req: GenesisPromoteRequest, _p: dict = Depends(require_admin)
):
    """Send Mail #2 (Level 02 access card) to every pending genesis subscriber.

    Refuses with code VAULT_SEALED while the vault is sealed unless ``force``
    — Mail #1 promised the card would arrive at mint, not before. Failed
    sends stay un-promoted and are retried on the next run.
    """
    return await genesis_promotion.promote_pending(
        db,
        create_card=_promotion_create_card,
        send_email=_promotion_send_email,
        dry_run=req.dry_run,
        limit=req.limit,
        force=req.force,
    )
