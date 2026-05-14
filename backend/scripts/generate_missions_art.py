"""One-shot generator — Mission dossier illustrations + Bingo Drum.

Renders the 6 mission cards (Sprint 19 Missions Hub) + the Deep State
Bingo Drum centerpiece via gpt-image-1, optimises into WebP + JPG, and
writes them to ``/app/frontend/public/missions/`` so the React side can
consume them through ``<picture><source type=image/webp>``.

Why a one-shot script (and not a runtime endpoint):
    * Image generation costs ~2–3 cents per call. Doing it once at
      design time and committing the outputs to the public folder is
      cheaper, faster (no LCP hit from a cold API call), and survives
      the OpenAI proxy being down.
    * Reproducibility — the prompts are checked in alongside the
      outputs so a future regenerate is one ``python3 …`` away.

Run locally with:

    cd /app/backend && python3 scripts/generate_missions_art.py

Environment:
    * Reads the Emergent image key from ``EMERGENT_LLM_KEY`` /
      ``EMERGENT_IMAGE_LLM_KEY`` (Cabinet Vault fallback handled by
      ``core.prophet_studio.get_emergent_image_llm_key``).
    * Writes optimised WebP + JPG (and a meta JSON) per asset.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from base64 import b64decode
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
sys.path.insert(0, str(BACKEND_ROOT))

from core.prophet_studio import get_emergent_image_llm_key  # noqa: E402

OUTPUT_DIR = Path("/app/frontend/public/missions")
META_PATH = OUTPUT_DIR / "_assets.meta.json"

# ---------------------------------------------------------------------
# Style guide — every prompt inherits this base. Keeps tonal cohesion
# across the 7 outputs (6 cards + 1 bingo drum) so they read as one
# series.
# ---------------------------------------------------------------------
STYLE_BASE = (
    "Deep State Cabinet aesthetic — classified vintage dossier illustration. "
    "Aged sepia parchment with burnt edges and scorch marks. "
    "Subtle scan-line CRT overlay. Faint Matrix-green digital code "
    "pattern showing through behind the parchment. "
    "A small wax seal in amber/bronze in one corner stamped with the "
    "Greek letters ΔΣ. Red neon accents (#FF3B3B) glowing through "
    "cracks, balanced with amber (#F59E0B) candlelight. "
    "Hand-drawn ink-on-paper feel for the central subject, slightly "
    "smudged. Square 1:1 composition, central subject. "
    "NO modern logos, NO readable English words on the parchment, NO "
    "computer-screen UI, NO realistic photographs of people. "
    "Mood: solemn, bureaucratic, occult, secret society."
)

# The 6 missions — each prompt builds on STYLE_BASE then describes the
# unique central subject + an accent color used in the redacted stamp.
MISSION_PROMPTS: Dict[str, str] = {
    "infiltration": (
        f"{STYLE_BASE} CENTRAL SUBJECT: Three hooded silhouettes in long "
        "trench coats walking single-file through a doorway carved with "
        "the ΔΣ symbol, their backs to the viewer. Footprints in ink lead "
        "to the door. A faint AMBER candle glow leaks from inside. The "
        "scene reads as 'recruitment / infiltration'. The wax seal should "
        "be AMBER and feature a stylised eye. Mood: clandestine arrival."
    ),
    "liquidity": (
        f"{STYLE_BASE} CENTRAL SUBJECT: A heavy bronze bank-vault door "
        "half-open, with a stream of OLD COINS (engraved with ΔΣ, not "
        "modern coins) pouring out onto an inked ledger book. The coins "
        "have a faint GREEN-NEON glow on their rims, like radioactive "
        "gold. A quill rests beside the ledger. The wax seal should be "
        "AMBER and feature a balance scale. Mood: cold, mathematical "
        "wealth being weighed."
    ),
    "amplification": (
        f"{STYLE_BASE} CENTRAL SUBJECT: A vintage brass megaphone "
        "(art-deco propaganda poster style) mounted on a wooden pole, "
        "emitting concentric red shock-wave rings that distort the "
        "parchment fibres. A scroll unrolls from the megaphone's bell, "
        "covered in glyphs and ΔΣ marks. Tiny ink crows fly outward "
        "carrying messages. The wax seal should be RED and feature a "
        "lightning bolt. Mood: official Cabinet broadcast."
    ),
    "archive": (
        f"{STYLE_BASE} CENTRAL SUBJECT: A tall wooden filing cabinet, "
        "antique, with brass handles. One drawer is open revealing "
        "stacked manila folders stamped CONFIDENTIEL (in red ink, "
        "partially redacted with black bars). A 1940s typewriter sits "
        "on top, paper half-fed. The ΔΣ symbol is carved into the side "
        "of the cabinet. The wax seal should be CYAN-TINTED AMBER and "
        "feature a filing cabinet silhouette. Mood: bureaucratic "
        "archive of secrets."
    ),
    "signal": (
        f"{STYLE_BASE} CENTRAL SUBJECT: A tall vintage radio antenna "
        "tower (1920s-style steel lattice) on a foggy hill, emitting "
        "concentric pulse rings of VIOLET light. The rings carry "
        "Morse-code dashes. The base of the tower has a guard hut "
        "marked with the ΔΣ symbol. Tiny silhouettes of citizens look "
        "up toward the signal. The wax seal should be VIOLET-TINTED "
        "AMBER. Mood: surveillance broadcast, the Cabinet listening."
    ),
    "future_06": (
        f"{STYLE_BASE} CENTRAL SUBJECT: A black manila dossier folder "
        "lying flat on the parchment, completely sealed with red wax "
        "and a chain padlock. A diagonal red ink stamp reads "
        "'CLASSIFIED'. Every label on the folder is REDACTED with thick "
        "black bars. A trace of RED neon glow leaks out from under the "
        "folder edges as if something inside is alive. The wax seal "
        "should be DARK RED with a skull-and-key motif. Mood: a sealed "
        "fate, anticipation, do-not-open."
    ),
}

# The bingo drum — generated separately because it gets a wider 16:9
# format and is the only "mechanism" illustration in the series.
BINGO_PROMPT = (
    "Deep State Cabinet aesthetic — vintage illustration. "
    "CENTRAL SUBJECT: A large antique steampunk BINGO DRUM cage, "
    "made of riveted brass and dark wood, mounted on a swivel crank. "
    "Inside the wire cage, dozens of antique BRONZE COINS (each "
    "engraved with the ΔΣ symbol) are mid-tumble — frozen in motion "
    "as if the drum is being cranked. A pile of selected coins sits "
    "on a velvet tray below the chute, each glowing faintly. "
    "The drum's brass frame is decorated with engraved laurel "
    "wreaths and a small plate that reads 'EXTRACTION'. "
    "Behind the drum, faint Matrix-green digital code scrolls down a "
    "smoky red-neon backdrop. Subtle scan-line CRT overlay. "
    "Aged sepia parchment foreground with burnt edges. Red neon "
    "accents (#FF3B3B) and amber candlelight (#F59E0B). "
    "Hand-drawn ink-on-paper feel for the drum's linework. "
    "16:9 cinematic composition, drum centered, leaving space for "
    "text overlay at the bottom. "
    "NO modern logos, NO readable English words on the parchment, "
    "NO computer screens, NO realistic photographs of people. "
    "Mood: a Cabinet ritual mid-ceremony, the random selection of "
    "the chosen few."
)


async def _generate_one(*, prompt: str, size: str, key: str) -> bytes:
    """Single image generation call. Returns raw PNG bytes.

    Isolated so we can ``gather`` them concurrently. Each call is
    independent (no shared client state) — the SDK creates an HTTP
    client per call internally.

    Note: ``size`` is accepted for forward-compat but currently
    ignored — the Emergent OpenAI proxy doesn't surface the kwarg,
    so the SDK returns a default 1024×1024 PNG which we crop/resize
    downstream when a different aspect ratio is needed.
    """
    del size  # not yet supported via the Emergent proxy SDK
    from emergentintegrations.llm.openai.image_generation import (  # type: ignore[import-not-found]
        OpenAIImageGeneration,
    )
    gen = OpenAIImageGeneration(api_key=key)
    images = await gen.generate_images(
        prompt=prompt,
        model="gpt-image-1",
        number_of_images=1,
    )
    if not images:
        raise RuntimeError("empty image list from gpt-image-1")
    raw = images[0]
    # The SDK returns either raw bytes or a dict — defend against both.
    if isinstance(raw, bytes):
        return raw
    if isinstance(raw, dict):
        b64 = raw.get("b64_json") or raw.get("image_base64")
        if not b64:
            raise RuntimeError(f"unexpected image payload keys: {list(raw)}")
        return b64decode(b64)
    raise RuntimeError(f"unexpected image type: {type(raw).__name__}")


def _save_optimised(
    raw_png: bytes,
    *,
    basename: str,
    max_dim: int = 768,
    target_ratio: Optional[float] = None,
) -> Dict[str, int]:
    """Resize + write WebP + JPG. Returns size diagnostics.

    When ``target_ratio`` is set (e.g. 16/9 for the bingo drum), we
    center-crop the source before resizing so the output has the
    requested aspect even though gpt-image-1 returns a 1024×1024
    square.
    """
    img = Image.open(BytesIO(raw_png))
    orig_w, orig_h = img.size

    # Optional aspect-ratio crop — same algorithm as the loyalty hero
    # script. Applied first so the resize step downstream operates on
    # the already-correct ratio.
    if target_ratio is not None:
        cur_ratio = orig_w / orig_h
        if cur_ratio > target_ratio:
            # Too wide → crop sides
            new_w = int(orig_h * target_ratio)
            off = (orig_w - new_w) // 2
            img = img.crop((off, 0, off + new_w, orig_h))
        elif cur_ratio < target_ratio:
            # Too tall → crop top/bottom
            new_h = int(orig_w / target_ratio)
            off = (orig_h - new_h) // 2
            img = img.crop((0, off, orig_w, off + new_h))

    # Cap the longest edge at ``max_dim`` to keep network weight sane.
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    img = img.convert("RGB")

    webp_path = OUTPUT_DIR / f"{basename}.webp"
    jpg_path = OUTPUT_DIR / f"{basename}.jpg"
    img.save(webp_path, "WEBP", quality=82, method=6)
    img.save(jpg_path, "JPEG", quality=86, optimize=True, progressive=True)
    return {
        "width": img.width,
        "height": img.height,
        "webp_bytes": webp_path.stat().st_size,
        "jpg_bytes": jpg_path.stat().st_size,
    }


async def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    key = await get_emergent_image_llm_key()
    if not key:
        print("[missions-art] No Emergent image key configured.", file=sys.stderr)
        return 1

    targets: List[Dict[str, str]] = []
    for slug, prompt in MISSION_PROMPTS.items():
        targets.append({"basename": f"mission_{slug}", "prompt": prompt, "size": "1024x1024"})
    targets.append({"basename": "bingo_drum", "prompt": BINGO_PROMPT, "size": "1536x1024"})

    print(f"[missions-art] Generating {len(targets)} illustrations in parallel …")
    print(f"[missions-art] Output directory: {OUTPUT_DIR}")

    async def _one(t: Dict[str, str]) -> Optional[Dict[str, object]]:
        bn = t["basename"]
        try:
            raw = await _generate_one(prompt=t["prompt"], size=t["size"], key=key)
        except Exception as exc:  # noqa: BLE001
            print(f"[missions-art] FAIL {bn}: {exc}", file=sys.stderr)
            return None
        # Hash the raw bytes for the meta sidecar — handy when an
        # operator wants to confirm "nothing changed" without diffing
        # binary blobs.
        h = hashlib.sha256(raw).hexdigest()[:16]
        # Mission cards = 768 px max edge (rendered at ~340 px).
        # Bingo drum = 1280 px max edge, 16:9 cropped (hero strip).
        max_dim = 1280 if bn == "bingo_drum" else 768
        target_ratio: Optional[float] = (16 / 9) if bn == "bingo_drum" else None
        sizes = _save_optimised(
            raw, basename=bn, max_dim=max_dim, target_ratio=target_ratio,
        )
        print(
            f"[missions-art] OK   {bn}: "
            f"webp={sizes['webp_bytes']/1024:.0f}KB "
            f"jpg={sizes['jpg_bytes']/1024:.0f}KB "
            f"{sizes['width']}x{sizes['height']}",
        )
        return {
            "basename": bn,
            "prompt_sha256": hashlib.sha256(t["prompt"].encode()).hexdigest()[:16],
            "raw_sha256": h,
            "raw_bytes": len(raw),
            **sizes,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # Concurrent generation — gpt-image-1 handles ~5 parallel calls
    # comfortably on the Emergent proxy. With 7 targets we run them all
    # at once; if rate-limits bite, the failed ones surface in the
    # logs and can be re-run individually.
    results = await asyncio.gather(*[_one(t) for t in targets])
    ok_results = [r for r in results if r is not None]

    # Persist meta sidecar — single JSON, append-only across runs.
    meta_blob = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "gpt-image-1",
        "count": len(ok_results),
        "assets": ok_results,
    }
    META_PATH.write_text(json.dumps(meta_blob, indent=2))
    print(
        f"[missions-art] Done. Wrote {len(ok_results)}/{len(targets)} assets "
        f"to {OUTPUT_DIR}.",
    )
    print(f"[missions-art] Meta: {META_PATH}")
    return 0 if len(ok_results) == len(targets) else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
