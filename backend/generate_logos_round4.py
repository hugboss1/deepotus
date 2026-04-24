"""Regenerate gold_coin_front.png with TRANSPARENT background so the coin
blends seamlessly into the Tokenomics donut chart without a visible black
rectangle around it.
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

from emergentintegrations.llm.chat import LlmChat, UserMessage

OUT_DIR = Path("/app/frontend/public")
KEY = os.environ.get("EMERGENT_LLM_KEY")
if not KEY:
    print("EMERGENT_LLM_KEY missing", file=sys.stderr)
    sys.exit(1)

MODEL_PROVIDER = "gemini"
MODEL_NAME = "gemini-3.1-flash-image-preview"

PROMPT = (
    "Ultra-realistic numismatic photography of a LUXURY COLLECTOR GOLD COIN for "
    "$DEEPOTUS cryptocurrency. SQUARE 1:1 format. Perfectly CENTERED, FRONTAL "
    "top-down shot (coin photographed flat, zero perspective). "
    "\n\n"
    "ABSOLUTELY CRITICAL: the background MUST be 100% TRANSPARENT (alpha "
    "channel PNG). NO black backdrop, NO charcoal, NO vignette, NO glow, NO "
    "shadow on the ground, NO color behind the coin. Output the coin as a "
    "CUTOUT — only the round medallion shape is visible, everything else is "
    "fully transparent alpha. The final PNG must be usable as a sticker that "
    "blends into ANY background. "
    "\n\n"
    "The coin itself: a large round polished pure-gold medallion (rich warm "
    "24-karat yellow gold, brilliant reflective finish, mirror-like fields "
    "with deep engraved reliefs). Dentilated classical rim (small teeth "
    "pattern around the edge), inner beaded circle. "
    "\n\n"
    "Struck at the CENTER of the obverse: a single bold MONOGRAM GLYPH "
    "combining the Greek capital letters DELTA (Δ) and SIGMA (Σ), fused into "
    "one unique cryptocurrency ticker mark (like ETH ◆ or XRP X) — the Δ sits "
    "inside the Σ's negative space, sharing a common vertical axis, deeply "
    "engraved in stamped relief. "
    "\n\n"
    "Around the monogram, following the rim in engraved uppercase serif "
    "letters: top arc '$DEEPOTUS', bottom arc 'PROTOCOL ΔΣ'. Tiny star "
    "separators on left and right of rim. "
    "\n\n"
    "Photography quality: razor-sharp focus, soft 45° studio lighting with "
    "subtle rim highlight showing the gold's metallic sheen, self-cast "
    "shadows WITHIN the coin's relief (not under the coin). Coin fills about "
    "92% of the square frame edge-to-edge with a tiny transparent margin. "
    "No hands, no props, no text overlay, no watermark."
)


async def main():
    chat = LlmChat(
        api_key=KEY,
        session_id="gold_coin_front_transparent",
        system_message="You are a world-class numismatic product photographer. Output ONLY the PNG with TRUE alpha transparency.",
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    _text, images = await chat.send_message_multimodal_response(
        UserMessage(text=PROMPT)
    )

    if not images:
        print("NO_IMAGE returned")
        sys.exit(1)

    img = images[0]
    mime = img.get("mime_type", "")
    raw = base64.b64decode(img["data"])
    out = OUT_DIR / "gold_coin_front.png"
    out.write_bytes(raw)
    print(f"OK: {out} ({out.stat().st_size // 1024} KB, mime={mime})")


if __name__ == "__main__":
    asyncio.run(main())
