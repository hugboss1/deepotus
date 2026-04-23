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

import resend
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse

import access_card as access_card_mod
from core.config import (
    PUBLIC_BASE_URL,
    RESEND_API_KEY,
    SENDER_EMAIL,
    db,
)
from email_templates import access_card_subject, render_access_card_email

router = APIRouter(prefix="/api/access-card", tags=["access-card"])


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

    We always succeed (narrative keeps flowing); whitelisted=True if email is
    found in the whitelist, False otherwise (we still send the card).
    """
    email = req.email.lower().strip()

    # Check blacklist (reuse existing collection)
    bl = await db.blacklist.find_one({"email": email})
    if bl:
        raise HTTPException(status_code=403, detail="Agent revoked")

    wl = await db.whitelist.find_one({"email": email})
    whitelisted = bool(wl)

    display_name = (req.display_name or "").strip() or None
    card_doc = await access_card_mod.create_or_refresh_card(
        db,
        email=email,
        display_name=display_name,
        whitelisted=whitelisted,
    )

    # Send the email in the background
    accred = card_doc["accreditation_number"]
    dn = card_doc["display_name"]
    card_path = card_doc["card_path"]

    async def _send_email(lang: str = "fr"):
        if not RESEND_API_KEY:
            logging.warning("[access-card] Resend key missing; skipping email")
            return
        try:
            html = render_access_card_email(
                lang=lang,
                display_name=dn,
                accreditation_number=accred,
                issued_at=card_doc["issued_at"][:10],
                expires_at=card_doc["expires_at"][:10],
                base_url=PUBLIC_BASE_URL,
                card_cid="access-card",
            )
            subject = access_card_subject(lang)
            # Attach the card image as inline CID
            with open(card_path, "rb") as fh:
                card_b64 = b64mod.b64encode(fh.read()).decode("ascii")
            params = {
                "from": SENDER_EMAIL,
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
        except Exception:
            logging.exception(f"[access-card] email failed for {email}")

    # Infer language from Accept-Language header best-effort
    lang = "fr"
    al = (request.headers.get("accept-language") or "").lower()
    if al.startswith("en"):
        lang = "en"
    background_tasks.add_task(_send_email, lang)

    return access_card_mod.AccessCardResponse(
        ok=True,
        email=email,
        accreditation_number=accred,
        display_name=dn,
        message="Access card generated. Check your inbox.",
        card_url=f"/api/access-card/image/{accred}",
    )


@router.post(
    "/verify",
    response_model=access_card_mod.AccessCardVerifyResponse,
)
async def access_card_verify(req: access_card_mod.AccessCardVerifyRequest):
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
