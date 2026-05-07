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
# Compute filesystem locations RELATIVE to this module so the code works
# whether the project is laid out under ``/app/backend`` (Emergent dev),
# ``/opt/render/project/src/backend`` (Render), Docker bind-mounts, or any
# other deployment layout. The module file is canonical.
_MODULE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = _MODULE_DIR / "assets" / "access_card_template.png"
CARDS_DIR = _MODULE_DIR / "assets" / "cards"


def _ensure_cards_dir() -> Path:
    """Lazily create the cards directory the first time we need to write
    a card. Doing this at import time crashes the backend on read-only
    filesystems (e.g. some Render instances when the project root is
    mounted read-only); doing it at first use means a single failing
    card-generation request is the worst case, not a boot-time crash.
    """
    try:
        CARDS_DIR.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError) as exc:
        # If the canonical location is read-only, fall back to /tmp which
        # is always writable on Render (ephemeral but cards are also
        # mailed to the recipient, so the on-disk copy is just a cache).
        logger = logging.getLogger("deepotus.access_card")
        logger.warning(
            "[access-card] %s not writable (%s) — falling back to /tmp",
            CARDS_DIR, exc,
        )
        fallback = Path("/tmp/deepotus_cards")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
    return CARDS_DIR


# Liberation Mono is the default in the Emergent dev image but is NOT
# guaranteed on every Render image. We resolve to the first font that
# actually exists on disk, falling back to DejaVu (ubiquitous on Debian
# bases) and finally to PIL's built-in bitmap font (always available,
# uglier but never crashes).
_FONT_CANDIDATES_MONO_BOLD = [
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
]
_FONT_CANDIDATES_MONO = [
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]
_FONT_CANDIDATES_SANS_BOLD = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def _first_existing(paths: list[str]) -> Optional[str]:
    for p in paths:
        if Path(p).is_file():
            return p
    return None


# Resolved at import time so the first card request doesn't pay the IO
# tax. Values may be ``None`` if no system font is available — the
# generation code tolerates that and falls back to PIL's default.
FONT_MONO_BOLD = _first_existing(_FONT_CANDIDATES_MONO_BOLD)
FONT_MONO = _first_existing(_FONT_CANDIDATES_MONO)
FONT_SANS_BOLD = _first_existing(_FONT_CANDIDATES_SANS_BOLD)

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

# Accreditation lifetime — 24h sliding window: every fresh request bumps
# expires_at to now+24h, so the visitor who reads their email within 24h
# can use the card; if they ignore it, they must re-request.
ACCRED_TTL_HOURS = 24
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
    # Sprint 17.5 — Cabinet Expansion. The Agent's public X handle, used
    # to (optionally) verify their follow status against @deepotus_ai
    # AND to address them in the daily Welcome Signal broadcast +
    # Prophet Interaction Bot replies. Optional: blank handle keeps
    # the legacy email-only flow working.
    x_handle: Optional[str] = Field(None, max_length=40)


class AccessCardResponse(BaseModel):
    ok: bool
    email: EmailStr
    # accreditation_number is INTENTIONALLY OPTIONAL — we never echo it back to
    # the public terminal so a visitor cannot bypass the email step and walk
    # straight into the vault. The number is only revealed inside the email
    # (text + image card + QR code). Internal callers (admin) may still set it.
    accreditation_number: Optional[str] = None
    display_name: str
    message: str
    # Where the card image is accessible (relative URL)
    card_url: Optional[str] = None
    # Hint to the front-end that the visitor must now check their inbox
    requires_email_step: bool = True
    # ISO timestamp at which the access card expires (so the UI can display "valid until")
    expires_at: Optional[str] = None


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
# Card rendering — split into small helpers for readability.
# ---------------------------------------------------------------------
def _mask_card_zones(base: Image.Image) -> dict:
    """Black out all placeholder zones on the template; return their boxes."""
    return {
        "name": _mask_zone(
            base, "name_banner", pad_x=4, pad_y=4, fill=COLOR_CARD_MATTE_DARK
        ),
        "accred": _mask_zone(
            base, "accred_banner", pad_x=4, pad_y=4, fill=COLOR_CARD_MATTE_DARK
        ),
        "issue": _mask_zone(
            base, "issue_date", pad_x=2, pad_y=2, fill=COLOR_CARD_MATTE_DARK
        ),
        "expire": _mask_zone(
            base, "expire_date", pad_x=2, pad_y=2, fill=COLOR_CARD_MATTE_DARK
        ),
        "qr": _mask_zone(
            base, "qr_slot", pad_x=0, pad_y=0, fill=COLOR_CARD_MATTE_DARK
        ),
        "_microtext_unused": _mask_zone(
            base,
            "microtext_strip",
            pad_x=2,
            pad_y=2,
            fill=(18, 18, 20, 255),
        ),
    }


def _draw_centered_in_box(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple,
    *,
    max_size: int,
    min_size: int,
    font_path: str,
    color,
    h_pad: int,
) -> None:
    """Auto-fit `text` and draw it centered inside `box`."""
    x0, y0, x1, y1 = box
    avail_w = (x1 - x0) - h_pad * 2
    box_h = y1 - y0
    font, _ = _fit_text_in_box(
        draw,
        text,
        avail_w,
        max_size=max_size,
        min_size=min_size,
        font_path=font_path,
    )
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    draw.text(
        (x0 + (x1 - x0 - tw) // 2, y0 + (box_h - th) // 2 - 4),
        text,
        font=font,
        fill=color,
    )


def _render_dates(
    draw: ImageDraw.ImageDraw,
    issued_at: datetime,
    expires_at: datetime,
    issue_box: tuple,
    expire_box: tuple,
) -> None:
    small_font = _try_load_font(FONT_MONO_BOLD, 18)
    draw.text(
        (issue_box[0] + 8, issue_box[1] + 6),
        issued_at.strftime("%Y-%m-%d"),
        font=small_font,
        fill=COLOR_CYAN,
    )
    draw.text(
        (expire_box[0] + 8, expire_box[1] + 6),
        expires_at.strftime("%Y-%m-%d"),
        font=small_font,
        fill=COLOR_AMBER,
    )


def _render_qr(base: Image.Image, qr_box: tuple, qr_data: str) -> None:
    qr_w = qr_box[2] - qr_box[0]
    qr_h = qr_box[3] - qr_box[1]
    qr_img = qrcode.make(
        qr_data,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    qr_img = qr_img.convert("RGBA")
    qr_side = min(qr_w, qr_h) - 12
    qr_img = qr_img.resize((qr_side, qr_side), Image.LANCZOS)
    qx = qr_box[0] + (qr_w - qr_side) // 2
    qy = qr_box[1] + (qr_h - qr_side) // 2
    base.paste(qr_img, (qx, qy), qr_img)


def _render_microtext(
    draw: ImageDraw.ImageDraw,
    accreditation_number: str,
    image_size: tuple,
) -> None:
    micro_font = _try_load_font(FONT_MONO, 13)
    micro = f"// CLEARANCE LEVEL 02 · PROTOCOL ΔΣ · {accreditation_number} //"
    W, H = image_size
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


def render_card(
    *,
    display_name: str,
    accreditation_number: str,
    issued_at: datetime,
    expires_at: datetime,
    output_path: Path,
    qr_payload: Optional[str] = None,
) -> Path:
    """Render a personalized access card on top of the pre-generated template.

    Pipeline:
        1. Open the template + mask placeholder zones (`_mask_card_zones`).
        2. Draw thin coloured underlines on the name and accred banners.
        3. Auto-fit + centre the agent NAME (`_draw_centered_in_box`).
        4. Auto-fit + centre the ACCREDITATION NUMBER.
        5. Render the two dates (`_render_dates`).
        6. Generate + paste the QR code (`_render_qr`).
        7. Stamp the microtext strip (`_render_microtext`).

    qr_payload: optional URL to encode in the QR code (typically
    `<base>/classified-vault?code=ACCRED`). Falls back to the bare
    accreditation number for backward compatibility.
    """
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(
            f"Access card template missing at {TEMPLATE_PATH}. "
            "Run tests/generate_access_card_template.py first."
        )

    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    draw = ImageDraw.Draw(base)

    boxes = _mask_card_zones(base)
    name_box = boxes["name"]
    accred_box = boxes["accred"]
    issue_box = boxes["issue"]
    expire_box = boxes["expire"]
    qr_box = boxes["qr"]

    # Decorative underlines on the name + accreditation banners.
    nx0, _, nx1, ny1 = name_box
    draw.line([(nx0 + 10, ny1 - 4), (nx1 - 10, ny1 - 4)], fill=COLOR_CYAN, width=2)
    ax0, _, ax1, ay1 = accred_box
    draw.line([(ax0 + 10, ay1 - 4), (ax1 - 10, ay1 - 4)], fill=COLOR_AMBER, width=2)

    _draw_centered_in_box(
        draw,
        display_name.upper(),
        name_box,
        max_size=54,
        min_size=18,
        font_path=FONT_SANS_BOLD,
        color=COLOR_WHITE_SOFT,
        h_pad=12,
    )
    _draw_centered_in_box(
        draw,
        accreditation_number,
        accred_box,
        max_size=46,
        min_size=16,
        font_path=FONT_MONO_BOLD,
        color=COLOR_AMBER,
        h_pad=10,
    )
    _render_dates(draw, issued_at, expires_at, issue_box, expire_box)
    _render_qr(base, qr_box, qr_payload or accreditation_number)
    _render_microtext(draw, accreditation_number, base.size)

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
    base_url: Optional[str] = None,
    x_handle: Optional[str] = None,
) -> Dict[str, Any]:
    """Create or refresh a card for the given email.

    The accreditation number is sticky: a returning visitor keeps the same
    code so they can re-receive the email without confusion.

    The expiration window however is **always reset to now + ACCRED_TTL_HOURS**
    (24 h sliding window). Rationale: the visitor proved ownership of the
    inbox at the moment of the request, so the 24 h timer should start now,
    not from the first historical request.

    base_url: optional base URL (e.g. `https://deepotus.xyz`). When provided,
    the QR code on the card encodes
    `{base_url}/classified-vault?code={accreditation_number}` so scanning
    opens the digicode page in the visitor's browser and auto-verifies.

    x_handle: optional public X handle (Sprint 17.5). Stored on the card
    doc so the Welcome Signal + Interaction Bot can address the agent.
    """
    email = email.lower().strip()
    existing = await find_card_by_email(db, email)

    issued_at = _now()
    expires_at = issued_at + timedelta(hours=ACCRED_TTL_HOURS)

    if existing:
        accreditation = existing["accreditation_number"]
        display_name = existing.get("display_name") or display_name or _derive_display_name(email)
        doc_id = existing["_id"]
    else:
        accreditation = generate_accreditation_number()
        display_name = display_name or _derive_display_name(email)
        doc_id = str(uuid.uuid4())

    output_path = _ensure_cards_dir() / f"{accreditation}.png"
    qr_payload = (
        f"{base_url.rstrip('/')}/classified-vault?code={accreditation}"
        if base_url
        else None
    )
    render_card(
        display_name=display_name,
        accreditation_number=accreditation,
        issued_at=issued_at,
        expires_at=expires_at,
        output_path=output_path,
        qr_payload=qr_payload,
    )

    # Normalise x_handle: strip leading @ and whitespace; preserve None
    # when caller didn't pass anything so we don't overwrite a previously
    # stored value with null on a refresh.
    x_handle_clean: Optional[str] = None
    if x_handle is not None:
        s = str(x_handle).strip().lstrip("@")
        x_handle_clean = s or None

    update_doc: Dict[str, Any] = {
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
    if x_handle_clean is not None:
        update_doc["x_handle"] = x_handle_clean

    # Upsert
    await db.access_cards.update_one(
        {"_id": doc_id},
        {"$set": update_doc},
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
