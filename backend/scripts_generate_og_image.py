"""
Generate Open Graph image 1200x630 for $DEEPOTUS landing page.

Strategy:
- Use existing AI hero portrait as background (deepotus_hero_serious.jpg)
- Apply dark gradient overlay so text remains legible
- Render bilingual brand identity:
   - Big bold ticker      "$DEEPOTUS"
   - Sub-line             "PROTOCOL ΔΣ · Deep State Candidate"
   - Lower right glitch   "AI-PROPHET · MICA-AWARE"
   - Bottom-left footer   "deepotus.preview · Solana"
   - Top-left stamp       "CONFIDENTIEL · NIVEAU 04"
- Output: /app/frontend/public/og_image.png  (1200x630, RGB)

Relies only on PIL — fast, deterministic, no AI hallucination risk.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public"
SRC_HERO = PUBLIC_DIR / "deepotus_hero_serious.jpg"
SRC_HERO_FALLBACK = PUBLIC_DIR / "deepotus_hero.jpg"
OUT_OG = PUBLIC_DIR / "og_image.png"
OUT_TWITTER = PUBLIC_DIR / "twitter_card.png"

W, H = 1200, 630


def _try_font(paths, size):
    for p in paths:
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


# Use locally available fonts (DejaVu is bundled with Pillow on Linux containers)
FONT_BOLD_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf",
    "/opt/plugins-venv/lib/python3.11/site-packages/reportlab/fonts/VeraBd.ttf",
]
FONT_REG_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/opt/plugins-venv/lib/python3.11/site-packages/reportlab/fonts/Vera.ttf",
]
FONT_MONO_PATHS = [
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def build_og_canvas() -> Image.Image:
    """Build the 1200x630 OG canvas with hero image + overlay + branding."""
    src_path = SRC_HERO if SRC_HERO.exists() else SRC_HERO_FALLBACK
    if not src_path.exists():
        raise FileNotFoundError(f"No source hero image found ({SRC_HERO} or {SRC_HERO_FALLBACK})")

    base = Image.open(src_path).convert("RGB")
    # Cover-resize: scale base so it fills the 1200x630 frame
    src_ratio = base.width / base.height
    dst_ratio = W / H
    if src_ratio > dst_ratio:
        # source is wider → match by height, crop sides
        new_h = H
        new_w = int(new_h * src_ratio)
    else:
        # source is taller → match by width, crop top/bottom
        new_w = W
        new_h = int(new_w / src_ratio)
    resized = base.resize((new_w, new_h), Image.LANCZOS)
    # Center crop
    left = (new_w - W) // 2
    top = (new_h - H) // 2
    cropped = resized.crop((left, top, left + W, top + H))

    # Slightly darken via overlay
    canvas = cropped.copy()

    # Darken-left + bottom gradient for legibility
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odr = ImageDraw.Draw(overlay)
    # Left vertical gradient (strongest on the left where text sits)
    for x in range(W):
        # cubic ease so the right half stays bright
        t = max(0.0, 1.0 - x / (W * 0.62))
        a = int(220 * (t ** 1.6))
        odr.line([(x, 0), (x, H)], fill=(8, 11, 14, a))
    # Bottom gradient for footer line
    for y in range(H):
        t = max(0.0, (y - H * 0.65) / (H * 0.35))
        a = int(180 * t)
        if a > 0:
            odr.line([(0, y), (W, y)], fill=(8, 11, 14, a))

    canvas = canvas.convert("RGBA")
    canvas = Image.alpha_composite(canvas, overlay)

    # Subtle scanlines for terminal vibe (very low opacity)
    sl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sld = ImageDraw.Draw(sl)
    for y in range(0, H, 3):
        sld.line([(0, y), (W, y)], fill=(0, 0, 0, 18))
    canvas = Image.alpha_composite(canvas, sl)

    # ---- Text layer ----
    txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)

    # Top-left red CONFIDENTIEL stamp
    stamp_font = _try_font(FONT_MONO_PATHS, 18)
    stamp_text = "CONFIDENTIEL · PROTOCOL ΔΣ · NIVEAU 04"
    pad_x, pad_y = 14, 8
    bbox = td.textbbox((0, 0), stamp_text, font=stamp_font)
    sw = bbox[2] - bbox[0]
    sh = bbox[3] - bbox[1]
    sx, sy = 56, 48
    # Red 2-px outlined box
    td.rectangle(
        [sx - pad_x, sy - pad_y, sx + sw + pad_x, sy + sh + pad_y],
        outline=(225, 29, 72, 230),
        width=2,
    )
    td.text((sx, sy - 2), stamp_text, fill=(225, 29, 72, 240), font=stamp_font)

    # Massive headline: "$DEEPOTUS"
    headline_font = _try_font(FONT_BOLD_PATHS, 168)
    head = "$DEEPOTUS"
    hbbox = td.textbbox((0, 0), head, font=headline_font)
    hw = hbbox[2] - hbbox[0]
    hx = 56
    hy = 175
    # subtle drop shadow
    td.text((hx + 4, hy + 4), head, fill=(0, 0, 0, 180), font=headline_font)
    td.text((hx, hy), head, fill=(246, 242, 234, 255), font=headline_font)

    # Accent underline (terminal teal → amber)
    underline_y = hy + 165
    grad = Image.new("RGBA", (min(hw, 720), 8), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for ix in range(grad.width):
        t = ix / max(grad.width - 1, 1)
        r = int(45 + (245 - 45) * t)
        g = int(212 + (158 - 212) * t)
        b = int(191 + (11 - 191) * t)
        gd.line([(ix, 0), (ix, grad.height)], fill=(r, g, b, 235))
    txt.paste(grad, (hx, underline_y), grad)

    # Sub-headline
    sub_font = _try_font(FONT_BOLD_PATHS, 38)
    sub = "The Deep State's AI Prophet Candidate"
    td.text((hx + 2, underline_y + 22), sub, fill=(0, 0, 0, 180), font=sub_font)
    td.text((hx, underline_y + 20), sub, fill=(246, 242, 234, 240), font=sub_font)

    # Tag line FR
    tag_font = _try_font(FONT_REG_PATHS, 24)
    tag = "Solana memecoin · MiCA-aware · 0% Tax · PROTOCOL ΔΣ"
    td.text((hx, underline_y + 80), tag, fill=(170, 188, 200, 230), font=tag_font)

    # Bottom-right glitch stamps
    rb_font = _try_font(FONT_MONO_PATHS, 20)
    rb1 = "AI-PROPHET"
    rb2 = "MICA-AWARE"
    rb3 = "PUMP.FUN → RAYDIUM"
    pad_x, pad_y = 12, 6
    bx_right = W - 56
    by = H - 56
    items = [(rb1, (51, 255, 51)), (rb2, (245, 158, 11)), (rb3, (45, 212, 191))]
    for label, color in reversed(items):
        bb = td.textbbox((0, 0), label, font=rb_font)
        lw = bb[2] - bb[0]
        lh = bb[3] - bb[1]
        x1 = bx_right - lw
        y1 = by - lh
        td.rectangle(
            [x1 - pad_x, y1 - pad_y, bx_right + pad_x - lw + lw, by + pad_y],
            outline=(*color, 220),
            width=2,
        )
        td.text((x1, y1 - 2), label, fill=(*color, 240), font=rb_font)
        bx_right = x1 - pad_x - 14  # shift left for next item

    # Bottom-left footer
    foot_font = _try_font(FONT_MONO_PATHS, 16)
    foot = "deepotus.live · /DEEP-STATE-POTUS · SOLANA SPL"
    td.text((58, H - 38), foot, fill=(0, 0, 0, 200), font=foot_font)
    td.text((56, H - 40), foot, fill=(180, 195, 205, 230), font=foot_font)

    # Subtle vignette
    vignette = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse([-260, -260, W + 260, H + 260], fill=255)
    vignette = vignette.filter(ImageFilter.GaussianBlur(220))
    vmask = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vmask_pixels = vmask.load()
    vp = vignette.load()
    for yy in range(H):
        for xx in range(W):
            v = vp[xx, yy]
            vmask_pixels[xx, yy] = (0, 0, 0, max(0, 90 - int(v * 0.35)))
    canvas = Image.alpha_composite(canvas, vmask)

    # Composite text on top
    canvas = Image.alpha_composite(canvas, txt)

    return canvas.convert("RGB")


def main():
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    img = build_og_canvas()
    img.save(OUT_OG, format="PNG", optimize=True)
    # Twitter card uses the same content
    img.save(OUT_TWITTER, format="PNG", optimize=True)
    print(f"OK :: wrote {OUT_OG} and {OUT_TWITTER} ({img.size})")


if __name__ == "__main__":
    main()
