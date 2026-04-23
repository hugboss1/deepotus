"""
One-shot generation of the DEEP STATE LEVEL 2 ACCESS CARD template.

The template is a blank ID-card style background that will be overlaid with
personalized text (NAME + ACCREDITATION NUMBER + QR code) server-side via PIL
when a visitor requests Level 2 clearance.

Target dimensions: wide 16:9 card (e.g. 1600x900 card-like composition).
The template MUST leave empty zones for:
  - NAME field (upper-middle or left side)
  - ACCREDITATION NUMBER (prominent, horizontal strip)
  - QR CODE placeholder (bottom-right square ~15% of width)
  - PHOTO placeholder (circular or rectangular silhouette, not a real face)
  - ISSUE DATE field

Run: cd /app && python tests/generate_access_card_template.py
"""

import os
import base64
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa

API_KEY = os.environ["EMERGENT_LLM_KEY"]
OUT_PATH = Path("/app/backend/assets/access_card_template.png")

PROMPT = (
    "Create a cinematic photorealistic wide 16:9 illustration of a TOP-SECRET "
    "DEEP STATE LEVEL 2 ACCESS CARD, viewed perfectly flat, head-on, centered, "
    "occupying the full frame like a scanned identification document. "
    "\n\n"
    "The card appears to be made of matte black composite with subtle brushed-metal "
    "trim, rounded corners, and a faint holographic security pattern in muted cyan "
    "diagonal stripes covering the bottom third. Aged slightly with micro scratches "
    "to feel authentic. "
    "\n\n"
    "Card layout (MUST leave these zones completely EMPTY for text overlay — no "
    "placeholder letters, no lorem ipsum, no numbers inside these zones): "
    "- Top-left: small square slot reserved for a monochrome abstract silhouette "
    "  of a human head-and-shoulders (like an anonymized agent portrait, "
    "  engraved on dark glass). Keep it vague, no real face. "
    "- Top-right corner: an engraved crest combining the letters 'ΔΣ' with a "
    "  radiating sunburst pattern and a small star of 13 rays. Color: warm amber "
    "  (#F59E0B). "
    "- Center-top: a HORIZONTAL EMPTY BANNER (dark recessed rectangle, no text) "
    "  reserved for AGENT NAME overlay. The banner has a thin cyan underline. "
    "- Below it: another, slightly smaller EMPTY BANNER reserved for "
    "  ACCREDITATION NUMBER overlay, inset into the card. "
    "- Bottom-left: small EMPTY text strips for ISSUE DATE and EXPIRATION DATE. "
    "- Bottom-right: a SQUARE EMPTY DARK SLOT (~15% of card width) reserved for "
    "  a QR code overlay — perfectly flat matte black, no pattern inside. "
    "- Bottom-center strip: a subtle horizontal band with embossed microtext bar "
    "  (pure decorative lines, NO readable text). "
    "\n\n"
    "Overall accents: thin cyan LED edging along the left side, thin amber LED "
    "edging along the right side, matching the $DEEPOTUS vault aesthetic. A large "
    "faint watermark 'PROTOCOL ΔΣ' visible but blurred/embossed in the card "
    "background behind the banners. "
    "\n\n"
    "Background around the card: very subtle dark desk surface with soft cinematic "
    "shadow beneath the card to ground it. The card itself occupies ~85% of the "
    "frame. "
    "\n\n"
    "STRICT REQUIREMENTS: "
    "(1) NO readable text anywhere except the pre-approved engravings 'PROTOCOL ΔΣ', "
    "    'ΔΣ', 'LEVEL 02 CLEARANCE', 'DEEP STATE' — all of which can appear as "
    "    small engraved labels in silver or amber foil; keep them clearly engraved "
    "    but not dominant. "
    "(2) NO lorem ipsum, NO placeholder words, NO dates, NO numbers, NO names — "
    "    every personal field must be an EMPTY slot. "
    "(3) NO real brand logos, NO real people. "
    "(4) Color palette: matte black card, amber (#F59E0B), cyan (#22D3EE), warm "
    "    silver accents. "
    "(5) The card must look like an authentic covert-agency credential, not playful "
    "    or cartoonish. "
    "(6) Horizontal 16:9 composition. "
)


async def main():
    chat = LlmChat(
        api_key=API_KEY,
        session_id="deepotus-access-card-template",
        system_message=(
            "You are an image generator that produces cinematic, fictional covert-"
            "agency ID-card templates for a parody AI memecoin project. Never "
            "include real brands, real people, real text/names/dates/numbers. "
            "The card must always leave personal fields EMPTY for later overlay."
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
