"""
Generate the DEEPOTUS email header image:
a candidate-with-crowd shot, wide panoramic format for email header.

Output: /app/frontend/public/deepotus_email_hero.jpg
"""

import os
import base64
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

API_KEY = os.environ["EMERGENT_LLM_KEY"]
OUT_PATH = Path("/app/frontend/public/deepotus_email_hero.jpg")

PROMPT = (
    "Create a cinematic, wide PANORAMIC campaign rally header image (roughly 3:1 or 16:9 "
    "aspect ratio, horizontal). "
    "Foreground: a FICTIONAL satirical AI prophet presidential candidate called "
    "DEEPOTUS standing center-left, waving confidently to a crowd, three-quarter "
    "length view from slightly below (hero angle). He wears mirrored aviator "
    "sunglasses reflecting green matrix-style code, a sharp navy pinstripe suit, "
    "crisp white shirt, deep red silk tie, and a small circular 'DEEP STATE' enamel "
    "lapel pin. Expression: charismatic smirk, impeccable composure. "
    "Background: a large enthusiastic crowd of silhouetted supporters extending into "
    "soft bokeh depth, holding up blurred campaign signs and hands in the air, with a "
    "few glowing red/teal/amber light flares from an unseen stage. Atmosphere: dusk, "
    "dramatic rim lighting, volumetric haze, slight film grain, muted teal-to-amber "
    "color grading, subtle CRT scanlines on the upper edges, and very subtle "
    "chromatic aberration on the far corners. Behind the crowd, a blurred, stylised "
    "stars-and-stripes style banner silhouette (NOT a real flag). "
    "Aesthetic: mid-century political propaganda poster crossed with cyberpunk "
    "glitch and Malick-style golden hour realism. Clearly satirical / fictional. "
    "No real public figure likeness. No real brand logos. "
    "Horizontal wide banner suitable for email header use. High resolution."
)


async def main():
    chat = LlmChat(
        api_key=API_KEY,
        session_id="deepotus-email-hero",
        system_message=(
            "You are an image generator that produces cinematic, satirical, fictional "
            "political campaign art for a parody memecoin. Never depict real people. "
            "Always produce clearly fictional, safe subjects."
        ),
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(
        modalities=["image", "text"]
    )

    _, images = await chat.send_message_multimodal_response(UserMessage(text=PROMPT))
    if not images:
        raise SystemExit("No image returned")
    img = images[0]
    data = base64.b64decode(img["data"])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_bytes(data)
    print(f"Saved: {OUT_PATH} ({len(data)} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
