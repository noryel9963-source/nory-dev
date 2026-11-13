"""Kırık Testi 20 — Khmer title, built like kirik17 (LaMa-erased original, Battambang). No author, no logo.

    python3 make_khmer.py [--hd] [20]
Writes khmer-20.png or khmer-20-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "kirik-notitle-source.png"
SOURCE_HD = HERE / "kirik-notitle-source-4x.png"

COVER = (0, 0, 573, 864)            # the whole image is the cover (source px)
CORNER = 12
CX = 286

BROWN, RIBBON = (88, 42, 26), (104, 54, 18)
SHADOW = (255, 244, 228)
# text, max width, ink height, centre y
# text, max width, ink height, centre y, colour
LINES = [
    ('វដ្តវិលជុំ', 380, 75, 120, BROWN),
    ('នៃពន្លឺនិងងងឹត', 440, 75, 200, BROWN),
    ('ក្អមបែក', 110, 28, 265, RIBBON),
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
    # one size per colour (the smallest fit), so the two white lines and the two pink lines match
    size = {}
    for text, max_w, ink_h, cy, colour in LINES:
        n = fit(FONTS / f"{font}.ttf", text, max_w * k, ink_h * k).size
        size[colour] = min(size.get(colour, n), n)
    for text, max_w, ink_h, cy, colour in LINES:
        f = ImageFont.truetype(str(FONTS / f"{font}.ttf"), size[colour], layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(CX * k - w / 2), int(cy * k - h / 2)
        sh = glyphs.filter(ImageFilter.GaussianBlur(4 * k)).transform(glyphs.size, Image.AFFINE,
                                                                      (1, 0, -2 * k, 0, 1, -3 * k))
        im.paste(SHADOW, (x, y), sh.point(lambda v: int(v * (0.3 if colour == BROWN else 0))))
        im.paste(colour, (x, y), glyphs)
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
    out = HERE / f"khmer-20{'-hd' if hd else ''}.png"
    build(hd, font).save(out)
    print("wrote", out.name)
