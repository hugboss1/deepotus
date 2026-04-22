"""
Generate 3 Prophet image variants via Gemini Nano Banana.

Variants:
  1. deepotus_hero_serious.jpg  - Institutional, presidential portrait
  2. deepotus_hero_meme.jpg     - Memetic, over-the-top campaign poster
  3. deepotus_hero_glitch.jpg   - Extreme glitch/deepfake corrupted look

Run: cd /app && python tests/generate_hero_variants.py
"""

import os
import base64
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

API_KEY = os.environ["EMERGENT_LLM_KEY"]
OUT_DIR = Path("/app/frontend/public")

VARIANTS = [
    {
        "name": "deepotus_hero_serious.jpg",
        "label": "serious",
        "prompt": (
            "Create a striking satirical presidential campaign portrait of a FICTIONAL "
            "AI prophet candidate called DEEPOTUS. Three-quarter length composition, "
            "center subject, stern and confident expression, eyes hidden behind mirrored "
            "aviator sunglasses reflecting faint green matrix-code. Impeccable dark navy "
            "pinstripe suit, crisp white shirt, deep red silk tie with a subtle "
            "tone-on-tone pattern, small circular enamel lapel pin reading 'DEEP STATE'. "
            "Background: out-of-focus institutional stars-and-stripes style banner in "
            "muted teal-to-amber duotone gradient, with subtle CRT scanlines. "
            "Aesthetic: mid-century political-campaign poster crossed with Bloomberg "
            "terminal palette, painterly realism, dramatic studio rim lighting, subtle "
            "film grain. No visible brand logos. Not resembling any real-life public "
            "figure. Clearly fictional and satirical. Vertical 4:5 aspect ratio, "
            "high resolution, sharp details."
        ),
    },
    {
        "name": "deepotus_hero_meme.jpg",
        "label": "meme",
        "prompt": (
            "Create a MEMETIC, OVER-THE-TOP satirical campaign poster portrait of a "
            "FICTIONAL AI prophet candidate called DEEPOTUS. Composition: centered "
            "three-quarter portrait, subject smirking with exaggerated confidence, "
            "pointing directly at the viewer like a classic Uncle Sam recruiting "
            "poster, one eyebrow raised. Wearing oversized mirrored aviator sunglasses "
            "with scrolling green matrix code reflected in the lenses, a navy suit with "
            "a golden laurel wreath pin and a bold red tie, 'DEEP STATE' pin on lapel. "
            "Behind subject: bold flat brutalist campaign poster background - stylised "
            "pop-art halftone stars, thick diagonal red and cream stripes, large "
            "stencilled text 'VOTE' and '20XX' partially visible in the corner (but "
            "NOT occupying the face area). Meme-friendly energy: exaggerated contrast, "
            "slight caricatural proportions, satirical political-propaganda vibe, "
            "Warhol-meets-4chan aesthetic, saturated colors but kept elegant. Must "
            "clearly feel like PARODY / SATIRE. No real-person likeness, no real brand "
            "logos. Vertical 4:5 aspect ratio, high resolution."
        ),
    },
    {
        "name": "deepotus_hero_glitch.jpg",
        "label": "glitch",
        "prompt": (
            "Create an EXTREME DEEPFAKE GLITCH portrait of a FICTIONAL AI prophet "
            "candidate called DEEPOTUS for a parody memecoin. Composition: a centered "
            "three-quarter portrait of a charismatic android-human hybrid in a navy "
            "suit with red tie and 'DEEP STATE' lapel pin, wearing mirrored aviator "
            "sunglasses with scrolling green matrix code reflected inside. CRITICAL: "
            "the image must look heavily CORRUPTED and glitched, as if a deepfake AI "
            "crashed mid-render. Include: prominent RGB-channel split chromatic "
            "aberration on the edges (cyan on one side, magenta on the other), "
            "horizontal data-moshing bands across the chest and shoulders, pixel "
            "sorting streaks, random scanline distortions, a few colorful VHS tear "
            "artifacts, subtle datamosh color bleeds on the background. Background: "
            "dark teal-to-amber gradient with a distorted stylised flag half-dissolving "
            "into noise. The face remains readable but has subtle uncanny-valley "
            "smoothness, with a single 'AI-GENERATED' watermark-style stamp visible "
            "in one corner. Aesthetic: cyberpunk-propaganda meets corrupted VHS "
            "meets Hito Steyerl. Must be clearly satirical and fictional. No real "
            "person, no real brand logos. Vertical 4:5 aspect ratio, high resolution."
        ),
    },
]


async def gen_one(v):
    print(f"[{v['label']}] generating...")
    chat = LlmChat(
        api_key=API_KEY,
        session_id=f"deepotus-hero-{v['label']}",
        system_message=(
            "You are an image generator that produces cinematic, satirical, "
            "fictional political campaign art for a parody memecoin project. "
            "Never depict real people. Always produce safe, clearly fictional subjects."
        ),
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(
        modalities=["image", "text"]
    )

    _, images = await chat.send_message_multimodal_response(UserMessage(text=v["prompt"]))
    if not images:
        raise RuntimeError(f"No image returned for variant {v['label']}")

    img = images[0]
    data = base64.b64decode(img["data"])
    out = OUT_DIR / v["name"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(f"[{v['label']}] saved {out} ({len(data)} bytes, mime={img.get('mime_type')})")


async def main():
    # Run sequentially to avoid rate limits
    for v in VARIANTS:
        try:
            await gen_one(v)
        except Exception as e:
            print(f"[{v['label']}] ERROR: {e}")

    print("\nDone. Files in:", OUT_DIR)
    for v in VARIANTS:
        p = OUT_DIR / v["name"]
        if p.exists():
            print(f"  {p} ({p.stat().st_size} bytes)")
        else:
            print(f"  {p} (MISSING)")


if __name__ == "__main__":
    asyncio.run(main())
