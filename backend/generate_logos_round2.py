"""Round 2: V4 Matrix-face logo + 3 crypto-ticker monograms.

V4 = another logo candidate (monochrome Matrix face).
M1, M2, M3 = monogram glyphs (the emblem that will be struck on the gold coin).
"""

import asyncio
import base64
import os
import sys
from pathlib import Path

from emergentintegrations.llm.chat import LlmChat, UserMessage

OUT_DIR = Path("/app/frontend/public")
OUT_DIR.mkdir(exist_ok=True)

KEY = os.environ.get("EMERGENT_LLM_KEY")
if not KEY:
    print("EMERGENT_LLM_KEY missing", file=sys.stderr)
    sys.exit(1)

MODEL_PROVIDER = "gemini"
MODEL_NAME = "gemini-3.1-flash-image-preview"  # Nano Banana

CONCEPTS = {
    # -------- V4: Matrix face monochrome --------
    "logo_v4_matrix_face": (
        "Monochromatic logo illustration for a Solana memecoin called $DEEPOTUS. "
        "SQUARE 1:1 format, crypto avatar style. "
        "Center: a STYLIZED frontal HUMAN FACE (head and shoulders silhouette) that is LITERALLY FORMED by "
        "vertical cascading MATRIX-style falling code — streams of glowing digital characters "
        "(Japanese katakana, binary 0 and 1, occasional brackets) dripping downward like rain, "
        "their density and brightness shaping the contours of the face like a sculpted light mosaic. "
        "The face wears iconic CLASSIC AVIATOR sunglasses (teardrop metal frames), the lenses are SOLID "
        "reflective surfaces that subtly mirror more cascading code inside them. "
        "Calm, stern, prophet-like expression. "
        "STRICTLY MONOCHROMATIC — a single luminous green hue (#00FF41 Matrix phosphor) on pure black #000000. "
        "No red, no blue, no other color whatsoever. Deep black negative space, brilliant phosphor green light. "
        "High contrast, cinematic, cyberpunk minimalism, ultra-sharp vector-like rendering. "
        "Centered composition, perfectly symmetric, professional crypto logo quality. "
        "No text, no watermark, no extra graphic elements — just the face-of-code with aviators."
    ),

    # -------- M1: Δ$ (Delta + Dollar) --------
    "monogram_m1_delta_dollar": (
        "Minimalist crypto-ticker-style MONOGRAM GLYPH for a Solana memecoin called $DEEPOTUS. "
        "SQUARE 1:1 format. "
        "Design: one single iconic symbol = the capital Greek letter DELTA (Δ, triangular A shape) with a "
        "VERTICAL DOLLAR-SIGN STROKE running top-to-bottom through its center. "
        "Visual language: instantly recognizable as a currency ticker mark, same family as Bitcoin ₿, "
        "Ethereum ◆, XRP X, Dogecoin Ð. Bold geometric strokes, clean serif-free edges, perfectly symmetric. "
        "Rendered as a POLISHED GOLD metal medallion face: warm rich gold gradient, engraved depth, "
        "subtle highlights on the edges of the strokes suggesting stamped relief. "
        "Background: very dark charcoal #111111 with a subtle vignette, so the gold glyph pops at the center. "
        "Style: institutional cryptocurrency logo mark, luxury numismatic finish, vector-sharp precision. "
        "No additional text, no extra ornaments, no face, no scenery — ONLY the single glyph, centered."
    ),

    # -------- M2: DS ligature with Bitcoin-style vertical bars --------
    "monogram_m2_ds_bars": (
        "Minimalist crypto-ticker-style MONOGRAM GLYPH for a Solana memecoin called $DEEPOTUS (Deep State). "
        "SQUARE 1:1 format. "
        "Design: one single iconic symbol = the capital letters D and S INTERWOVEN as a single custom "
        "ligature — the back-stroke of the D continues into the top curve of the S like a brand monogram. "
        "TWO SHORT VERTICAL BARS pierce vertically through the top and bottom of the S, in the exact same "
        "visual language as the Bitcoin symbol ₿. "
        "Bold geometric strokes, clean modern sans-serif, perfectly symmetric, instantly recognizable as a "
        "currency ticker mark. "
        "Rendered as a POLISHED GOLD metal medallion face: warm rich gold gradient, engraved depth, "
        "crisp highlights on stroke edges, stamped-relief feel. "
        "Background: very dark charcoal #111111 with subtle vignette. "
        "Style: institutional cryptocurrency logo mark, luxury numismatic finish, vector-sharp. "
        "No extra text, no ornaments, no face, no scenery — ONLY the single DS-bars glyph, centered."
    ),

    # -------- M3: ΔΣ pure (PROTOCOL ΔΣ homage) --------
    "monogram_m3_delta_sigma": (
        "Minimalist crypto-ticker-style MONOGRAM GLYPH for a Solana memecoin called $DEEPOTUS. "
        "SQUARE 1:1 format. "
        "Design: one single iconic symbol = the two capital Greek letters DELTA (Δ) and SIGMA (Σ) fused "
        "into a UNIQUE cryptocurrency glyph — the Δ sits inside the negative space of the Σ, or their "
        "strokes share a common vertical axis to form a single balanced mark. "
        "Think of it like ETH ◆ or XRP X: an instantly-memorable currency emblem. "
        "Bold geometric strokes, clean edges, perfectly symmetric around a vertical axis. "
        "Rendered as a POLISHED GOLD metal medallion face: warm rich gold gradient, engraved depth, "
        "subtle edge highlights suggesting stamped relief. "
        "Background: very dark charcoal #111111 with a subtle vignette. "
        "Style: institutional cryptocurrency logo mark, luxury numismatic finish, vector-sharp precision. "
        "No additional text, no extra ornaments, no face, no scenery — ONLY the single ΔΣ glyph, centered."
    ),
}


async def generate_one(session_id: str, prompt: str, out_path: Path) -> str:
    chat = LlmChat(
        api_key=KEY,
        session_id=session_id,
        system_message="You are a world-class crypto logo / numismatic designer. Output ONLY the image, no text commentary.",
    ).with_model(MODEL_PROVIDER, MODEL_NAME)

    _text, images = await chat.send_message_multimodal_response(
        UserMessage(text=prompt)
    )

    if not images:
        return f"NO_IMAGE returned for {session_id}"

    img = images[0]
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
