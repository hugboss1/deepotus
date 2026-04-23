"""
One-shot image generation for the /classified-vault GATE view.

Depicts a heavy black-ops reinforced door with a LED digicode keypad, matching
the aesthetic of vault_frame.png (matte black, cyan + amber LEDs, bunker vibe).

The central keypad zone must leave an EMPTY RECTANGULAR DISPLAY above the
keys where we will overlay the accreditation input field and LED status.

Outputs: /app/frontend/public/door_keypad.png
Run: cd /app && python tests/generate_door_keypad.py
"""

import os
import base64
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa

API_KEY = os.environ["EMERGENT_LLM_KEY"]
OUT_PATH = Path("/app/frontend/public/door_keypad.png")

PROMPT = (
    "Cinematic photorealistic wide 16:9 illustration of a heavy REINFORCED "
    "BLACK-OPS SECURITY DOOR, centered head-on, occupying the full frame. "
    "The door is matte black brushed metal with military-grade armor panels, "
    "massive forged hinges on both sides, industrial rivets along all edges, "
    "thick bulletproof cladding, a few subtle scratches for realism. "
    "\n\n"
    "Centered on the door, slightly below the midline, is a recessed square "
    "control panel (about 25–30% of the image width) that contains, from top "
    "to bottom: "
    "(1) A LARGE HORIZONTAL RECTANGULAR LED DISPLAY — completely empty, pure "
    "matte black, with a thin glowing cyan bezel. This display zone is "
    "reserved for later overlay — NO characters, NO numbers, NO text inside. "
    "It occupies about 80% of the control panel width and ~25% of the panel "
    "height. "
    "(2) Below it, a physical 3x4 digicode keypad with 12 square backlit keys "
    "showing the digits 0-9 plus a red cancel key (X) and a green confirm key "
    "(OK). Keys are raised, slightly worn, with soft individual LED backlight. "
    "Keys remain visible and legible. "
    "(3) Small status LEDs to the right of the display — one cyan (idle) and "
    "one amber (pending). "
    "\n\n"
    "Around the control panel: a thin glowing cyan LED edge lights the panel "
    "border, with warm amber accent strips along the top-left and bottom-right "
    "corners matching the vault chassis aesthetic. "
    "A small engraved metal plate near the upper-right of the door reads only "
    "'PROTOCOL ΔΣ — LEVEL 02' in silver foil engraving. Another small plate "
    "near the lower-left reads 'DEEP STATE · RESTRICTED'. No other text. "
    "\n\n"
    "Framing: camera straight on, the door fills ~85% of the frame. Subtle dark "
    "concrete bunker wall visible around the door, cinematic chiaroscuro "
    "lighting, dust motes in the air. Strong warm key light illuminating the "
    "door from slightly above camera-left, with a cooler blue rim light on the "
    "right edge. Shallow depth of field on the background, door in sharp focus. "
    "\n\n"
    "STRICT REQUIREMENTS: "
    "(1) The large horizontal LED display zone ABOVE the keypad MUST remain "
    "completely EMPTY and pure matte black — NO digits, NO letters, NO asterisks, "
    "NO placeholders inside that rectangle. It is reserved for external overlay. "
    "(2) The digits on the keypad keys (0-9, X, OK) are ALLOWED and REQUIRED. "
    "(3) NO other readable text except the two small engraved plates mentioned. "
    "(4) NO real brand logos, NO people, NO violence. "
    "(5) Color palette: matte black, amber (#F59E0B), cyan (#22D3EE), warm "
    "silver; the same family as the existing vault chassis. "
    "(6) Wide 16:9 horizontal composition."
)


async def main():
    chat = LlmChat(
        api_key=API_KEY,
        session_id="deepotus-door-keypad-gen",
        system_message=(
            "You are an image generator that produces cinematic, fictional "
            "black-ops security doors for a parody AI memecoin project. Always "
            "leave the reserved LED display area completely empty for external "
            "overlay. Keypad digits (0-9, X, OK) are allowed."
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
        raise SystemExit("No image returned.")

    img = images[0]
    print("First image mime:", img.get("mime_type"))

    image_bytes = base64.b64decode(img["data"])
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_bytes(image_bytes)
    print(f"Saved: {OUT_PATH} ({len(image_bytes)} bytes)")


if __name__ == "__main__":
    asyncio.run(main())
