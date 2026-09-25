"""Khmer edition of "Yaşatma İdeali" (Kırık Testi 11, new parchment design): ឧត្តមគតិ នៃការធ្វើឱ្យរស់ (proposed).
Series name ក្អមបែក goes on the gold ribbon, the number under it (no burgundy box on this design).

    python3 make_khmer.py [--hd] 1 2 ...
Writes khmer-N.png (799x1196) or khmer-N-hd.png (3196x4784). Default volume 11.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "kirik-notitle-source.png"
SOURCE_HD = HERE / "kirik-notitle-source-4x.png"

COVER = (27, 11, 824, 1219)
CORNER = 12
CX = 413

# text, font, max width, ink height, centre y, colour, shadow colour (None = no shadow)
LINES = [
    ("ឧត្តមគតិ", "Battambang.ttf", 480, 95, 187, (101, 66, 32), None),           # YAŞATMA
    ("នៃការធ្វើឱ្យរស់", "Battambang.ttf", 480, 95, 285, (101, 66, 32), None),   # İDEALİ
    ("ក្អមបែក", "Battambang.ttf", 200, 40, 380, (101, 66, 32), None),           # ribbon: KIRIK TESTİ
]

# number under the ribbon (like "11")
NUM_CX, NUM_BOTTOM, NUM_H = 416, 470, 50
NUM_COLOR = (138, 90, 43)
SIDE = []
SIDE_H = 13


def fit(font_path, text, max_w, ink_h):
    size = 6
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(volume="1", hd=False, round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    for text, font, max_w, ink_h, cy, colour, shadow in LINES:
        f = fit(FONTS / font, text, max_w * k, ink_h * k)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(16 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(CX * k - w / 2), int(cy * k - h / 2)
        if shadow:
            sh = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(3 * k)), round(3 * k), round(4 * k))
            im.paste(shadow, (x, y), sh.point(lambda v: int(v * 0.6)))
        im.paste(colour, (x, y), glyphs)
    d = ImageDraw.Draw(im)
    nf = ImageFont.truetype(str(FONTS / "CormorantGaramond-Medium.ttf"), 10)
    size = 10
    while True:
        nf = ImageFont.truetype(str(FONTS / "CormorantGaramond-Medium.ttf"), size + 1)
        l, t, r, b = nf.getbbox(volume, features=["lnum"])
        if b - t > NUM_H * k:
            break
        size += 1
    nf = ImageFont.truetype(str(FONTS / "CormorantGaramond-Medium.ttf"), size)
    l, t, r, b = nf.getbbox(volume, features=["lnum"])
    d.text((NUM_CX * k - (l + r) / 2, NUM_BOTTOM * k - b), volume, font=nf, fill=NUM_COLOR, features=["lnum"])
    for text, sx, sy in SIDE:
        f = fit(FONTS / "Hanuman.ttf", text, 60 * k, SIDE_H * k)
        l, t, r, b = f.getbbox(text, language="km")
        d.text((sx * k - (l + r) / 2, sy * k - (t + b) / 2), text, font=f, fill=NUM_COLOR, language="km")
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
    for v in [a for a in args if a != "--hd"] or ["11"]:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd).save(out)
        print("wrote", out.name)
