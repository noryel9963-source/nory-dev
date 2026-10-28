"""Khmer edition of Faruk Mercan's "M. Fethullah Gülen": the title page reads ជីវប្រវត្តិ / Fethullah Gülen, so the
original black "M. FETHULLAH GÜLEN" stays and ជីវប្រវត្តិ ("biography") replaces the white script "Allah yolunda bir
ömür"; white Battambang Bold with a soft dark shadow. No author name (FARUK MERCAN is erased).

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "omur-notitle-source.png"
SOURCE_HD = HERE / "omur-notitle-source-4x.png"

COVER = (27, 21, 981, 1482)          # cover inside the screenshot's white frame (source px)
CORNER = 0
CX = 505

INK = (255, 255, 255)
SHADOW = (8, 8, 14)
# text, max width, ink height, centre y
LINES = [
    ("ជីវប្រវត្តិ", 640, 190, 1090),     # Allah yolunda bir ömür
]


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(hd=False, font="Battambang-Bold", round_corners=True):
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
        im.paste(SHADOW, (x, y), sh.point(lambda v: int(v * 0.85)))
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
    font = args[args.index("--font") + 1] if "--font" in args else "Battambang-Bold"
    out = HERE / f"khmer{'-hd' if hd else ''}.png"
    build(hd, font).save(out)
    print("wrote", out.name)
