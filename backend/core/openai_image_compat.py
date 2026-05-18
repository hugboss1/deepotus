"""OpenAI image-generation compatibility shim.

Drop-in replacement for
``emergentintegrations.llm.openai.image_generation.OpenAIImageGeneration``.

Why this exists
---------------
Same rationale as :mod:`core.llm_compat`: the original codebase used
the private ``emergentintegrations`` package for ``gpt-image-1`` image
generation. When the project is deployed outside Emergent (Render,
Vercel, Fly, …) that package is not installable from the public PyPI
index, so the ``OpenAIImageGeneration`` import fails outright.

This module preserves the exact public API the rest of the codebase
relies on::

    from core.openai_image_compat import OpenAIImageGeneration

    gen = OpenAIImageGeneration(api_key=...)
    images: list[bytes] = await gen.generate_images(
        prompt=...,
        model="gpt-image-1",
        number_of_images=1,
        size="1024x1024",   # optional
    )

Two routing modes (auto-detected at import time)
------------------------------------------------
**Mode A — Emergent proxy (preferred when available)**
    If ``emergentintegrations.llm.openai.image_generation`` is
    importable (Emergent preview/dev env where the package is
    pre-installed), we re-export the real ``OpenAIImageGeneration``
    class verbatim. The ``EMERGENT_LLM_KEY`` ("sk-emergent-…") then
    works out of the box through the Emergent proxy.

**Mode B — Native OpenAI SDK fallback (Render-compatible)**
    If the import fails, we fall back to a hand-rolled implementation
    that calls the official ``openai`` SDK already pinned in
    ``requirements.txt``. In this mode the ``api_key`` must be a real
    OpenAI key ("sk-…") — either passed explicitly or sourced by the
    caller from ``OPENAI_API_KEY`` / Cabinet Vault before construction.

Output shape parity
-------------------
Both modes return ``list[bytes]`` (raw image bytes, typically PNG) so
``core.openai_image_gen`` and ``scripts/generate_missions_art`` keep
working unchanged regardless of the active mode.

This file has zero hard dependency on the other ``core/*`` modules so
the one-shot ``generate_*.py`` scripts keep working from a
stripped-down environment.
"""

from __future__ import annotations

import base64
import logging
from typing import List, Optional

logger = logging.getLogger("deepotus.openai_image_compat")


# ---------------------------------------------------------------------
# Mode A — Try the real Emergent proxy lib first.
#
# When this import succeeds we re-export the real
# ``OpenAIImageGeneration`` class. EMERGENT_LLM_KEY routing then "just
# works" because the lib internally talks to the Emergent
# LiteLLM-compatible proxy.
# ---------------------------------------------------------------------
try:
    from emergentintegrations.llm.openai.image_generation import (  # type: ignore[import-not-found]
        OpenAIImageGeneration,
    )

    _USING_EMERGENT_PROXY = True
    logger.info(
        "[openai_image_compat] Mode A active — routing through "
        "emergentintegrations proxy (EMERGENT_LLM_KEY-compatible)."
    )
    __all__ = ["OpenAIImageGeneration"]

except ImportError:
    _USING_EMERGENT_PROXY = False
    logger.info(
        "[openai_image_compat] Mode B active — emergentintegrations not "
        "installed, falling back to the native OpenAI SDK "
        "(real OPENAI_API_KEY required)."
    )

    class OpenAIImageGeneration:  # type: ignore[no-redef]
        """Native-SDK equivalent of the Emergent ``OpenAIImageGeneration``.

        Signature-compatible with the original:

            OpenAIImageGeneration(api_key=...)
                .generate_images(prompt=..., model=..., number_of_images=..., size=...)

        Returns a ``list[bytes]`` of raw image data (PNG) so callers
        that already handle the Emergent shape need no changes.
        """

        def __init__(self, api_key: Optional[str] = None, **_kw):
            self._api_key = (api_key or "").strip() or None

        async def generate_images(
            self,
            *,
            prompt: str,
            model: str = "gpt-image-1",
            number_of_images: int = 1,
            size: Optional[str] = None,
        ) -> List[bytes]:
            if not self._api_key:
                raise ValueError(
                    "OpenAIImageGeneration (Mode B): empty api_key. Pass a "
                    "real OpenAI key ('sk-…'), or set OPENAI_API_KEY / store "
                    "it in the Cabinet Vault and resolve it before calling."
                )

            from openai import AsyncOpenAI  # lazy — keeps cold-start light

            client = AsyncOpenAI(api_key=self._api_key)

            kwargs = {
                "model": model,
                "prompt": prompt,
                "n": int(number_of_images or 1),
            }
            if size:
                kwargs["size"] = size

            try:
                resp = await client.images.generate(**kwargs)
            except TypeError:
                # Older/newer SDK that rejects the ``size`` kwarg — retry
                # without it so we still get a (default-size) image
                # rather than failing outright.
                logger.warning(
                    "[openai_image_compat] SDK rejected size kwarg — "
                    "retrying without size"
                )
                kwargs.pop("size", None)
                resp = await client.images.generate(**kwargs)

            data = getattr(resp, "data", None) or []
            out: List[bytes] = []
            for item in data:
                b64 = getattr(item, "b64_json", None)
                if b64:
                    out.append(base64.b64decode(b64))
                    continue
                url = getattr(item, "url", None)
                if url:
                    # Some SDK/model combos return a hosted URL instead
                    # of inline base64 — fetch it so the return shape
                    # stays uniform (raw bytes).
                    import httpx  # lazy

                    async with httpx.AsyncClient(timeout=60) as http:
                        r = await http.get(url)
                        r.raise_for_status()
                        out.append(r.content)
                    continue
                logger.warning(
                    "[openai_image_compat] image item had neither "
                    "b64_json nor url — skipped"
                )

            return out

    __all__ = ["OpenAIImageGeneration"]
