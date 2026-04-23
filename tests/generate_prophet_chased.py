"""
One-shot image generation for the /operation reveal page.

Depicts the PROPHET panicking and chased by a crowd brandishing banners with
the RIPPLED logo (concentric golden arcs + central human figure). Represents
the fall of the Deep State — the narrative payoff at DECLASSIFIED.

Uses Gemini Nano Banana (gemini-3.1-flash-image-preview) via emergentintegrations.
Outputs: /app/frontend/public/prophet_chased.png

Run: cd /app && python tests/generate_prophet_chased.py
"""

import os
import base64
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa

API_KEY = os.environ["EMERGENT_LLM_KEY"]
OUT_PATH = Path("/app/frontend/public/prophet_chased.png")

PROMPT = (
    "Cinematic photorealistic wide 16:9 scene depicting THE FALL OF THE DEEP STATE. "
    "Foreground, slightly left of center: a middle-aged American presidential-candidate "
    "figure running towards the camera in full panic. He wears a dark charcoal suit with "
    "a loosened red tie, short gray hair, aviator sunglasses slipping off his nose, mouth "
    "open in a silent scream, arms flailing. Sweat, disheveled hair, tie flying. "
    "He holds a briefcase that is falling apart — papers fluttering behind him marked "
    "with 'CLASSIFIED' stamps (no other text). "
    "\n\n"
    "Mid-ground and background: a massive peaceful but determined crowd of diverse people "
    "(men and women of varied ethnicities, ages, ordinary clothes) pursuing him down a wide "
    "boulevard. They raise tall rectangular cloth banners high above their heads. "
    "EVERY banner must show the SAME stylized logo in a muted golden-yellow color (#E3D99F) "
    "on a cream/off-white background: a MINIMAL GEOMETRIC symbol consisting of a small "
    "abstract human figure (a circle for the head and an inverted-teardrop body) standing "
    "at the center of THREE concentric incomplete circular arcs that ripple outward — "
    "the arcs open asymmetrically, suggesting waves propagating. The logo is clean, "
    "modern, minimalist, no typography. Some banners show just the logo; some show the "
    "logo with additional thin golden ripple lines in the background. "
    "The crowd's expressions: resolute, hopeful, not violent — a peaceful uprising. "
    "\n\n"
    "Environment: a grand wide avenue flanked by classical government-style architecture "
    "(pillars, pediments, tall windows). Torn propaganda posters peel from the walls "
    "(the posters show shadowy portraits but no readable text). Street lights flicker. "
    "A vintage newspaper flies across the scene. Broken CCTV cameras hang from lamp posts. "
    "Dust and debris in the air. "
    "\n\n"
    "Sky: an apocalyptic gradient from a deep bronze-orange at the horizon to a purple-charcoal "
    "at the top. Strong warm backlight from the sunset behind the crowd, illuminating the "
    "banners and haloing the crowd, casting the Prophet into relief against the glow. "
    "Volumetric light, dust motes, cinematic haze, shallow depth of field — the Prophet "
    "and the front row of the crowd are in sharp focus, the rest of the crowd softly blurred. "
    "\n\n"
    "Mood: revolutionary, historical, end-of-regime, epic — like a famous photograph from "
    "a 20th-century revolution, but filtered through a modern deepfake/AI cinematic aesthetic. "
    "Serious and powerful, not comical. "
    "\n\n"
    "STRICT REQUIREMENTS: "
    "(1) NO readable text anywhere in the image (no words, no letters on the banners, "
    "no street signs, no brand names — only the described abstract geometric RIPPLED logo). "
    "(2) NO real-world brand logos or real public figures. "
    "(3) NO blood, NO weapons, NO violence — the scene shows fear and pursuit, not combat. "
    "(4) Horizontal 16:9 framing. "
    "(5) Color palette: warm bronze-oranges, creams, muted golds, deep charcoals, "
    "with the golden-yellow logo color (#E3D99F) repeated across the banners."
)


async def main():
    chat = LlmChat(
        api_key=API_KEY,
        session_id="deepotus-prophet-chased-gen",
        system_message=(
            "You are an image generator that produces cinematic, fictional political-satire "
            "illustrations for a parody AI memecoin project. Never include real brands, real "
            "people, real text, real propaganda, or violence."
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

    img = images[0]
    print("First image mime:", img.get("mime_type"))

    image_bytes = base64.b64decode(img["data"])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_bytes(image_bytes)
    print(f"Saved: {OUT_PATH} ({len(image_bytes)} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
