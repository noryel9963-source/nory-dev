"""Khmer edition of "Fasıldan Fasıla 5 — Fikir Atlası": the translation's title page uses the series title
ពីវគ្គមួយ / ទៅវគ្គមួយ — ភាគ ៥, so the cover does too; laid out like "fikir" (regular) / "atlası" (big bold), navy
with a soft white glow; author and the small "FASILDAN FASILA" mark removed, the number box "5" kept.

    python3 make_khmer.py [--hd]
Writes khmer-5.png or khmer-5-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "fasil5-notitle-source.png"
SOURCE_HD = HERE / "fasil5-notitle-source-4x.png"

COVER = (103, 27, 828, 1120)         # cover inside the screenshot's dark frame (source px)
CORNER = 12

NAVY = (4, 34, 90)
GLOW = (255, 255, 255)
# text, max width, ink height, centre x, centre y, colour, glow, font
LINES = [
    ("ពីវគ្គមួយ", 300, 100, 380, 398, NAVY, GLOW, "Battambang.ttf"),          # fikir
    ("ទៅវគ្គមួយ", 440, 150, 466, 552, NAVY, GLOW, "Battambang-Bold.ttf"),     # atlası
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
        if shadow:   # soft white glow around the letters, like the original
            gl = glyphs.filter(ImageFilter.MaxFilter(3 if k == 1 else 9)).filter(ImageFilter.GaussianBlur(7 * k))
            im.paste(shadow, (x, y), gl.point(lambda v: min(255, int(v * 0.9))))
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
    out = HERE / f"khmer-5{'-hd' if hd else ''}.png"
    build(hd, font).save(out)
    print("wrote", out.name)
