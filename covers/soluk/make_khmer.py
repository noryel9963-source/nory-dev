"""Khmer edition of "Kalbin Solukları": ដង្ហើម / នៃដួងចិត្ត (soluk = breath, ដង្ហើម; kalp = heart, ដួងចិត្ត as in
ភ្នំមរកតនៃដួងចិត្ត) — the title the translation's text layer carries (title page and the chapter of the same name).
Navy letters with a soft white glow, laid out like the original two lines. No author.

    python3 make_khmer.py [--hd] [--font Battambang]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "soluk-notitle-source.png"
SOURCE_HD = HERE / "soluk-notitle-source-4x.png"

COVER = (22, 21, 744, 1093)          # cover inside the screenshot's dark frame (source px)
CORNER = 12

NAVY = (26, 48, 71)
GLOW = (255, 255, 255)
# text, max width, ink height, centre x, centre y
LINES = [
    ("ដង្ហើម", 500, 104, 384, 548),           # KALBİN
    ("នៃដួងចិត្ត", 500, 104, 384, 646),       # SOLUKLARI
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
    sizes = [fit(FONTS / f"{font}.ttf", t, w * k, h * k).size for t, w, h, _, _ in LINES]
    for text, max_w, ink_h, cx, cy in LINES:
        f = ImageFont.truetype(str(FONTS / f"{font}.ttf"), min(sizes), layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(30 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        glow = glyphs.filter(ImageFilter.MaxFilter(3 if k == 1 else 9)).filter(ImageFilter.GaussianBlur(9 * k))
        im.paste(GLOW, (x, y), glow.point(lambda v: min(255, int(v * 1.1))))
        im.paste(NAVY, (x, y), glyphs)
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
