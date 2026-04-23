"""
One-shot image generation for the PROTOCOL ΔΣ vault frame.

Generates a high-tech black-ops electronic vault illustration.
The generated image is meant to be used as a BACKGROUND/FRAME around the 6
React combination dials (they will be overlaid on the central display area).

Uses Gemini Nano Banana (gemini-3.1-flash-image-preview) via emergentintegrations.
Outputs: /app/frontend/public/vault_frame.png

Run: cd /app && python tests/generate_vault_frame.py
"""

import os
import base64
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa

API_KEY = os.environ["EMERGENT_LLM_KEY"]
OUT_PATH = Path("/app/frontend/public/vault_frame.png")

PROMPT = (
    "Create a high-detail cinematic illustration of a futuristic black-ops "
    "ELECTRONIC VAULT, centered front view, wide 16:9 framing. "
    "The vault body is matte black brushed metal with subtle military panel "
    "lines, rivets, and heavy reinforced hinges on both sides. "
    "A LARGE RECESSED horizontal rectangular display panel in the exact center "
    "is EMPTY, PURE MATTE BLACK, no content, no digits, no symbols — this empty "
    "area is reserved for a digital combination readout that will be overlaid "
    "later in code. The empty central panel must occupy about 55% of the image "
    "width and be perfectly centered, with a subtle thin glowing cyan inner bezel "
    "frame around it. "
    "Around this central empty panel: thin LED strips glowing a subtle MIX of "
    "CYAN and AMBER (no other colors), small status LEDs, a fingerprint scanner "
    "on the bottom-right, a numeric keypad with faintly lit keys on the bottom-left, "
    "and a small engraved stamp 'PROTOCOL ΔΣ — CLASSIFIED' in the top-right corner. "
    "A subtle horizontal seam suggests the vault door can open. "
    "Background: dark concrete bunker wall, cinematic chiaroscuro lighting, very "
    "shallow depth of field, hints of warm amber backlight. "
    "Aesthetic: Deep State / CIA black-ops / modern high-tech bunker hybrid, "
    "photorealistic, extremely sharp, premium cinematic look. "
    "STRICT REQUIREMENTS: (1) the central rectangular panel MUST remain empty "
    "and pure black (no numbers, no dials, no text inside it); (2) only cyan and "
    "amber LEDs, no red, no blue, no green; (3) no people, no logos of real brands; "
    "(4) wide 16:9 horizontal aspect."
)


async def main():
    chat = LlmChat(
        api_key=API_KEY,
        session_id="deepotus-vault-frame-gen",
        system_message=(
            "You are an image generator that produces cinematic, fictional "
            "military-tech vault illustrations for a parody AI memecoin project. "
            "Never include real brands, never include people, always leave the "
            "reserved central display area completely empty."
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
