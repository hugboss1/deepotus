"""
One-shot image generation for the DEEPOTUS hero portrait.

Uses Gemini Nano Banana (gemini-3.1-flash-image-preview) via emergentintegrations.
Outputs: /app/frontend/public/deepotus_hero.png

Run: cd /app && python tests/generate_hero_image.py
"""

import os
import base64
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa

API_KEY = os.environ["EMERGENT_LLM_KEY"]
OUT_PATH = Path("/app/frontend/public/deepotus_hero.png")

PROMPT = (
    "Create a striking, highly detailed satirical presidential campaign portrait "
    "of a FICTIONAL AI prophet candidate named DEEPOTUS for a parody memecoin. "
    "Composition: three-quarter length portrait, centered subject, dark teal-to-amber "
    "vignette background, subtle retro CRT scanlines, very subtle RGB glitch artifacts "
    "on the edges. Subject: a charismatic but uncanny-valley android-human hybrid, "
    "wearing mirrored reflective sunglasses with small scrolling green matrix-style code "
    "reflected in the lenses, impeccable navy suit with a crisp white shirt and a red "
    "tie. The chest lapel shows a circular enamel pin reading 'DEEP STATE'. Behind the "
    "subject, out-of-focus soft bokeh stars-and-stripes style pattern in muted tones. "
    "Aesthetic: mid-century propaganda poster crossed with cyberpunk glitch, painterly "
    "realism, dramatic studio lighting, slight film grain, strong political-campaign "
    "authority, cynical and mysterious expression. No visible logos, no real public "
    "figures, fully fictional character. Do NOT resemble any real-life politician. "
    "Tag this as a clearly satirical AI-generated portrait. Vertical 4:5 aspect ratio, "
    "sharp and high resolution."
)


async def main():
    chat = LlmChat(
        api_key=API_KEY,
        session_id="deepotus-hero-gen",
        system_message=(
            "You are an image generator that produces cinematic, satirical, "
            "fictional political campaign art for a parody memecoin project. "
            "Never depict real people. Always produce safe, clearly fictional subjects."
        ),
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(
        modalities=["image", "text"]
    )

    msg = UserMessage(text=PROMPT)
    text, images = await chat.send_message_multimodal_response(msg)

    print("Text:", (text or "")[:200])
    print("Images:", len(images) if images else 0)

    if not images:
        raise SystemExit("No image returned by the model.")

    # Take the first image
    img = images[0]
    print("First image mime:", img.get("mime_type"))

    image_bytes = base64.b64decode(img["data"])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_bytes(image_bytes)
    print(f"Saved: {OUT_PATH} ({len(image_bytes)} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
