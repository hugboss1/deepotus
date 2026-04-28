"""V5 — Best of both worlds:
  • razor-sharp ΔΣ monogram engraving (like Round 3, before the transparency
    refactor diluted the focal detail), and
  • clean alpha-channel transparent PNG (like Round 4, so the coin sits on
    the Tokenomics donut without a black halo).

The Round 4 prompt over-emphasised "transparent background" so heavily that
Nano Banana spent its attention budget on the alpha layer instead of the
Δ/Σ glyph, producing a softer engraving than Round 3. This script flips
the priority: the monogram description is front-loaded with explicit
sharpness directives, and the transparent background is treated as a
single concise post-instruction.
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

from core.llm_compat import LlmChat, UserMessage

OUT_DIR = Path("/app/frontend/public")
KEY = os.environ.get("EMERGENT_LLM_KEY")
if not KEY:
    print("EMERGENT_LLM_KEY missing", file=sys.stderr)
    sys.exit(1)

MODEL_PROVIDER = "gemini"
MODEL_NAME = "gemini-3.1-flash-image-preview"

PROMPT = (
    # ---- Headline subject ----
    "Numismatic studio photograph, SQUARE 1:1 format, of a single luxury "
    "collector GOLD MEDALLION designed for the $DEEPOTUS cryptocurrency. "
    "The coin is photographed perfectly FLAT, top-down, frontal — zero "
    "perspective, axis aligned with the camera. The coin fills ~92% of "
    "the frame, perfectly centered. "
    "\n\n"
    # ---- Focal point: the Δ/Σ monogram (super-detailed, front-loaded) ----
    "PRIMARY FOCAL POINT — the obverse engraving: at the exact geometric "
    "center of the coin, a single iconic MONOGRAM GLYPH combining the "
    "Greek capital letters DELTA (Δ) and SIGMA (Σ), fused into one "
    "instantly recognizable cryptocurrency ticker mark (think of how "
    "Ethereum's diamond Ξ or Ripple's X works). Construction: the Δ "
    "(equilateral triangle, pointed top) sits INSIDE the negative space "
    "of the Σ (Greek 'M-on-its-side' character with two horizontal arms), "
    "both glyphs sharing the SAME vertical axis. Sharp 60° corners on the "
    "Δ, crisp serif terminals on the Σ. The monogram is DEEPLY STRUCK in "
    "raised relief — clearly stamped into the gold with razor-sharp edges, "
    "well-defined facets catching the studio light, deep recessed shadows "
    "between the two glyphs that emphasise the engraving depth. "
    "Engraving must be UNAMBIGUOUSLY READABLE at any zoom level. The "
    "monogram occupies ~38% of the coin's diameter, dominating the design. "
    "\n\n"
    # ---- Secondary engraving: rim text ----
    "Surrounding rim engraving (separate from the central monogram): "
    "circling the coin's inner ring in classic raised serif uppercase "
    "letters, 'Ξ$DEEPOTUSΞ' arching across the TOP, 'PROTOCOL ΔΣ' "
    "arching across the BOTTOM. A small five-pointed star separator at "
    "9 o'clock and another at 3 o'clock. Dentilated outer rim (tiny tooth "
    "pattern), inner beaded circle just outside the rim text. "
    "\n\n"
    # ---- Material / lighting ----
    "Material: rich warm 24-karat yellow gold with a brilliant mirror "
    "finish on the flat fields, brushed matte texture inside the relief "
    "recesses to create contrast. Subtle scratches and patina on the rim "
    "add a tiny touch of authenticity (do NOT overdo it). Studio lighting: "
    "soft 45° key light from upper-left producing crisp specular "
    "highlights on the monogram's edges, gentle fill from the right. "
    "Self-cast shadows live INSIDE the engravings (not under the coin). "
    "\n\n"
    # ---- Background: concise, single instruction ----
    "BACKGROUND: pure transparent PNG (RGBA), full alpha channel zeroed "
    "outside the coin's circular silhouette. The coin is a clean cutout — "
    "no rectangle, no halo, no glow, no drop-shadow on the ground. The "
    "circular medallion is the ONLY opaque pixel in the output. "
    "\n\n"
    # ---- Negative directives ----
    "Forbidden elements: no hands, no fingers, no props, no table, no "
    "text overlay, no UI, no watermark, no signature, no QR code, no "
    "second coin, no perspective tilt, no DOF blur, no fictional alphabets "
    "(only Greek Δ Σ and Latin uppercase). "
    "\n\n"
    "Goal quality: award-winning numismatic product photography, the kind "
    "you'd see on the cover of a luxury crypto launch deck. Razor-sharp "
    "focus across the entire coin face."
)


async def main():
    chat = LlmChat(
        api_key=KEY,
        # Fresh session — avoids any latent caching from round 4
        session_id="gold_coin_front_v5_sharp_transparent",
        system_message=(
            "You are a world-class numismatic product photographer specializing "
            "in luxury cryptocurrency commemorative coins. Always output a "
            "single PNG with TRUE alpha transparency outside the coin's "
            "circular silhouette. The Greek monogram engraving must be "
            "razor-sharp and unambiguously readable."
        ),
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    _text, images = await chat.send_message_multimodal_response(
        UserMessage(text=PROMPT)
    )

    if not images:
        print("NO_IMAGE returned", file=sys.stderr)
        sys.exit(1)

    img = images[0]
    mime = img.get("mime_type", "")
    raw = base64.b64decode(img["data"])
    out = OUT_DIR / "gold_coin_front.png"
    out.write_bytes(raw)
    print(f"OK: {out} ({out.stat().st_size // 1024} KB, mime={mime})")


if __name__ == "__main__":
    asyncio.run(main())
