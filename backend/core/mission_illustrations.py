"""Mission illustrations (Sprint 21).

Generates per-mission cover artwork via OpenAI ``gpt-image-1`` (through
the Emergent LLM proxy, same key used elsewhere). The generated PNG is
saved into the public Vercel-served folder
``frontend/public/assets/missions-email/{mission_id}.png`` so emails
can reference it with a stable, CDN-cached URL
(``${PUBLIC_BASE_URL}/assets/missions-email/{mission_id}.png``).

Prompt brief
------------
Every illustration must:
  * Stay in the **DEEPOTUS tech-noir universe** (deep navy + amber +
    cyan-teal accents, Matrix grain, IBM Plex Mono UI hints).
  * Convey the **mission theme** unambiguously through symbolism
    (no text labels — we add those in the email HTML).
  * Land at **1024×1024** (square) so it crops cleanly into both
    desktop and mobile email clients.

The ``MISSION_PROMPTS`` table holds one prompt per mission. The admin
Command Center exposes a "Regenerate" button that calls this module
async; failures surface clearly so the editor can retry.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from core.config import logger

# ---------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------
FRONTEND_PUBLIC = Path("/app/frontend/public")
ASSET_SUBDIR = "assets/missions-email"
ASSET_DIR = FRONTEND_PUBLIC / ASSET_SUBDIR

# Make the directory on import — idempotent + cheap.
try:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    logging.exception("[mission_illustrations] could not create asset dir")

# ---------------------------------------------------------------------
# Prompt catalogue — one entry per mission_id.
# ---------------------------------------------------------------------
_BASE_STYLE = (
    "DEEPOTUS tech-noir aesthetic. Deep navy/black background (#0B0E14), "
    "warm amber highlights (#F59E0B), cyan-teal accents (#2DD4BF). "
    "Cinematic light wash, 35mm grain, subtle Matrix scanlines. "
    "Geometric brutalist composition, isometric where relevant, IBM Plex Mono "
    "micro-grid hints in the background. NO TEXT, NO LOGOS, NO WATERMARKS. "
    "Mood: classified intelligence dossier crossed with cyberpunk noir, slow and premium."
)

MISSION_PROMPTS: Dict[str, str] = {
    "infiltration": (
        "A masked silhouette stepping through a digital portal made of pure cyan light, "
        "binary glyphs streaming around its feet, looking back over its shoulder. "
        "Single amber lamp glowing in the upper-right corner. "
        + _BASE_STYLE
    ),
    "liquidity": (
        "A liquid mercury pool reflecting cyan constellations, an amber droplet rising in slow motion, "
        "glowing Greek deltas (Δ) and sigmas (Σ) floating just below the surface. "
        "Faint financial-terminal grid in the deep background. "
        + _BASE_STYLE
    ),
    "amplification": (
        "A black brutalist broadcasting tower with three concentric amber halos pulsing outward, "
        "thin cyan signal wires fanning into the night sky, distant Manhattan-like silhouettes below. "
        + _BASE_STYLE
    ),
    "archive": (
        "A vault of leather-bound dossier boxes on cyan-glowing shelves, one box ajar revealing a single "
        "folded paper sealed with an amber wax ΔΣ emblem. Soft library lamp lighting, motes of dust. "
        + _BASE_STYLE
    ),
    "signal": (
        "A bird's-eye view of a desk with a tactical map, a cyan signal flare burning in the centre, "
        "amber-coordinate pins forming a constellation pattern, hand of a Cabinet operative reaching in "
        "from the edge of the frame. "
        + _BASE_STYLE
    ),
    "future_06": (
        "A redacted classified envelope with thick amber bars over the title, deep navy felt background, "
        "a cyan wax seal hanging from a delta-sigma sigil ribbon, faint scan lines crossing diagonally. "
        + _BASE_STYLE
    ),
}


def get_mission_image_path(mission_id: str) -> Path:
    """Return the absolute Path of the generated image for ``mission_id``."""
    return ASSET_DIR / f"{mission_id}.png"


def get_mission_image_public_url(mission_id: str, base_url: str = "") -> str:
    """Compose the public URL of an illustration.

    ``base_url`` should be ``PUBLIC_BASE_URL`` (e.g. https://deepotus.xyz).
    Falls back to a relative path if base_url is empty.
    """
    rel = f"/{ASSET_SUBDIR}/{mission_id}.png"
    if not base_url:
        return rel
    return f"{base_url.rstrip('/')}{rel}"


def has_mission_image(mission_id: str) -> bool:
    p = get_mission_image_path(mission_id)
    return p.exists() and p.stat().st_size > 0


async def generate_mission_illustration(
    mission_id: str, *, force: bool = False
) -> Dict[str, Any]:
    """Generate (or regenerate) the illustration for ``mission_id``.

    Returns ``{ok, mission_id, path, public_path, size_bytes, regenerated}``.
    Raises ``ValueError`` if ``mission_id`` is unknown.
    Raises ``RuntimeError`` (prefix ``image_llm_failure:``) on provider errors.
    """
    if mission_id not in MISSION_PROMPTS:
        raise ValueError(f"unknown mission_id={mission_id!r}")

    out_path = get_mission_image_path(mission_id)
    if out_path.exists() and not force:
        return {
            "ok": True,
            "mission_id": mission_id,
            "path": str(out_path),
            "public_path": f"/{ASSET_SUBDIR}/{mission_id}.png",
            "size_bytes": out_path.stat().st_size,
            "regenerated": False,
        }

    from core.prophet_studio import get_emergent_image_llm_key

    key = await get_emergent_image_llm_key()
    if not key:
        raise RuntimeError("image_llm_failure: no Emergent image key configured")

    try:
        from emergentintegrations.llm.openai.image_generation import (  # type: ignore[import-not-found]
            OpenAIImageGeneration,
        )
    except ImportError as exc:
        raise RuntimeError(
            f"image_llm_failure: emergentintegrations missing — {exc}"
        ) from exc

    prompt = MISSION_PROMPTS[mission_id]
    image_gen = OpenAIImageGeneration(api_key=key)
    try:
        # 1024x1024 square — best for email viewports.
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1,
            size="1024x1024",
        )
    except TypeError:
        # Older SDK — retry without size= kwarg.
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("[mission_illustrations] gpt-image-1 failed for %s", mission_id)
        raise RuntimeError(f"image_llm_failure: {exc}") from exc

    if not images:
        raise RuntimeError("image_llm_no_output")

    raw = images[0]
    if not isinstance(raw, (bytes, bytearray)):
        # Some SDK versions return base64 strings; handle defensively.
        if isinstance(raw, str):
            try:
                raw = base64.b64decode(raw)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"image_llm_failure: cannot decode output ({exc})") from exc
        else:
            raise RuntimeError(
                f"image_llm_failure: unexpected payload type {type(raw).__name__}"
            )

    out_path.write_bytes(bytes(raw))
    logger.info(
        "[mission_illustrations] generated %s (%d KB) -> %s",
        mission_id, len(raw) // 1024, out_path,
    )
    return {
        "ok": True,
        "mission_id": mission_id,
        "path": str(out_path),
        "public_path": f"/{ASSET_SUBDIR}/{mission_id}.png",
        "size_bytes": len(raw),
        "regenerated": True,
    }


async def list_illustrations() -> Dict[str, Any]:
    """Return a summary of which missions have an illustration on disk."""
    out: Dict[str, Any] = {}
    for mid in MISSION_PROMPTS.keys():
        p = get_mission_image_path(mid)
        if p.exists():
            out[mid] = {
                "present": True,
                "size_bytes": p.stat().st_size,
                "public_path": f"/{ASSET_SUBDIR}/{mid}.png",
            }
        else:
            out[mid] = {
                "present": False,
                "size_bytes": 0,
                "public_path": f"/{ASSET_SUBDIR}/{mid}.png",
            }
    return out


__all__ = [
    "MISSION_PROMPTS",
    "get_mission_image_path",
    "get_mission_image_public_url",
    "has_mission_image",
    "generate_mission_illustration",
    "list_illustrations",
]
