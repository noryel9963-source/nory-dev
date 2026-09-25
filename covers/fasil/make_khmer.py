"""Khmer edition of the "Fasıldan Fasıla" cover (title, number, author and "7. BASKI" ribbon removed).

    python3 make_khmer.py [--hd] [--font Moul] 1 2 ...
Writes khmer-N.png (759x1099) or khmer-N-hd.png (3036x4396).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "fasil-notitle-source.png"
SOURCE_HD = HERE / "fasil-notitle-source-4x.png"

COVER = (13, 12, 772, 1111)            # cover inside the app frame (source px)
CORNER = 12

# ពីជំពូកមួយ ទៅជំពូកមួយ — "From Chapter to Chapter" (Fasıldan Fasıla); proposed translation.
# Ornate like the original: Moul, red-brown fill with a darker outline, one line across the top.
TITLE = [
    # text, max width, ink height, center x, center y
    ("ពីជំពូកមួយ ទៅជំពូកមួយ", 700, 88, 392, 148),
]
FILL_TOP, FILL_BOTTOM = (170, 60, 15), (95, 30, 5)
OUTLINE = (55, 18, 0)

# volume number under the title, like the original "1"
NUMBER_CENTER_X, NUMBER_BOTTOM, NUMBER_HEIGHT = 383, 294, 40
NUMBER_COLOR = (120, 45, 8)


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
                                     stroke_width=max(1, round(1.5 * k)), stroke_fill=255)
        shadow = ImageChops.offset(outline.filter(ImageFilter.GaussianBlur(2 * k)), round(2 * k), round(2 * k))
        grad = np.linspace(0, 1, h)[:, None, None]
        fill = (np.array(FILL_TOP) * (1 - grad) + np.array(FILL_BOTTOM) * grad).astype(np.uint8)
        fill = Image.fromarray(np.broadcast_to(fill, (h, w, 3)).copy())
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        im.paste((60, 40, 10), (x, y), shadow.point(lambda v: int(v * 0.35)))
        im.paste(OUTLINE, (x, y), outline)
        im.paste(fill, (x, y), glyphs)


def draw_number(im, number, k):
    font = fit(FONTS / "CormorantGaramond-Medium.ttf", number, 400 * k, NUMBER_HEIGHT * k, None, ["lnum"])
    l, t, r, b = font.getbbox(number, features=["lnum"])
    x, y = NUMBER_CENTER_X * k - (l + r) / 2, NUMBER_BOTTOM * k - b
    d = ImageDraw.Draw(im)
    d.text((x, y), number, font=font, fill=NUMBER_COLOR, features=["lnum"],
           stroke_width=max(1, round(0.8 * k)), stroke_fill=NUMBER_COLOR)


def build(volume, hd=False, font="Moul", round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    draw_title(im, k, FONTS / f"{font}.ttf")
    draw_number(im, volume, k)
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
    font = "Moul"
    if "--font" in args:
        font = args[args.index("--font") + 1]
        args = [a for a in args if a not in ("--font", font)]
    for v in [a for a in args if a != "--hd"] or ["1"]:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd, font).save(out)
        print("wrote", out.name)
