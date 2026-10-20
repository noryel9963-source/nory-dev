"""Khmer edition of "Ölüm Ötesi Hayat": សេចក្ដីស្លាប់ / និងជីវិតបរលោក — the title printed on the translation's title
page ("Ölüm ve Ötesi Hayat"). Navy like the original
"ÖLÜM ÖTESİ / HAYAT", with a soft light glow. No author (the blue band stays empty).

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "olum-notitle-source.png"
SOURCE_HD = HERE / "olum-notitle-source-4x.png"

COVER = (47, 27, 810, 1170)          # cover inside the screenshot's dark frame (source px)
CORNER = 14
CX = 435

NAVY_TOP, NAVY_BOTTOM = (26, 40, 96), (40, 72, 150)
GLOW = (255, 250, 232)
# text, max width, ink height, centre y
LINES = [
    ("សេចក្ដីស្លាប់", 520, 84, 346),    # ÖLÜM ÖTESİ
    ("និងជីវិតបរលោក", 600, 130, 466),   # HAYAT
]


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def navy(w, h):
    t = np.linspace(0, 1, h)[:, None, None]
    g = np.array(NAVY_TOP) * (1 - t) + np.array(NAVY_BOTTOM) * t
    return Image.fromarray(np.repeat(g, w, 1).round().astype(np.uint8))


def build(hd=False, font="Battambang", round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    for text, max_w, ink_h, cy in LINES:
        f = fit(FONTS / f"{font}.ttf", text, max_w * k, ink_h * k)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(CX * k - w / 2), int(cy * k - h / 2)
        glow = glyphs.filter(ImageFilter.GaussianBlur(6 * k))
        im.paste(GLOW, (x, y), glow.point(lambda v: int(v * 0.7)))
        im.paste(navy(w, h), (x, y), glyphs)
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
