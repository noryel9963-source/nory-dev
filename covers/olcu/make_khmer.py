"""Khmer edition of the "Ölçü veya Yoldaki Işıklar" cover (title and author removed).

    python3 make_khmer.py [--hd] [--font Battambang]
Writes khmer.png (830x1245) or khmer-hd.png (3320x4980).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "olcu-notitle-source.png"
SOURCE_HD = HERE / "olcu-notitle-source-4x.png"

COVER = (15, 12, 845, 1257)            # cover inside the app frame (source px)
CORNER = 12

# រង្វាស់ / ឬ / ពន្លឺ / លើផ្លូវ — "The Measure, or Lights on the Way" (Ölçü veya Yoldaki Işıklar);
# proposed translation. Same layout as the original: big first word, small "or", two lines below.
TITLE = [
    # text, max width, ink height, center x, center y
    ("រង្វាស់", 540, 200, 430, 505),
    ("ឬ", 120, 70, 395, 685),
    ("ពន្លឺ", 460, 165, 405, 800),
    ("លើផ្លូវ", 480, 165, 405, 950),
]
FILL_TOP, FILL_BOTTOM = (240, 105, 50), (215, 75, 35)
OUTLINE = (190, 60, 25)


def fit(font_path, text, max_w, ink_h, lang="km", features=None):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language=lang, features=features)
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def draw_title(im, k, font_path):
    for text, max_w, ink_h, cx, cy in TITLE:
        font = fit(font_path, text, max_w * k, ink_h * k)
        l, t, r, b = font.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        origin = (-l + pad, -t + pad)
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text(origin, text, font=font, fill=255, language="km")
        outline = Image.new("L", (w, h), 0)
        ImageDraw.Draw(outline).text(origin, text, font=font, fill=255, language="km",
                                     stroke_width=max(1, round(0.8 * k)), stroke_fill=255)
        shadow = ImageChops.offset(outline.filter(ImageFilter.GaussianBlur(3 * k)), round(3 * k), round(4 * k))
        grad = np.linspace(0, 1, h)[:, None, None]
        fill = (np.array(FILL_TOP) * (1 - grad) + np.array(FILL_BOTTOM) * grad).astype(np.uint8)
        fill = Image.fromarray(np.broadcast_to(fill, (h, w, 3)).copy())
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        im.paste((120, 50, 10), (x, y), shadow.point(lambda v: int(v * 0.45)))
        im.paste(OUTLINE, (x, y), outline)
        im.paste(fill, (x, y), glyphs)


def build(hd=False, font="Battambang", round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    draw_title(im, k, FONTS / f"{font}.ttf")
    im = im.crop(tuple(v * k for v in COVER))
    if not round_corners:
        return im
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), CORNER * k, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    hd = "--hd" in args
    font = args[args.index("--font") + 1] if "--font" in args else "Battambang"
    out = HERE / f"khmer{'-hd' if hd else ''}.png"
    build(hd, font).save(out)
    print("wrote", out.name)
