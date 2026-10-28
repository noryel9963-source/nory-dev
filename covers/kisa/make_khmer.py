"""Kısa Sûrelerin Tefsiri (Prof. Dr. Davut Aydüz), on the real cover (the user's photo of the printed book):
តាហ្វសៀរ / ស៊ូរ៉ោះខ្លីៗ — the title in the translation (its title page reads តាហ្វសៀរស៊ូរ៉ោះខ្លីៗ) — in the place of
"Kısa Sûrelerin / Tefsîri" on the beige panel, near-black like the original. No author, no publisher logo.

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "kisa-notitle-source.png"
SOURCE_HD = HERE / "kisa-notitle-source-4x.png"

COVER = (47, 9, 925, 1450)           # the book inside the photo, right of the spine crease at x 40 (source px)
CORNER = 0
CX = 479

INK = (40, 32, 26)
SHADOW = (255, 236, 196)
# text, max width, ink height, centre y
LINES = [
    ("តាហ្វសៀរ", 440, 128, 872),        # Tefsîri (Khmer word order: tafsir first)
    ("ស៊ូរ៉ោះខ្លីៗ", 420, 96, 1000),      # Kısa Sûrelerin
]


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


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
        sh = glyphs.filter(ImageFilter.GaussianBlur(4 * k)).transform(glyphs.size, Image.AFFINE,
                                                                      (1, 0, -2 * k, 0, 1, -3 * k))
        im.paste(SHADOW, (x, y), sh.point(lambda v: int(v * 0.35)))
        im.paste(INK, (x, y), glyphs)
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
