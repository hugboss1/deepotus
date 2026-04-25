"""
Generate a "redacted dossier" image for the PublicStats page.

Visual concept:
- Aged off-white paper, typewriter-style monospace
- Headers: "DEEP STATE COORDINATION OFFICE" + "OPERATION ΔΣ · DOSSIER 04"
- Top-right stamp: "TOP SECRET · NIVEAU 04"
- Body lines look like a confidential memo, with the most important
  fields fully blacked out by thick redaction bars, including the
  launch date.
- Bottom: "AUTHORIZED PERSONNEL ONLY" + sigil ΔΣ

Output: /app/frontend/public/redacted_dossier.png  (1600x900)
"""
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public"
OUT = PUBLIC_DIR / "redacted_dossier.png"

W, H = 1600, 900
PAPER = (235, 226, 207)  # aged off-white
PAPER_DARK = (200, 188, 162)
INK = (24, 22, 18)
RED_STAMP = (162, 30, 38)
BLACK_BAR = (10, 10, 10)


def _try_font(paths, size):
    for p in paths:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


FONT_MONO = [
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]
FONT_MONO_BOLD = [
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
]
FONT_SERIF = [
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
]
FONT_SERIF_BOLD = [
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
]


def make_paper_texture(size):
    """Create a subtle aged paper texture."""
    w, h = size
    img = Image.new("RGB", size, PAPER)
    px = img.load()
    # Add fine noise
    for _ in range(int(w * h * 0.04)):
        x = random.randint(0, w - 1)
        y = random.randint(0, h - 1)
        v = random.randint(-12, 8)
        r, g, b = px[x, y]
        px[x, y] = (
            max(0, min(255, r + v)),
            max(0, min(255, g + v)),
            max(0, min(255, b + v)),
        )
    # Add a few warm "coffee" stains
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for _ in range(6):
        cx, cy = random.randint(80, w - 80), random.randint(80, h - 80)
        r = random.randint(60, 160)
        a = random.randint(8, 20)
        col = (160, 110, 60, a)
        od.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
    overlay = overlay.filter(ImageFilter.GaussianBlur(36))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return img


def draw_redaction_bar(d, x, y, w, h):
    """Draw a thick black redaction bar with subtle imperfections."""
    d.rectangle([x, y, x + w, y + h], fill=BLACK_BAR)
    # tiny horizontal "smear" lines at edges to feel hand-applied
    for i in range(3):
        d.line(
            [(x + 6 + i, y - 1 - i), (x + w - 6 - i, y - 1 - i)],
            fill=(20, 20, 20),
            width=1,
        )
        d.line(
            [(x + 6 + i, y + h + i), (x + w - 6 - i, y + h + i)],
            fill=(20, 20, 20),
            width=1,
        )


def draw_stamp(d, x, y, label, color, font, pad=14, rotation_text=False):
    """Draw a rectangular red stamp with bold mono label and a subtle frame."""
    bbox = d.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.rectangle(
        [x, y, x + tw + pad * 2, y + th + pad],
        outline=color,
        width=3,
    )
    # Inner light border
    d.rectangle(
        [x + 4, y + 4, x + tw + pad * 2 - 4, y + th + pad - 4],
        outline=color,
        width=1,
    )
    d.text((x + pad, y + pad // 2 - 2), label, fill=color, font=font)


def main():
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(2026)

    img = make_paper_texture((W, H))
    d = ImageDraw.Draw(img)

    # --- Header band ---
    # Office line
    f_office = _try_font(FONT_SERIF_BOLD, 30)
    f_office_sub = _try_font(FONT_SERIF, 22)
    f_mono_h = _try_font(FONT_MONO_BOLD, 18)
    f_mono = _try_font(FONT_MONO, 22)
    f_mono_label = _try_font(FONT_MONO_BOLD, 22)
    f_mono_small = _try_font(FONT_MONO, 16)
    f_stamp = _try_font(FONT_MONO_BOLD, 22)

    # Top horizontal hairline
    d.line([(70, 70), (W - 70, 70)], fill=INK, width=2)

    d.text((90, 92), "DEEP STATE COORDINATION OFFICE", fill=INK, font=f_office)
    d.text(
        (90, 132),
        "Operation ΔΣ — DOSSIER #04 · Internal memorandum",
        fill=INK,
        font=f_office_sub,
    )

    # Top-right "TOP SECRET" stamp
    draw_stamp(d, W - 470, 78, "TOP SECRET · NIVEAU 04", RED_STAMP, f_stamp)
    # Sub-stamp under it
    draw_stamp(
        d,
        W - 470,
        128,
        "DECLASS: ████████",
        RED_STAMP,
        _try_font(FONT_MONO_BOLD, 18),
        pad=12,
    )

    # Reference line
    d.text(
        (90, 175),
        "REF: ΔΣ-04 / 2026 · CHANNEL: SECURED · COPIES: 1/1",
        fill=(70, 60, 50),
        font=f_mono_small,
    )

    # Hairline under header
    d.line([(90, 210), (W - 90, 210)], fill=INK, width=1)

    # --- Body fields (label + redaction bar) ---
    # Each line: label (in bold mono) + ":" + redacted bar
    field_x = 90
    label_x = 90
    bar_x_start = 90 + 360  # labels are reserved 360px
    line_h = 54
    bar_h = 30
    y = 240

    fields_fr = [
        ("OBJECTIF",            500),
        ("CIBLE PRIMAIRE",      700),
        ("CONTACT TERRAIN",     600),
        ("BUDGET",              360),
        ("DATE DE LANCEMENT",   620),  # the redacted launch date
        ("VECTEUR",             520),
        ("FENÊTRE D'EXÉCUTION", 480),
    ]

    for label, bar_w in fields_fr:
        d.text(
            (label_x, y + 4),
            f"{label}",
            fill=INK,
            font=f_mono_label,
        )
        # ":" anchored at label-x + label width to avoid clash
        bar_y = y - 2
        # subtle "shadow" under the bar
        d.rectangle(
            [bar_x_start + 3, bar_y + 4, bar_x_start + bar_w + 3, bar_y + bar_h + 4],
            fill=(180, 168, 140),
        )
        draw_redaction_bar(d, bar_x_start, bar_y, bar_w, bar_h)
        y += line_h

    # --- Special highlighted "DATE" callout under the field grid ---
    # Big horizontal divider
    y += 8
    d.line([(90, y), (W - 90, y)], fill=INK, width=2)
    y += 22
    callout_label = "J0 · DATE DE LANCEMENT (PUMP.FUN MINT)"
    d.text((90, y), callout_label, fill=INK, font=f_mono_label)
    y += 32
    # Fat redaction bar
    draw_redaction_bar(d, 90, y, 1080, 56)
    # Stamp on right of bar: REDACTED
    draw_stamp(d, 1190, y - 2, "REDACTED", RED_STAMP, _try_font(FONT_MONO_BOLD, 26), pad=14)
    y += 80

    # --- Footer ---
    d.line([(90, H - 130), (W - 90, H - 130)], fill=INK, width=1)

    # Footer left: signature
    d.text(
        (90, H - 110),
        "AUTHORIZED PERSONNEL ONLY · NE PAS DUPLIQUER",
        fill=INK,
        font=f_mono,
    )
    d.text(
        (90, H - 78),
        "— Bureau de coordination · canal sécurisé · 1 copie",
        fill=(70, 60, 50),
        font=f_mono_small,
    )

    # Footer right: ΔΣ sigil
    sigil_font = _try_font(FONT_MONO_BOLD, 64)
    d.text((W - 170, H - 130), "ΔΣ", fill=INK, font=sigil_font)
    d.text(
        (W - 270, H - 60),
        "PROTOCOL ΔΣ",
        fill=INK,
        font=f_mono_small,
    )

    # --- Aging touches: small black ink dots / page corner shadow ---
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # corner darkening (vignette-ish)
    for i in range(60):
        a = max(0, 50 - i)
        od.rectangle([0, i, i, H - i], fill=(0, 0, 0, a // 2))
        od.rectangle([W - i, i, W, H - i], fill=(0, 0, 0, a // 2))
        od.rectangle([0, 0, W, i], fill=(0, 0, 0, a // 2))
        od.rectangle([0, H - i, W, H], fill=(0, 0, 0, a // 2))
    # tiny ink dots
    for _ in range(140):
        x = random.randint(0, W - 1)
        y = random.randint(0, H - 1)
        s = random.randint(1, 2)
        od.ellipse((x, y, x + s, y + s), fill=(15, 12, 8, 180))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    img.save(OUT, format="PNG", optimize=True)
    print(f"OK :: wrote {OUT} ({img.size})")


if __name__ == "__main__":
    main()
