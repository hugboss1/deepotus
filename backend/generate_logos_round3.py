"""Round 3: regenerate V4 (generic face, not Trump-like) + mint the gold coin with monogram M3."""

import asyncio
import base64
import os
import sys
from pathlib import Path

from emergentintegrations.llm.chat import LlmChat, UserMessage

OUT_DIR = Path("/app/frontend/public")
KEY = os.environ.get("EMERGENT_LLM_KEY")
if not KEY:
    print("EMERGENT_LLM_KEY missing", file=sys.stderr)
    sys.exit(1)

MODEL_PROVIDER = "gemini"
MODEL_NAME = "gemini-3.1-flash-image-preview"

CONCEPTS = {
    # -------- V4 v2: Matrix face, GENERIC man, NOT a political figure --------
    "logo_v4_matrix_face": (
        "Monochromatic logo illustration for a Solana memecoin called $DEEPOTUS. "
        "SQUARE 1:1 format, crypto avatar style. "
        "Center: a COMPLETELY FICTIONAL, GENERIC, anonymous adult male face (head and shoulders) that is "
        "LITERALLY FORMED by vertical cascading MATRIX-style falling code — streams of glowing digital "
        "characters (Japanese katakana, binary 0s and 1s, brackets) dripping downward like rain, their "
        "density shaping the contours of the face like a sculpted light mosaic. "
        "VERY IMPORTANT — the face MUST NOT resemble any existing real-world politician, celebrity, or "
        "public figure. NO Donald Trump, NO Biden, NO Obama, NO Putin, NO Macron, NO Musk. Avoid any blonde "
        "bouffant hairstyle, avoid any combover. The face should have: SHORT DARK HAIR (buzz-cut or very "
        "short neutral crop), high cheekbones, strong straight jawline, neutral age around 35-45, average "
        "ethnicity-ambiguous features, calm stern oracle-like expression. Think of an archetypal \"neutral "
        "government operative\" rather than anyone specific. "
        "Wearing CLASSIC TEARDROP AVIATOR sunglasses with fully reflective metallic lenses that show more "
        "cascading code inside them. "
        "STRICTLY MONOCHROMATIC — a single luminous phosphor GREEN hue (#00FF41) on pure black background "
        "(#000000). NO other color whatsoever. High contrast, cinematic, cyberpunk minimalism, extreme "
        "sharpness. Centered, symmetric, professional crypto logo quality. No text, no watermark."
    ),

    # -------- Gold coin — flat / "frontal top-down" shot --------
    "gold_coin_front": (
        "Ultra-realistic numismatic photography of a LUXURY COLLECTOR GOLD COIN for $DEEPOTUS cryptocurrency. "
        "SQUARE 1:1 format. Perfectly CENTERED, FRONTAL top-down shot (like a coin photographed flat on a "
        "jewelry studio backdrop). "
        "The coin is a large round polished pure-gold medallion (rich warm 24-karat yellow gold, brilliant "
        "reflective finish, mirror-like fields with deep engraved reliefs). Dentilated classical rim (small "
        "teeth pattern around the edge), inner beaded circle. "
        "Struck at the CENTER of the obverse: a single bold MONOGRAM GLYPH combining the Greek capital "
        "letters DELTA (Δ) and SIGMA (Σ), fused into one unique cryptocurrency ticker mark (like ETH ◆ or "
        "XRP X) — the Δ sits inside the Σ's negative space, sharing a common vertical axis, deeply engraved "
        "in stamped relief. "
        "Around the monogram, following the rim in engraved uppercase serif letters: "
        "top arc '$DEEPOTUS', bottom arc 'PROTOCOL ΔΣ'. Tiny star separators on left and right of rim. "
        "Photographic quality: razor-sharp focus, soft studio lighting with subtle rim highlight showing "
        "the gold's metallic sheen, gentle vignette, background a very dark neutral charcoal (#0f0f0f) with "
        "a faint warm glow around the coin. "
        "No hands, no fingers, no table props, no text overlay, no watermark. Only the coin itself, "
        "centered, filling about 85% of the frame. Numismatic precision, award-winning product photography."
    ),

    # -------- Gold coin — 3D perspective, cinematic --------
    "gold_coin_3d": (
        "Cinematic hero shot of a LUXURY COLLECTOR GOLD COIN for $DEEPOTUS cryptocurrency. "
        "SQUARE 1:1 format. 3D PERSPECTIVE view — the coin is tilted at about 30-40° toward the camera, "
        "floating mid-air with dramatic side-lighting, showing both the depth of its engraving and the "
        "thickness of its edge. Subtle motion-blur on a second identical coin behind, slightly out of focus. "
        "The coin is a large round polished pure-gold medallion (rich warm 24-karat yellow gold, brilliant "
        "mirror finish, deep engraved reliefs catching the light). Dentilated classical rim, inner beaded "
        "circle, visible coin thickness on the tilted edge. "
        "Struck at the CENTER of the obverse: a single bold MONOGRAM GLYPH combining the Greek capital "
        "letters DELTA (Δ) and SIGMA (Σ), fused into one unique cryptocurrency ticker (like ETH ◆ or XRP X) "
        "— the Δ inside the Σ, shared vertical axis, deep stamped relief catching the rim light. "
        "Around the monogram on the rim in engraved uppercase serif letters: '$DEEPOTUS' (top arc), "
        "'PROTOCOL ΔΣ' (bottom arc), small star separators. "
        "Atmosphere: dark charcoal background with a subtle warm golden rim-light on the coin edge, a very "
        "soft volumetric light ray, faint smoke/particles in the background for depth. Highly cinematic, "
        "like a luxury crypto launch visual. "
        "Razor-sharp focus on the main coin, shallow depth of field, ultra-realistic product rendering. "
        "No hands, no text overlay, no watermark."
    ),
}


async def generate_one(session_id: str, prompt: str, out_path: Path) -> str:
    chat = LlmChat(
        api_key=KEY,
        session_id=session_id,
        system_message="You are a world-class numismatic + crypto product photographer. Output ONLY the image.",
    ).with_model(MODEL_PROVIDER, MODEL_NAME)
    _text, images = await chat.send_message_multimodal_response(
        UserMessage(text=prompt)
    )
    if not images:
        return f"NO_IMAGE for {session_id}"
    img = images[0]
    raw = base64.b64decode(img["data"])
    out_path.write_bytes(raw)
    return f"OK {session_id}: {out_path.stat().st_size // 1024} KB"


async def main():
    tasks = [
        generate_one(name, prompt, OUT_DIR / f"{name}.png")
        for name, prompt in CONCEPTS.items()
    ]
    for r in await asyncio.gather(*tasks, return_exceptions=True):
        print(r)


if __name__ == "__main__":
    asyncio.run(main())
