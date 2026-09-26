"""Khmer edition of "Buhranlı Günler ve Ümit Atlasımız" (Kırık Testi 14): ថ្ងៃនៃវិបត្តិ និងផែនទីក្ដីសង្ឃឹមរបស់យើង (proposed).
Orange first half, pale gold second half, on the right like the original.

    python3 make_khmer.py [--hd] 1 2 ...
Writes khmer-N.png (799x1196) or khmer-N-hd.png (3196x4784). Default volume 14.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "kirik-notitle-source.png"
SOURCE_HD = HERE / "kirik-notitle-source-4x.png"

COVER = (29, 4, 826, 1194)
CORNER = 12
CX = 588

# text, font, max width, ink height, centre y, colour, shadow colour (None = no shadow)
LINES = [
    ("ថ្ងៃនៃ", "Suwannaphum-Regular.ttf", 240, 80, 300, (238, 133, 54), None),           # buhranlı
    ("វិបត្តិ", "Suwannaphum-Regular.ttf", 260, 100, 395, (238, 133, 54), None),         # günler
    ("និង", "Suwannaphum-Regular.ttf", 110, 45, 478, (238, 133, 54), None),             # ve
    ("ផែនទីក្ដីសង្ឃឹម", "Suwannaphum-Regular.ttf", 330, 110, 570, (244, 204, 109), None),  # ümit
    ("របស់យើង", "Suwannaphum-Regular.ttf", 300, 95, 685, (244, 204, 109), None),        # atlasımız
]

# number box: big orange digit with the series name in small letters on both sides (like "KIRIK 1 TESTİ")
NUM_CX, NUM_BOTTOM, NUM_H = 738, 1128, 72
NUM_COLOR = (223, 144, 49)
SIDE = [("ក្អម", 681, 1106), ("បែក", 808, 1106)]    # text, centre x, centre y
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
    for v in [a for a in args if a != "--hd"] or ["14"]:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd).save(out)
        print("wrote", out.name)
