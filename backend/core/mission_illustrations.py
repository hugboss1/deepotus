"""Mission illustrations (Sprint 21 — simplified after Sprint 21.1).

Originally this module generated per-mission cover artwork via
``gpt-image-1``. Following user feedback, we **reuse the tech-noir
illustrations already shipping on the public site** (under
``/missions/mission_{id}.jpg``) instead of generating new ones. The
generation pipeline is intentionally removed to keep behaviour
predictable and free of LLM costs.

The public-facing API stays compatible:

  * ``get_mission_image_public_url(mission_id, base_url)``
        Returns an absolute URL Resend can embed in emails.
  * ``has_mission_image(mission_id)``
        True if the on-disk asset exists (always true for the 6
        canonical missions since the assets ship with the repo).
  * ``list_illustrations()``
        Status dict for the admin Command Center.

The legacy ``generate_mission_illustration(...)`` is kept as a stub
that raises ``RuntimeError`` so any forgotten caller fails loudly
instead of silently consuming an LLM key.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from core.config import logger

# ---------------------------------------------------------------------
# Storage — point at the existing, ready-shipped mission illustrations.
# ---------------------------------------------------------------------
FRONTEND_PUBLIC = Path("/app/frontend/public")
ASSET_SUBDIR = "missions"  # served at /missions/*

#: Canonical mission ids in priority order. The companion artwork is
#: ``mission_{id}.jpg`` (with a ``.webp`` sibling preferred by the
#: browser); emails request the ``.jpg`` flavour for maximum client
#: compatibility (Outlook still chokes on WebP).
MISSION_IDS: tuple[str, ...] = (
    "infiltration",
    "liquidity",
    "amplification",
    "archive",
    "signal",
    "future_06",
)


def get_mission_image_path(mission_id: str) -> Path:
    """Absolute on-disk Path of the public illustration."""
    return FRONTEND_PUBLIC / ASSET_SUBDIR / f"mission_{mission_id}.jpg"


def get_mission_image_public_url(mission_id: str, base_url: str = "") -> str:
    """Compose the public URL of an illustration.

    ``base_url`` should be the absolute origin (e.g. https://deepotus.xyz).
    Falls back to a relative path when ``base_url`` is empty.
    """
    rel = f"/{ASSET_SUBDIR}/mission_{mission_id}.jpg"
    if not base_url:
        return rel
    return f"{base_url.rstrip('/')}{rel}"


def has_mission_image(mission_id: str) -> bool:
    """True if the on-disk asset exists and is non-empty."""
    p = get_mission_image_path(mission_id)
    return p.exists() and p.stat().st_size > 0


async def generate_mission_illustration(
    mission_id: str, *, force: bool = False
) -> Dict[str, Any]:
    """Deprecated — generation removed in favour of bundled assets.

    Raises ``RuntimeError`` so any unintended caller surfaces clearly.
    """
    _ = force  # unused
    raise RuntimeError(
        "mission_illustrations.generate_mission_illustration is disabled — "
        "reuse the bundled artwork at /missions/mission_{id}.jpg instead."
    )


async def list_illustrations() -> Dict[str, Any]:
    """Return per-mission disk status. Used by the admin Command Center
    to show which artwork is bundled (size in bytes + public path)."""
    out: Dict[str, Any] = {}
    for mid in MISSION_IDS:
        p = get_mission_image_path(mid)
        if p.exists():
            out[mid] = {
                "present": True,
                "size_bytes": p.stat().st_size,
                "public_path": f"/{ASSET_SUBDIR}/mission_{mid}.jpg",
                "source": "bundled",
            }
        else:
            out[mid] = {
                "present": False,
                "size_bytes": 0,
                "public_path": f"/{ASSET_SUBDIR}/mission_{mid}.jpg",
                "source": "bundled",
            }
            logging.warning("[mission_illustrations] missing bundled asset: %s", p)
    return out


__all__ = [
    "MISSION_IDS",
    "get_mission_image_path",
    "get_mission_image_public_url",
    "has_mission_image",
    "generate_mission_illustration",  # kept for stub raise
    "list_illustrations",
]
