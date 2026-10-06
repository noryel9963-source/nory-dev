"""Khmer edition of "Fasıldan Fasıla 2": ពីជំពូកមួយ / ទៅជំពូកមួយ (same title as volume 1), dark brown like the original
"Fasıldan" (regular) / "Fasıla" (bold, Battambang Bold); author and small mark removed, the number box kept.

    python3 make_khmer.py [--hd]
Writes khmer-2.png or khmer-2-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "fasil2-notitle-source.png"
SOURCE_HD = HERE / "fasil2-notitle-source-4x.png"

COVER = (10, 10, 674, 996)          # cover inside the screenshot's white frame (source px)
CORNER = 0

BROWN = (88, 41, 31)
# text, max width, ink height, centre x, centre y, colour, shadow, font
LINES = [
    ("ពីជំពូកមួយ", 440, 112, 340, 478, BROWN, None, "Battambang.ttf"),         # Fasıldan
    ("ទៅជំពូកមួយ", 380, 118, 340, 622, BROWN, None, "Battambang-Bold.ttf"),    # Fasıla
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
    for text, max_w, ink_h, cx, cy, colour, shadow, ff in LINES:
        f = fit(FONTS / ff, text, max_w * k, ink_h * k)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        if shadow:
            sh = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(3 * k)), round(2 * k), round(3 * k))
            im.paste(shadow, (x, y), sh.point(lambda v: int(v * 0.5)))
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
    out = HERE / f"khmer-2{'-hd' if hd else ''}.png"
    build(hd, font).save(out)
    print("wrote", out.name)
