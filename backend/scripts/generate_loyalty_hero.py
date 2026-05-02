"""One-shot script — generate the Loyalty email hero illustration via
OpenAI gpt-image-1 (through the Emergent image proxy) and save it to
``backend/static/loyalty_hero.jpg``.

Run locally with:

    cd /app/backend && python3 scripts/generate_loyalty_hero.py

Environment:
    * Reads the Emergent image key from the Cabinet Vault or env
      (``EMERGENT_LLM_KEY`` / ``EMERGENT_IMAGE_LLM_KEY``).
    * Writes the optimised JPG to ``backend/static/loyalty_hero.jpg``.
    * Also writes a sidecar JSON with the prompt, model, size and hash
      so future regenerations are reproducible.

Why JPG + 960px-wide?
    gpt-image-1 returns PNGs around 1.5–2 MB at 1536×1024. Gmail web +
    Outlook start complaining above ~700 kB (clipping, external-image
    blocks). A 960×540 JPG at q=85 lands around 120–200 kB — sharp
    enough for Retina (the email renders at 640px-wide so we have 1.5×
    headroom for high-density screens) and light enough to not trigger
    image-proxy caches.

Why DO NOT embed the image inline (base64 in the <img src>):
    Same reason — Gmail web strips or truncates inlined base64 past a
    few kB. A hosted JPG served from ``/api/assets/…`` on our own
    backend is the most reliable strategy for Resend deliveries.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from base64 import b64decode
from io import BytesIO

from PIL import Image

# Path shim so running ``python3 scripts/xxx.py`` from /app/backend
# still finds the core modules on sys.path.
HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from core.openai_image_gen import generate_image_openai  # noqa: E402

OUTPUT_DIR = BACKEND_ROOT / "static"
OUTPUT_JPG = OUTPUT_DIR / "loyalty_hero.jpg"
OUTPUT_META = OUTPUT_DIR / "loyalty_hero.meta.json"

#: Target dimensions — email table renders at 640px-wide on desktop
#: clients, so 960×540 provides 1.5× Retina headroom while keeping
#: file size bounded.
TARGET_WIDTH = 960
TARGET_HEIGHT = 540
JPG_QUALITY = 85  # sweet spot for photographic content, ~140 kB typical


def _optimise(raw_png: bytes) -> tuple[bytes, dict]:
    """Resize + convert to JPG. Returns (bytes, diagnostics)."""
    img = Image.open(BytesIO(raw_png))
    orig_w, orig_h = img.size
    # Use a crop-then-resize to guarantee the 16:9 aspect ratio even if
    # the model returned a slightly off ratio (OpenAI rounds to its own
    # allowed sizes like 1536×1024 which is 3:2, not 16:9).
    orig_ratio = orig_w / orig_h
    target_ratio = TARGET_WIDTH / TARGET_HEIGHT
    if orig_ratio > target_ratio:
        # Too wide → crop sides.
        new_w = int(orig_h * target_ratio)
        off = (orig_w - new_w) // 2
        img = img.crop((off, 0, off + new_w, orig_h))
    elif orig_ratio < target_ratio:
        # Too tall → crop top/bottom.
        new_h = int(orig_w / target_ratio)
        off = (orig_h - new_h) // 2
        img = img.crop((0, off, orig_w, off + new_h))
    img = img.convert("RGB")  # JPG doesn't support alpha
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


async def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[loyalty-hero] Generating illustration via gpt-image-1 …")
    hint = (
        "The Deep-State bureau has logged a Level 02 allegiance. "
        "The ledger of the loyal closes. Those who stay are "
        "remembered; those who sell are not."
    )
    try:
        result = await generate_image_openai(
            content_type="loyalty_hero",
            aspect_ratio="16:9",
            text_hint=hint,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[loyalty-hero] FAILED: {exc}", file=sys.stderr)
        return 1

    b64 = result.get("image_base64")
    if not b64:
        print("[loyalty-hero] FAILED: empty image_base64", file=sys.stderr)
        return 2

    raw = b64decode(b64)
    print(f"[loyalty-hero] raw PNG: {len(raw):,} bytes")

    jpg_bytes, opt_meta = _optimise(raw)
    OUTPUT_JPG.write_bytes(jpg_bytes)
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
    OUTPUT_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

    # Also remove any legacy PNG produced by an earlier run so we don't
    # ship duplicate binaries to Render.
    legacy_png = OUTPUT_DIR / "loyalty_hero.png"
    if legacy_png.exists():
        legacy_png.unlink()
        print(f"[loyalty-hero] cleaned legacy {legacy_png.name}")

    print(f"[loyalty-hero] OK → {OUTPUT_JPG}")
    print(f"[loyalty-hero]    size={len(jpg_bytes):,} bytes  sha256={sha}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

