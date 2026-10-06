"""Khmer edition of "Enginliğiyle Bizim Dünyamız": ពិភពរបស់យើង / ក្នុងភាពធំទូលាយរបស់វា — the title printed in the
translation's title page (which has no subtitle, so the "-İktisadî Mülâhazalar-" line is dropped).
Cream letters with a soft shadow.

    python3 make_khmer.py [--hd] [--font Battambang]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "dunyamiz-notitle-source.png"
SOURCE_HD = HERE / "dunyamiz-notitle-source-4x.png"

COVER = (28, 23, 908, 1343)          # cover inside the screenshot's dark frame (source px)
CORNER = 14

CREAM = (250, 238, 210)
SHADE = (110, 45, 5)
# text, max width, ink height, centre x, centre y, colour, shadow
LINES = [
    ("ពិភពរបស់យើង", 700, 150, 465, 610, CREAM, SHADE),              # BİZİM DÜNYAMIZ
    ("ក្នុងភាពធំទូលាយរបស់វា", 620, 72, 465, 760, CREAM, SHADE),    # ENGİNLİĞİYLE
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
    for text, max_w, ink_h, cx, cy, colour, shadow in LINES:
        f = fit(FONTS / f"{font}.ttf", text, max_w * k, ink_h * k)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        if shadow:
            sh = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(3 * k)), round(2 * k), round(3 * k))
            im.paste(shadow, (x, y), sh.point(lambda v: int(v * 0.55)))
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
    out = HERE / f"khmer{'-hd' if hd else ''}.png"
    build(hd, font).save(out)
    print("wrote", out.name)
