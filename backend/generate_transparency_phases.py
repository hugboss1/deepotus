"""Generate 4 'classified contract page' illustrations — one per Treasury
Discipline phase shown on the public landing site. Each image shows a
sealed dossier / stamped contract (vintage paper + red CONFIDENTIEL stamp)
in a Matrix / Deep-State aesthetic.

CRITICAL: NO rendered text inside the images. Diffusion models hallucinate
typography. Any "text" appearing on the contract pages must be unreadable
scribbles or generic Lorem-ipsum-style filler glyphs. The wax seal can
have generic insignia but NO recognizable letters. The only readable mark
allowed is the red 'CONFIDENTIEL' stamp because we'll watch out for typos.

The user wants ZERO typography errors, so we instruct the model to either:
  - render the CONFIDENTIEL stamp using the simplest sans-serif uppercase,
    OR
  - render the stamp text as illegible inkblot.
We pick option B (illegible) by default — we'll overlay the actual
'CONFIDENTIEL' text via CSS at render time on the frontend, which
guarantees zero typo.
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

from core.llm_compat import LlmChat, UserMessage

OUT_DIR = Path("/app/frontend/public")
KEY = os.environ.get("EMERGENT_LLM_KEY")
if not KEY:
    print("EMERGENT_LLM_KEY missing", file=sys.stderr)
    sys.exit(1)

PROVIDER = "gemini"
MODEL = "gemini-3.1-flash-image-preview"

SHARED_RULES = (
    "STRICT FORMATTING:\n"
    "- 16:9 cinematic landscape composition.\n"
    "- The dossier / contract page fills 70-85% of the frame, slightly tilted "
    "for drama, photographed from above (top-down at 75°).\n"
    "- Aged ivory parchment paper with subtle vintage grain, faint tea-stain "
    "spots, slightly torn corners.\n"
    "- Background = matte deep-charcoal #0B0D10 desk surface, with subtle "
    "Matrix green digit rain (#33FF33) faintly glowing in the deep blur. "
    "Cyan #2DD4BF ambient rim light from upper-left, gold #F59E0B "
    "candlelight glow from lower-right.\n"
    "- ABSOLUTELY ZERO STAMPS, ZERO SEALS, ZERO OFFICIAL MARKS, ZERO RED INK "
    "OF ANY KIND on the document. The site overlays a clean CSS stamp "
    "afterwards — your image must NOT contain a single red mark.\n"
    "- The contract body lines must look like generic blurred ink lines "
    "(just horizontal smudges and dashes), no actual reading allowed.\n"
    "- A small wax seal in DEEP GOLD (#B8860B), embossed with a stylised "
    "abstract sigil (geometric shapes only — circles, triangles, lines), "
    "located in a corner. NO letters, NO Greek glyphs that could be confused "
    "with real letters. Just abstract emblem.\n"
    "- Subtle film grain, cinematic depth-of-field, sharp focus on the "
    "diagrammatic icons, slight bokeh on the background.\n"
    "- ABSOLUTE PROHIBITIONS: no rendered words in any language, no Latin "
    "alphabet, no Greek alphabet, no Cyrillic, no Chinese, no Arabic, no "
    "QR codes, no hands, no modern logos, no faces, NO RED STAMPS, NO RED "
    "INK MARKS, NO 'CONFIDENTIAL' or 'TOP SECRET' or any stamp text "
    "whatsoever. If the image contains a single readable letter or number, "
    "the output is REJECTED. Diagrammatic icons (arrows, scales, padlocks, "
    "graph curves, chains, geometric shapes) are encouraged."
)

PHASES = {
    "phase_01_launch.png": (
        "PHASE 01 - 'D0 PUMP.FUN LAUNCH · 0% TAX'.\n"
        "Visual narrative: a freshly-stamped INITIATION DOSSIER. A sealed "
        "leather portfolio half-open revealing the first contract page. On "
        "the page, abstract diagrammatic icons: a small bonding-curve graph "
        "shape (rising arc), a stylised mint icon (coin silhouette), and a "
        "padlock with chains over a folder labeled with abstract glyphs. "
        "Wax seal in deep red, embossed with a stylised Δ inside Σ. "
        "Mood: solemn, the moment a clandestine operation officially begins."
    ),
    "phase_02_bonding_curve.png": (
        "PHASE 02 - 'BONDING CURVE · CLIMBING'.\n"
        "Visual narrative: a contract page covered in handwritten engineering "
        "diagrams (rising curves, Fibonacci spirals, target-marker icons), "
        "a small abacus with gold beads in the corner, an antique brass "
        "magnifying glass over a stylised bonding-curve sketch (an ascending "
        "arc with marked checkpoints). Coffee ring stains on the corner. "
        "Mood: focused, calculated ascension."
    ),
    "phase_03_pumpswap_migration.png": (
        "PHASE 03 - 'PUMPSWAP ASCENSION'.\n"
        "Visual narrative: a contract page mid-migration. Two diagrammatic "
        "circles connected by a thick gold arrow (representing pool migration). "
        "Burnt edges on the left circle (the LP being burned). A small "
        "geometric infinity icon. Smoke wisps curling up from the burned "
        "circle. A red Confidentiel stamp half-overlapping the arrow. "
        "Mood: irreversible commitment, transition."
    ),
    "phase_04_anti_dump.png": (
        "PHASE 04 - 'PUMPSWAP → ∞ · ANTI-DUMP DISCIPLINE'.\n"
        "Visual narrative: a contract page showing diagrammatic icons of "
        "discipline: a small balance scale (justice), an antique padlock "
        "with multiple keys (multisig), a clock face with 48h marked, "
        "and a small calendar grid with x-marks (weekly cap). Steel-blue "
        "ink. The wax seal here is gold instead of red, signifying integrity. "
        "Mood: long-term stewardship, controlled discipline."
    ),
}


async def generate_one(filename: str, brief: str) -> None:
    chat = LlmChat(
        api_key=KEY,
        session_id=f"transparency_phase_{filename}",
        system_message=(
            "You are a film concept artist for political-thriller dossier "
            "design. Output ONE single PNG, no rendered legible text "
            "anywhere — only abstract glyphs, blurred ink and stamps. "
            "If the image contains any readable typography, the output is "
            "REJECTED. Repeat: zero rendered words."
        ),
    ).with_model(PROVIDER, MODEL)

    full_prompt = f"{brief}\n\n{SHARED_RULES}"
    _text, images = await chat.send_message_multimodal_response(
        UserMessage(text=full_prompt)
    )
    if not images:
        print(f"[FAIL] {filename}: no image returned", file=sys.stderr)
        return
    raw = base64.b64decode(images[0]["data"])
    out = OUT_DIR / filename
    out.write_bytes(raw)
    print(f"OK: {out.name} ({out.stat().st_size // 1024} KB)")


async def main() -> None:
    # Run sequentially so we don't hammer the LLM rate limits, but they
    # could be parallelised with asyncio.gather() if needed.
    for filename, brief in PHASES.items():
        try:
            await generate_one(filename, brief)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {filename}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
