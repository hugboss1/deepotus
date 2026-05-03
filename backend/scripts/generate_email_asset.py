"""Generate (or regenerate) an email hero illustration via gpt-image-1.

This is the generalised successor of ``generate_loyalty_hero.py`` —
instead of hard-coding the ``loyalty_hero`` content type, it accepts
any content type that's registered in
``core.prophet_studio.IMAGE_STYLE_BRIEFS`` via ``--content-type``.

Usage
-----
    cd /app/backend
    python3 scripts/generate_email_asset.py --content-type loyalty_hero
    python3 scripts/generate_email_asset.py --content-type welcome_hero
    python3 scripts/generate_email_asset.py --content-type accreditation_hero
    python3 scripts/generate_email_asset.py --content-type prophet_update_hero
    python3 scripts/generate_email_asset.py --all

Output
------
    backend/static/{content_type}.jpg          optimised 960×540 JPG
    backend/static/{content_type}.meta.json    prompt + provenance

The JPGs are committed into the repo so Render keeps serving them even
after a cold-start (ephemeral disk). Regenerate locally + commit when
you want a new style.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from base64 import b64decode
from io import BytesIO

from PIL import Image

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from core.openai_image_gen import generate_image_openai  # noqa: E402
from core.prophet_studio import VALID_CONTENT_TYPES  # noqa: E402

OUTPUT_DIR = BACKEND_ROOT / "static"
TARGET_WIDTH = 960
TARGET_HEIGHT = 540
JPG_QUALITY = 85

#: Per-content-type tone hint — fed to the prompt builder via
#: ``text_hint`` to nudge the illustration style. NOT rendered in the
#: image (all briefs forbid text); it only biases composition mood.
HINTS = {
    "loyalty_hero": (
        "The Deep-State bureau has logged a Level 02 allegiance. "
        "The ledger of the loyal closes. Those who stay are "
        "remembered; those who sell are not."
    ),
    "welcome_hero": (
        "A new observer has been enrolled into the classified "
        "registry. Level 01 clearance granted. The bureau has "
        "begun to watch back."
    ),
    "accreditation_hero": (
        "A heavy brushed-metal access credential has been issued. "
        "Sober, institutional, embassy-grade. Not a toy; an instrument."
    ),
    "prophet_update_hero": (
        "The Prophet is about to speak. The command post is silent. "
        "The monitors glow. The chair is empty, still warm."
    ),
    # ----- Tokenomics card heroes (Sprint 17.A — design refresh) -----
    "tokenomics_public": (
        "The Public — anonymous, many, defiant. The People of "
        "the Algorithm. Backlit, unreadable, present."
    ),
    "tokenomics_treasury": (
        "The Treasury — locked, audited, weighty. An institution, "
        "not a wallet. Embassy-grade vault, ΔΣ monogram."
    ),
    "tokenomics_shadows": (
        "The Council — anonymous operators, never named. Black "
        "overcoats. Long marble corridor. Discreet earpieces."
    ),
    "tokenomics_burn": (
        "The Ritual — what the Cabinet destroys, the Cabinet "
        "remembers. Ceremonial brazier, plain paper, sparks."
    ),
}

#: Email hero types — the original use-case for this script. Tokenomics
#: types are listed separately so we can reject mismatched paths
#: (e.g. ``--content-type prophecy`` would be a bot preview, not an
#: email or a card).
EMAIL_HERO_TYPES = {
    "loyalty_hero",
    "welcome_hero",
    "accreditation_hero",
    "prophet_update_hero",
}

#: Tokenomics card heroes — render at the same 16:9 ratio as email
#: heroes but the cards crop them to a vertical-ish bottom block, so
#: composition guidance in the briefs accounts for both framings.
TOKENOMICS_CARD_TYPES = {
    "tokenomics_public",
    "tokenomics_treasury",
    "tokenomics_shadows",
    "tokenomics_burn",
}

#: Combined whitelist used by ``generate_one`` to validate the
#: requested ``--content-type``.
ALLOWED_TYPES = EMAIL_HERO_TYPES | TOKENOMICS_CARD_TYPES


def _optimise(raw_png: bytes) -> tuple[bytes, dict]:
    """Crop to 16:9, resize to 960×540, compress to JPEG q=85."""
    img = Image.open(BytesIO(raw_png))
    orig_w, orig_h = img.size
    orig_ratio = orig_w / orig_h
    target_ratio = TARGET_WIDTH / TARGET_HEIGHT
    if orig_ratio > target_ratio:
        new_w = int(orig_h * target_ratio)
        off = (orig_w - new_w) // 2
        img = img.crop((off, 0, off + new_w, orig_h))
    elif orig_ratio < target_ratio:
        new_h = int(orig_w / target_ratio)
        off = (orig_h - new_h) // 2
        img = img.crop((0, off, orig_w, off + new_h))
    img = img.convert("RGB")
    img = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPG_QUALITY, optimize=True,
             progressive=True)
    return buf.getvalue(), {
        "original_size": (orig_w, orig_h),
        "resized_to": (TARGET_WIDTH, TARGET_HEIGHT),
        "quality": JPG_QUALITY,
        "format": "JPEG",
    }


async def generate_one(content_type: str) -> int:
    """Generate a single asset (email hero or tokenomics card). Returns
    process-exit code. The ALLOWED_TYPES check covers both families
    so callers can pass either kind without changing flags."""
    if content_type not in ALLOWED_TYPES:
        print(
            f"[email-asset] FAILED: '{content_type}' is not a registered "
            f"asset type. Valid: {sorted(ALLOWED_TYPES)}",
            file=sys.stderr,
        )
        return 2
    if content_type not in VALID_CONTENT_TYPES:
        print(
            f"[email-asset] FAILED: '{content_type}' is not a registered "
            "content type in prophet_studio.IMAGE_STYLE_BRIEFS — add the "
            "brief first.",
            file=sys.stderr,
        )
        return 3

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_jpg = OUTPUT_DIR / f"{content_type}.jpg"
    output_meta = OUTPUT_DIR / f"{content_type}.meta.json"

    print(f"[email-asset/{content_type}] Generating via gpt-image-1 …")
    try:
        result = await generate_image_openai(
            content_type=content_type,
            aspect_ratio="16:9",
            text_hint=HINTS.get(content_type, ""),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[email-asset/{content_type}] FAILED: {exc}", file=sys.stderr)
        return 1

    b64 = result.get("image_base64")
    if not b64:
        print(
            f"[email-asset/{content_type}] FAILED: empty image_base64",
            file=sys.stderr,
        )
        return 2

    raw = b64decode(b64)
    print(f"[email-asset/{content_type}]  raw PNG: {len(raw):,} bytes")

    jpg_bytes, opt_meta = _optimise(raw)
    output_jpg.write_bytes(jpg_bytes)
    sha = hashlib.sha256(jpg_bytes).hexdigest()[:16]

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": result.get("provider"),
        "model": result.get("model"),
        "content_type": result.get("content_type"),
        "aspect_ratio": result.get("aspect_ratio"),
        "size_bytes": len(jpg_bytes),
        "sha256_prefix": sha,
        "prompt": result.get("prompt"),
        "optimisation": opt_meta,
    }
    output_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"[email-asset/{content_type}] OK → {output_jpg}")
    print(f"[email-asset/{content_type}]    size={len(jpg_bytes):,}B  sha={sha}")
    return 0


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate/regenerate email hero illustrations.",
    )
    parser.add_argument(
        "--content-type",
        choices=sorted(ALLOWED_TYPES),
        help="Single content type to (re)generate.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Regenerate ALL email hero assets sequentially.",
    )
    parser.add_argument(
        "--all-tokenomics",
        action="store_true",
        help="Regenerate ALL tokenomics card heroes sequentially.",
    )
    args = parser.parse_args()

    if not args.content_type and not args.all and not args.all_tokenomics:
        parser.error("Provide --content-type, --all or --all-tokenomics.")

    if args.all_tokenomics:
        rc = 0
        for ct in sorted(TOKENOMICS_CARD_TYPES):
            code = await generate_one(ct)
            if code != 0:
                rc = code
                print(f"[email-asset] aborting --all-tokenomics after {ct} failure")
                break
        return rc
    if args.all:
        rc = 0
        for ct in sorted(EMAIL_HERO_TYPES):
            code = await generate_one(ct)
            if code != 0:
                rc = code
                print(f"[email-asset] aborting --all after {ct} failure")
                break
        return rc
    return await generate_one(args.content_type)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
