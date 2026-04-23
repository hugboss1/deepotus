"""
Level 2 Access Card system for $DEEPOTUS / PROTOCOL ΔΣ.

Flow:
  1. Visitor cracks the fake Vault and clicks the CTA
  2. A TerminalPopup denies access and invites them to request Level 2
  3. POST /api/access-card/request with their email (+ optional display name)
  4. We verify they are on the whitelist, generate a unique accreditation number,
     personalize the AI-generated card template (name + accreditation + QR + dates),
     save it, and send it to the user by email
  5. Later, the visitor enters their accreditation number on /classified-vault
  6. POST /api/access-card/verify returns a signed session token → full access

The Gemini-generated template sits at /app/backend/assets/access_card_template.png.
Zones (% of card width/height) used for overlay come from analyzing the template.
"""

from __future__ import annotations

import io
import os
import re
import uuid
import base64
import secrets
import string
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import qrcode
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, EmailStr, Field

# ---------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------
TEMPLATE_PATH = Path("/app/backend/assets/access_card_template.png")
CARDS_DIR = Path("/app/backend/assets/cards")
CARDS_DIR.mkdir(parents=True, exist_ok=True)

FONT_MONO_BOLD = "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
FONT_SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# Template overlay zones, calibrated precisely from the generated template
# (all coordinates are percentages of template width/height).
ZONES = {
    "name_banner": {"left": 0.32, "top": 0.25, "w": 0.38, "h": 0.12},
    "accred_banner": {"left": 0.32, "top": 0.505, "w": 0.38, "h": 0.105},
    "issue_date": {"left": 0.08, "top": 0.655, "w": 0.14, "h": 0.075},
    "expire_date": {"left": 0.08, "top": 0.775, "w": 0.14, "h": 0.075},
    "qr_slot": {"left": 0.72, "top": 0.64, "w": 0.18, "h": 0.205},
    "microtext_strip": {"left": 0.27, "top": 0.79, "w": 0.41, "h": 0.07},
}

# Accreditation lifetime
ACCRED_TTL_DAYS = 365
# Session (after verify) lifetime
SESSION_TTL_HOURS = 24

# Colors used during overlay (match the existing card design)
COLOR_AMBER = (245, 158, 11, 255)
COLOR_CYAN = (34, 211, 238, 255)
COLOR_WHITE_SOFT = (235, 235, 235, 255)
COLOR_DIM = (160, 160, 160, 255)
COLOR_CARD_MATTE_DARK = (14, 14, 16, 255)  # to mask placeholder text
COLOR_TRANSPARENT_SHADOW = (0, 0, 0, 140)


# ---------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------
class AccessCardRequest(BaseModel):
    email: EmailStr
    display_name: Optional[str] = Field(None, max_length=80)
    # Optional hint: user claims they already joined the whitelist;
    # if the email is NOT whitelisted we still proceed but flag it (we don't
    # want a dead-end for the narrative).
    require_whitelist: Optional[bool] = False


class AccessCardResponse(BaseModel):
    ok: bool
    email: EmailStr
    accreditation_number: str
    display_name: str
    message: str
    # Where the card image is accessible (relative URL)
    card_url: Optional[str] = None


class AccessCardVerifyRequest(BaseModel):
    accreditation_number: str = Field(..., min_length=8, max_length=40)


class AccessCardVerifyResponse(BaseModel):
    ok: bool
    accreditation_number: Optional[str] = None
    display_name: Optional[str] = None
    session_token: Optional[str] = None
    issued_at: Optional[str] = None
    expires_at: Optional[str] = None
    message: str


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _slugify_email(email: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "", email.split("@")[0].upper())
    return base[:8] or "AGENT"


def _derive_display_name(email: str) -> str:
    """Generate a codename from the email if the user did not provide one."""
    agent = _slugify_email(email)
    suffix = "".join(secrets.choice(string.digits) for _ in range(3))
    return f"AGENT {agent}-{suffix}"


def generate_accreditation_number() -> str:
    """Generate a cryptographically-random accreditation number.

    The accreditation number IS the Level-2 Bearer token (used by the
    /classified-vault gate). It MUST be unpredictable, hence `secrets`.
    Format: DS-02-XXXX-XXXX-XX (uppercase alphanumerics).
    """
    pool = string.ascii_uppercase + string.digits
    blocks = [
        "".join(secrets.choice(pool) for _ in range(4)),
        "".join(secrets.choice(pool) for _ in range(4)),
        "".join(secrets.choice(pool) for _ in range(2)),
    ]
    return f"DS-02-{blocks[0]}-{blocks[1]}-{blocks[2]}"


def _try_load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        logging.warning(f"[access_card] font missing: {path} — fallback")
        return ImageFont.load_default()


def _fit_text_in_box(
    draw: ImageDraw.ImageDraw,
    text: str,
    box_w: int,
    max_size: int,
    min_size: int,
    font_path: str,
) -> Tuple[ImageFont.FreeTypeFont, int]:
    """Find the largest font size at which `text` fits within `box_w`."""
    for size in range(max_size, min_size - 1, -1):
        f = _try_load_font(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=f)
        w = bbox[2] - bbox[0]
        if w <= box_w:
            return f, size
    # Fallback: smallest possible
    return _try_load_font(font_path, min_size), min_size


def _mask_zone(
    img: Image.Image,
    zone_key: str,
    pad_x: int = 0,
    pad_y: int = 0,
    fill=COLOR_CARD_MATTE_DARK,
) -> Tuple[int, int, int, int]:
    """Paint a matte rectangle over the template placeholder text. Returns the
    absolute box (x0, y0, x1, y1) for downstream overlay placement."""
    W, H = img.size
    z = ZONES[zone_key]
    x0 = int(z["left"] * W) - pad_x
    y0 = int(z["top"] * H) - pad_y
    x1 = int((z["left"] + z["w"]) * W) + pad_x
    y1 = int((z["top"] + z["h"]) * H) + pad_y

    draw = ImageDraw.Draw(img)
    # Slight darker than COLOR_CARD_MATTE_DARK on the banners, flatter on small fields
    draw.rectangle([x0, y0, x1, y1], fill=fill)
    return (x0, y0, x1, y1)


# ---------------------------------------------------------------------
# Card rendering
# ---------------------------------------------------------------------
def render_card(
    *,
    display_name: str,
    accreditation_number: str,
    issued_at: datetime,
    expires_at: datetime,
    output_path: Path,
) -> Path:
    """Render a personalized access card on top of the pre-generated template."""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Access card template missing at {TEMPLATE_PATH}. "
            "Run tests/generate_access_card_template.py first."
        )

    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    W, H = base.size
    draw = ImageDraw.Draw(base)

    # --- 1) Mask all placeholder text in the template ---
    name_box = _mask_zone(
        base, "name_banner", pad_x=4, pad_y=4, fill=COLOR_CARD_MATTE_DARK
    )
    accred_box = _mask_zone(
        base, "accred_banner", pad_x=4, pad_y=4, fill=COLOR_CARD_MATTE_DARK
    )
    issue_box = _mask_zone(
        base, "issue_date", pad_x=2, pad_y=2, fill=COLOR_CARD_MATTE_DARK
    )
    expire_box = _mask_zone(
        base, "expire_date", pad_x=2, pad_y=2, fill=COLOR_CARD_MATTE_DARK
    )
    qr_box = _mask_zone(
        base, "qr_slot", pad_x=0, pad_y=0, fill=COLOR_CARD_MATTE_DARK
    )
    _mask_zone(
        base,
        "microtext_strip",
        pad_x=2,
        pad_y=2,
        fill=(18, 18, 20, 255),
    )

    # --- 2) Redraw a thin cyan underline on the name banner (signature line) ---
    nx0, ny0, nx1, ny1 = name_box
    draw.line([(nx0 + 10, ny1 - 4), (nx1 - 10, ny1 - 4)], fill=COLOR_CYAN, width=2)
    # And a thin amber underline on accreditation banner
    ax0, ay0, ax1, ay1 = accred_box
    draw.line([(ax0 + 10, ay1 - 4), (ax1 - 10, ay1 - 4)], fill=COLOR_AMBER, width=2)

    # --- 3) Write the NAME ---
    name_w = nx1 - nx0 - 24
    name_h = ny1 - ny0
    name_font, name_size = _fit_text_in_box(
        draw,
        display_name.upper(),
        name_w,
        max_size=54,
        min_size=18,
        font_path=FONT_SANS_BOLD,
    )
    nb = draw.textbbox((0, 0), display_name.upper(), font=name_font)
    nw = nb[2] - nb[0]
    nh = nb[3] - nb[1]
    draw.text(
        (nx0 + (nx1 - nx0 - nw) // 2, ny0 + (name_h - nh) // 2 - 4),
        display_name.upper(),
        font=name_font,
        fill=COLOR_WHITE_SOFT,
    )

    # --- 4) Write the ACCREDITATION NUMBER ---
    accred_w = ax1 - ax0 - 20
    accred_h = ay1 - ay0
    accred_font, _ = _fit_text_in_box(
        draw,
        accreditation_number,
        accred_w,
        max_size=46,
        min_size=16,
        font_path=FONT_MONO_BOLD,
    )
    ab = draw.textbbox((0, 0), accreditation_number, font=accred_font)
    aw = ab[2] - ab[0]
    ah = ab[3] - ab[1]
    draw.text(
        (ax0 + (ax1 - ax0 - aw) // 2, ay0 + (accred_h - ah) // 2 - 4),
        accreditation_number,
        font=accred_font,
        fill=COLOR_AMBER,
    )

    # --- 5) Dates ---
    def _format_date(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d")

    small_font = _try_load_font(FONT_MONO_BOLD, 18)
    draw.text(
        (issue_box[0] + 8, issue_box[1] + 6),
        _format_date(issued_at),
        font=small_font,
        fill=COLOR_CYAN,
    )
    draw.text(
        (expire_box[0] + 8, expire_box[1] + 6),
        _format_date(expires_at),
        font=small_font,
        fill=COLOR_AMBER,
    )

    # --- 6) QR code ---
    qr_w = qr_box[2] - qr_box[0]
    qr_h = qr_box[3] - qr_box[1]
    qr_img = qrcode.make(
        accreditation_number,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    # Convert to RGBA and resize
    qr_img = qr_img.convert("RGBA")
    qr_side = min(qr_w, qr_h) - 12
    qr_img = qr_img.resize((qr_side, qr_side), Image.LANCZOS)
    # Place centered within the slot
    qx = qr_box[0] + (qr_w - qr_side) // 2
    qy = qr_box[1] + (qr_h - qr_side) // 2
    base.paste(qr_img, (qx, qy), qr_img)

    # --- 7) Discreet microtext over the bottom strip ---
    micro_font = _try_load_font(FONT_MONO, 13)
    micro = f"// CLEARANCE LEVEL 02 · PROTOCOL ΔΣ · {accreditation_number} //"
    mz = ZONES["microtext_strip"]
    mx = int(mz["left"] * W)
    my = int(mz["top"] * H)
    mw = int(mz["w"] * W)
    mh = int(mz["h"] * H)
    mb = draw.textbbox((0, 0), micro, font=micro_font)
    mtw = mb[2] - mb[0]
    mth = mb[3] - mb[1]
    draw.text(
        (mx + (mw - mtw) // 2, my + (mh - mth) // 2 - 2),
        micro,
        font=micro_font,
        fill=COLOR_DIM,
    )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(output_path, format="PNG", optimize=True)
    return output_path


# ---------------------------------------------------------------------
# DB-facing helpers
# ---------------------------------------------------------------------
async def find_card_by_accred(db, accreditation_number: str) -> Optional[Dict[str, Any]]:
    return await db.access_cards.find_one(
        {"accreditation_number": accreditation_number.upper()}
    )


async def find_card_by_email(db, email: str) -> Optional[Dict[str, Any]]:
    return await db.access_cards.find_one({"email": email.lower()})


async def create_or_refresh_card(
    db,
    *,
    email: str,
    display_name: Optional[str] = None,
    whitelisted: bool = False,
) -> Dict[str, Any]:
    """Idempotent-ish: if a card already exists for the email, refresh its image
    using the stored accreditation number (so the user always gets the same code
    even if they request twice)."""
    email = email.lower().strip()
    existing = await find_card_by_email(db, email)

    if existing:
        accreditation = existing["accreditation_number"]
        display_name = existing.get("display_name") or display_name or _derive_display_name(email)
        issued_at = datetime.fromisoformat(existing["issued_at"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(existing["expires_at"].replace("Z", "+00:00"))
        doc_id = existing["_id"]
    else:
        accreditation = generate_accreditation_number()
        display_name = display_name or _derive_display_name(email)
        issued_at = _now()
        expires_at = issued_at + timedelta(days=ACCRED_TTL_DAYS)
        doc_id = str(uuid.uuid4())

    output_path = CARDS_DIR / f"{accreditation}.png"
    render_card(
        display_name=display_name,
        accreditation_number=accreditation,
        issued_at=issued_at,
        expires_at=expires_at,
        output_path=output_path,
    )

    # Upsert
    await db.access_cards.update_one(
        {"_id": doc_id},
        {
            "$set": {
                "_id": doc_id,
                "email": email,
                "accreditation_number": accreditation,
                "display_name": display_name,
                "whitelisted": whitelisted,
                "issued_at": issued_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "card_path": str(output_path),
                "updated_at": _now_iso(),
            }
        },
        upsert=True,
    )
    doc = await db.access_cards.find_one({"_id": doc_id})
    return doc


async def create_session(db, accred: str, display_name: Optional[str] = None) -> Dict[str, Any]:
    token = uuid.uuid4().hex + uuid.uuid4().hex  # 64 chars
    now = _now()
    expires = now + timedelta(hours=SESSION_TTL_HOURS)
    doc = {
        "_id": token,
        "accreditation_number": accred,
        "display_name": display_name,
        "issued_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "revoked": False,
    }
    await db.access_sessions.insert_one(doc)
    return doc


async def validate_session(db, token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    doc = await db.access_sessions.find_one({"_id": token, "revoked": {"$ne": True}})
    if not doc:
        return None
    try:
        exp = datetime.fromisoformat(doc["expires_at"].replace("Z", "+00:00"))
        if exp < _now():
            return None
    except Exception:
        return None
    return doc


def card_to_base64(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii")
