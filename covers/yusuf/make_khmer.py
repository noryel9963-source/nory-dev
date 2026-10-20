"""Khmer edition of "Kur'ân'ın Sihirli Ufku: Yusuf Sûresi": ជើងមេឃដ៏មន្តស្នេហ៍នៃគម្ពីរគួរអាន / ស៊ូរ៉ោះយូសុហ្វ — the title
printed on the translation's title page. Gold like the original: the small series line on top, then ស៊ូរ៉ោះ and a
large យូសុហ្វ (the original's "YUSUF sûresi"), with a soft dark shadow. No author.

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "yusuf-notitle-source.png"
SOURCE_HD = HERE / "yusuf-notitle-source-4x.png"

COVER = (16, 16, 686, 1026)          # cover inside the screenshot's navy frame (source px)
CORNER = 12
CX = 351

GOLD_TOP, GOLD_BOTTOM = (252, 226, 140), (196, 140, 46)
SHADOW = (12, 4, 4)
# text, max width, ink height, centre y
LINES = [
    ("ជើងមេឃដ៏មន្តស្នេហ៍នៃគម្ពីរគួរអាន", 430, 30, 104),   # KUR'ÂN'IN SİHİRLİ UFKU
    ("ស៊ូរ៉ោះ", 300, 62, 168),                          # sûresi
    ("យូសុហ្វ", 460, 120, 262),                          # YUSUF
]


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def gold(w, h):
    t = np.linspace(0, 1, h)[:, None, None]
    g = np.array(GOLD_TOP) * (1 - t) + np.array(GOLD_BOTTOM) * t
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
        sh = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(3 * k)), round(2 * k), round(3 * k))
        im.paste(SHADOW, (x, y), sh.point(lambda v: int(v * 0.8)))
        im.paste(gold(w, h), (x, y), glyphs)
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
