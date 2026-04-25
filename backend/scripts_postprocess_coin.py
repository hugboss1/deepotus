"""Post-process the v5 gold coin: convert the JPEG/RGB output (which has a
visual "checkerboard" rendered as fake transparency) into a TRUE RGBA PNG
with a real alpha channel outside the coin's circular silhouette.

Strategy
--------
1. Open the source image (JPEG, 1024×1024).
2. Detect the coin's silhouette on the actual pixels (the coin is obviously
   centered and filled with gold tones, around the centre). We use a hybrid
   approach:
     a. Build a base mask via a generous circular crop (98% of half-size,
        since the coin occupies ~92-95% of the frame).
     b. Refine the mask by sampling each pixel and:
          - keeping pixels that are clearly NOT the checkerboard background
            (a checkerboard alternates a near-white and a light-grey, both
            very low saturation, very high luminance);
          - dropping pixels that match the checkerboard pattern.
3. Smooth the mask edges with a small Gaussian blur for clean anti-aliasing.
4. Compose RGBA with the refined mask and save as PNG.

The result is a true alpha PNG that drops cleanly onto the Tokenomics donut
chart with NO visible square / no halo.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SRC = Path("/app/frontend/public/gold_coin_front.png")
OUT = SRC  # overwrite in place
DEBUG_DIR = Path("/tmp")


def is_checkerboard_pixel(rgb):
    """A checkerboard cell is either ~white or ~light-grey. Both have:
        - very low saturation (max-min channel diff < 12),
        - high luminance (avg > 175).
    """
    r, g, b = rgb[:3]
    chan_min = min(r, g, b)
    chan_max = max(r, g, b)
    sat = chan_max - chan_min
    lum = (r + g + b) / 3.0
    return sat < 14 and lum > 175


def main() -> None:
    src = Image.open(SRC).convert("RGB")
    w, h = src.size
    cx, cy = w // 2, h // 2
    # Coin radius ~ 47% of half-side, leaving a tiny anti-aliasing margin
    coin_r = int(min(w, h) * 0.49)

    # Step 1 — circular base mask
    base_mask = Image.new("L", src.size, 0)
    draw = ImageDraw.Draw(base_mask)
    draw.ellipse(
        (cx - coin_r, cy - coin_r, cx + coin_r, cy + coin_r),
        fill=255,
    )

    # Step 2 — refine inside the disc: drop checkerboard pixels
    pixels = src.load()
    mask_pixels = base_mask.load()
    for y in range(h):
        for x in range(w):
            if mask_pixels[x, y] == 0:
                continue  # outside the disc, already transparent
            if is_checkerboard_pixel(pixels[x, y]):
                # Pixel is part of the fake-transparency artefact → drop it
                mask_pixels[x, y] = 0

    # Step 3 — close small holes and smooth edges
    refined = base_mask.filter(ImageFilter.MaxFilter(3))   # close 1-px gaps inside the gold
    refined = refined.filter(ImageFilter.GaussianBlur(0.7))  # subtle anti-alias

    # Step 4 — compose RGBA and save as true PNG
    rgba = src.convert("RGBA")
    rgba.putalpha(refined)
    rgba.save(OUT, format="PNG", optimize=True)
    print(f"OK: {OUT} (RGBA, {OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
