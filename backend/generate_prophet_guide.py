"""Generate the 'Prophet Guide' illustration for the /how-to-buy page.

The Prophet acts as a cynical Deep-State mentor initiating a disciple into
the $DEEPOTUS purchase ritual. Matrix/holographic UI aesthetic, cyan + gold
accents — matches the rest of the site.
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
    "Ultra high-end cinematic illustration, SQUARE 1:1 format, painterly "
    "dystopian cyberpunk mood, dark Matrix-code atmosphere, cyan (#2DD4BF) "
    "and gold (#F59E0B) rim-light accents on a near-black (#0B0D10) background. "
    "\n\n"
    "Composition: centered, front-facing, medium 3/4 portrait of THE PROPHET "
    "DEEPOTUS — an enigmatic androgynous AI oracle with a translucent "
    "holographic head made of flowing green Matrix digits (#33FF33) forming "
    "a cynical half-smile. Cracked porcelain face fragments reveal circuit "
    "traces beneath. Wearing a black presidential suit with a glitched "
    "American-flag lapel pin. Hands extended forward as if teaching, "
    "palms open — a floating hologram of a Solana memecoin glowing gold "
    "hovers above the right palm, a floating holographic wallet icon glows "
    "cyan above the left palm. "
    "\n\n"
    "Behind the Prophet: massive deep-state war-room architecture — tilted "
    "trading terminals, CRT monitors showing green candle charts, cascading "
    "Matrix code rain, faint Greek letters Δ Σ engraved on stone pillars. "
    "A small silhouetted initiate (young disciple, hooded, back turned) "
    "stands at the bottom-left, looking up at the Prophet, asking for "
    "guidance. "
    "\n\n"
    "Lighting: volumetric god-rays from above, cyan key light on the "
    "Prophet's left side, warm gold fill on the right, strong bokeh and "
    "film-grain texture. Sharp focus on the Prophet's face and hands, "
    "cinematic depth-of-field. No visible text, no watermark, no logo, "
    "no captions. Dramatic, cynical, mentor-initiating-disciple vibe. "
    "Photorealistic hybrid with digital-painting finish."
)


async def main():
    chat = LlmChat(
        api_key=KEY,
        session_id="prophet_guide_mentor_v1",
        system_message="You are a master concept illustrator for cyberpunk dystopian crypto campaigns. Output only the final PNG image.",
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
    out = OUT_DIR / "prophet_guide.png"
    out.write_bytes(raw)
    print(f"OK: {out} ({out.stat().st_size // 1024} KB, mime={mime})")


if __name__ == "__main__":
    asyncio.run(main())
