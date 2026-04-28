"""Generate three $DEEPOTUS logo concepts in parallel via Gemini Nano Banana.

Run once from the backend root. Results are written to
/app/frontend/public/logo_v{1,2,3}.png so the main agent can show them
inline in its next message.
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

from core.llm_compat import LlmChat, UserMessage

OUT_DIR = Path("/app/frontend/public")
OUT_DIR.mkdir(exist_ok=True)

KEY = os.environ.get("EMERGENT_LLM_KEY")
if not KEY:
    print("EMERGENT_LLM_KEY missing", file=sys.stderr)
    sys.exit(1)

MODEL_PROVIDER = "gemini"
MODEL_NAME = "gemini-3.1-flash-image-preview"  # Nano Banana

CONCEPTS = {
    "logo_v1_ai_prophet": (
        "Logo illustration for a Solana memecoin called $DEEPOTUS — the AI presidential candidate chosen by the Deep State. "
        "SQUARE 1:1 format, crypto token avatar style. "
        "Center: a stylized portrait of a stern presidential candidate wearing ICONIC mirrored aviator sunglasses, "
        "the reflection in the sunglasses shows glowing neon cyan circuit-board patterns suggesting an AI brain. "
        "Subtle holographic red/white/blue American flag stripes wrapping around the head as flowing data streams. "
        "Behind the head, a faint circular seal with the letters 'D S' (Deep State) and binary code. "
        "Color palette: deep navy, crimson red, electric cyan, off-white, with subtle glitch accents. "
        "Style: modern tech-crypto illustration, vector-clean lines, high contrast, futuristic yet political. "
        "Think AIXBT × TURBO × WorldCoin aesthetics. Flat background (solid dark navy or gradient). No text watermark. "
        "Extremely high detail, professional crypto logo quality, centered composition."
    ),
    "logo_v2_presidential_coin": (
        "Logo illustration for a Solana memecoin called $DEEPOTUS, designed as a CLASSIC US presidential portrait seal but memetic. "
        "SQUARE 1:1 format. "
        "Center: a PROFILE side-view bust of a fictional president in the style of a US coin engraving (like the quarter or Lincoln memorial), "
        "wearing black wraparound sunglasses with a tiny earpiece wire, short stern hair, strong jawline. "
        "Around the portrait: a laurel wreath on the left and right, and at the top an arc of tiny stars. "
        "Bottom arc reads 'DEEP STATE' in engraved serif caps, tiny tiny subtext '— OFFICIAL CANDIDATE —'. "
        "Color palette: luxurious navy-blue background with a tight red border ring, white/ivory coin relief, subtle gold accents. "
        "Style: like an official political campaign seal but with a clearly memetic vibe, "
        "Dogecoin × TRUMP coin × US dollar-bill engraving energy, crisp engraving lines, balanced symmetry. "
        "No blur, no watermark, vector-clean illustration, centered portrait."
    ),
    "logo_v3_brutalist_degen": (
        "Logo illustration for a Solana memecoin called $DEEPOTUS, BRUTALIST DEGEN / PUMP.FUN sticker style. "
        "SQUARE 1:1 format. "
        "Center: a cartoony yet brutal mascot character — a confident stylized prophet/president figure "
        "with oversized dark sunglasses, open-mouthed smirk, fat black outline strokes (thick bold cartoon lines), "
        "a cracked halo of data/static hovering above his head like a corrupted saint. "
        "Tiny details: tongue out, one bead of sweat, glitchy CRT scanline texture behind him, "
        "a small 'DS' cult emblem on his collar. "
        "Background: flat single color (hot safety-orange OR brutalist yellow OR glitch red), "
        "high-contrast, no gradients. "
        "Style: pump.fun / $WIF / $POPCAT / $PEPE energy — sticker-ready, 4chan-adjacent humor, "
        "irreverent mascot, memecoin-avatar perfection, vector-clean bold outlines, HIGH saturation. "
        "No watermark, no extra text, centered character, strong readability as a small 64×64 icon."
    ),
}


async def generate_one(session_id: str, prompt: str, out_path: Path) -> str:
    """Generate a single image and save it."""
    chat = LlmChat(
        api_key=KEY,
        session_id=session_id,
        system_message="You are a world-class crypto logo designer. Output ONLY the image, no text commentary.",
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    _text, images = await chat.send_message_multimodal_response(
        UserMessage(text=prompt)
    )

    if not images:
        return f"NO_IMAGE returned for {session_id}"

    img = images[0]
    # data is base64-encoded PNG/JPEG bytes
    raw = base64.b64decode(img["data"])
    out_path.write_bytes(raw)
    size_kb = out_path.stat().st_size // 1024
    return f"OK {session_id}: {out_path} ({size_kb} KB, mime={img['mime_type']})"


async def main():
    tasks = []
    for name, prompt in CONCEPTS.items():
        out = OUT_DIR / f"{name}.png"
        tasks.append(generate_one(name, prompt, out))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        print(r)


if __name__ == "__main__":
    asyncio.run(main())
