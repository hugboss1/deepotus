"""OpenAI image generation wrapper (gpt-image-1) — alternate provider for the Bots preview UI.

Why this exists
---------------
The default image provider is Gemini Nano Banana (fast, free, handled
in ``prophet_studio.generate_image``). This module adds OpenAI's
``gpt-image-1`` as an on-demand "variant" path so the admin can
compare interpretations side-by-side without committing the heavier
model as the default.

Design choices
--------------
* **Same public contract as ``prophet_studio.generate_image``** so
  ``routers/bots.py`` can dispatch between the two without any shape
  rewriting downstream. Output dict matches ``GeneratedImage`` in
  ``routers/bots.py`` exactly.
* **Prompt reuse**: we call ``prophet_studio._build_image_prompt``
  unchanged so the STYLE brief (Matrix-green palette, ΔΣ watermark,
  hard rules, etc.) stays consistent across both providers.
* **Aspect-ratio mapping**: OpenAI doesn't accept the ``16:9`` etc.
  strings — it wants explicit pixel sizes from a restricted set. We
  map the public-facing ratios to the closest supported size.
* **Key sourcing**: reuses ``get_emergent_image_llm_key`` (same key
  the Nano Banana path already uses) so there's a single place to
  rotate the secret. The OpenAI proxy backed by EMERGENT_LLM_KEY
  accepts this key natively.
* **Failure mode**: raises ``RuntimeError`` with a ``image_llm_failure:``
  prefix so ``routers/bots.py`` can surface the reason in the existing
  ``image_error`` response field — no new error plumbing required.

Performance note
----------------
OpenAI image calls can take up to ~60 s (vs ~10 s for Gemini). The
caller (admin UI) should set a generous timeout; the router enforces
90 s when ``image_provider == "openai"``.
"""

from __future__ import annotations

import base64
import logging
from typing import Any, Dict, Optional

from core.prophet_studio import (
    VALID_CONTENT_TYPES,
    _build_image_prompt,
    get_emergent_image_llm_key,
    get_emergent_llm_key,
)

logger = logging.getLogger("deepotus.openai_image_gen")

# ---------------------------------------------------------------------
# Provider metadata
# ---------------------------------------------------------------------

#: Model identifier accepted by the Emergent proxy for OpenAI image
#: generation. ``gpt-image-1`` is OpenAI's current universal model
#: exposed through the proxy; per the Emergent playbook this is the
#: only OpenAI image model routed today (DALL-E 3 is also available
#: but explicitly deprecated).
OPENAI_IMAGE_MODEL = "gpt-image-1"
OPENAI_IMAGE_PROVIDER = "openai"

#: Mapping from the public aspect_ratio strings (shared with Gemini
#: path) to OpenAI's accepted pixel sizes. OpenAI gpt-image-1 accepts
#: a small fixed set; we pick the closest match per ratio.
#:
#: * 1:1   → 1024×1024 (true square)
#: * 3:4   → 1024×1536 (portrait — closest match)
#: * 16:9  → 1536×1024 (landscape — closest match; true 16:9 isn't
#:            natively supported, 1536×1024 = 3:2 is the accepted
#:            landscape format)
_ASPECT_TO_SIZE = {
    "1:1": "1024x1024",
    "3:4": "1024x1536",
    "16:9": "1536x1024",
}


async def generate_image_openai(
    content_type: str,
    *,
    aspect_ratio: str = "16:9",
    text_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a single illustration via OpenAI gpt-image-1.

    Args:
        content_type: must be one of ``VALID_CONTENT_TYPES``
            (``market_commentary`` / ``prophecy`` / ``kol_reply`` / …).
        aspect_ratio: ``"16:9"`` (default), ``"3:4"`` or ``"1:1"``.
            Mapped internally to the closest pixel size OpenAI accepts.
        text_hint: optional narrative snippet to inspire the scene
            (typically the ``content_en`` returned by ``generate_post``).

    Returns:
        Dict with the same shape as ``prophet_studio.generate_image``::

            {
              "content_type": str, "aspect_ratio": str,
              "provider": "openai", "model": "gpt-image-1",
              "prompt": str, "mime_type": "image/png",
              "image_base64": str, "size_bytes": int,
            }

    Raises:
        ValueError: unknown ``content_type`` or ``aspect_ratio``.
        RuntimeError: OpenAI / proxy call failure, or empty payload.
    """
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(f"unknown content_type={content_type}")
    if aspect_ratio not in _ASPECT_TO_SIZE:
        raise ValueError(
            f"unsupported aspect_ratio={aspect_ratio}. "
            f"Expected one of {sorted(_ASPECT_TO_SIZE.keys())}."
        )

    size = _ASPECT_TO_SIZE[aspect_ratio]
    image_key = await get_emergent_image_llm_key()
    if not image_key:
        raise RuntimeError("no_image_llm_key_configured")

    prompt = _build_image_prompt(content_type, aspect_ratio, text_hint=text_hint)

    # Lazy import so the module stays importable from one-shot scripts
    # that haven't installed emergentintegrations yet. Any ImportError
    # surfaces as a clean ``image_llm_failure`` to the caller.
    try:
        from emergentintegrations.llm.openai.image_generation import (  # type: ignore[import-not-found]
            OpenAIImageGeneration,
        )
    except ImportError as exc:
        raise RuntimeError(
            f"image_llm_failure: emergentintegrations missing — {exc}"
        ) from exc

    try:
        image_gen = OpenAIImageGeneration(api_key=image_key)
        # The Emergent playbook's basic_usage only shows `prompt`,
        # `model`, and `number_of_images`. We pass `size` in addition
        # since gpt-image-1 accepts it natively via the proxy; if the
        # proxy rejects the kwarg at runtime, the except branch below
        # will surface the error with a clear prefix.
        images = await image_gen.generate_images(
            prompt=prompt,
            model=OPENAI_IMAGE_MODEL,
            number_of_images=1,
            size=size,
        )
    except TypeError:
        # Fallback path: older SDK that doesn't accept `size=` kwarg.
        # Retry without it so we at least get a square 1024×1024 PNG
        # rather than failing outright. Downstream still gets the
        # expected response shape.
        logger.warning(
            "[openai_image_gen] SDK rejected size kwarg — retrying default"
        )
        try:
            images = await image_gen.generate_images(
                prompt=prompt,
                model=OPENAI_IMAGE_MODEL,
                number_of_images=1,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("[openai_image_gen] image gen failed (fallback)")
            raise RuntimeError(f"image_llm_failure: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("[openai_image_gen] image gen failed")
        raise RuntimeError(f"image_llm_failure: {exc}") from exc

    if not images:
        raise RuntimeError("image_llm_no_output")

    # OpenAIImageGeneration returns a list of raw BYTES per the Emergent
    # playbook (unlike Gemini's multimodal shape which returns a list of
    # dicts). We base64-encode here to match the public contract.
    first = images[0]
    if not isinstance(first, (bytes, bytearray)):
        raise RuntimeError(
            f"image_llm_failure: unexpected image type {type(first).__name__}"
        )
    image_base64 = base64.b64encode(bytes(first)).decode("ascii")
    size_bytes = len(first)

    # Diagnostic: confirm whether the dedicated image key is distinct
    # from the base text-LLM key (useful when debugging quota issues).
    base_key_for_log = await get_emergent_llm_key()
    logger.info(
        "[openai_image_gen] image generated type=%s ratio=%s size=%s (%d KB, dedicated_key=%s)",
        content_type,
        aspect_ratio,
        size,
        size_bytes // 1024,
        bool(image_key and image_key != base_key_for_log),
    )

    return {
        "content_type": content_type,
        "aspect_ratio": aspect_ratio,
        "provider": OPENAI_IMAGE_PROVIDER,
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "mime_type": "image/png",
        "image_base64": image_base64,
        "size_bytes": size_bytes,
    }
