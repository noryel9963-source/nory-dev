"""Khmer edition of the "Namaz" cover (İbadet Hayatımız series; all text, author and publisher logo removed).

    python3 make_khmer.py [--hd]
Writes khmer.png (815x1229) or khmer-hd.png (3260x4916).
Terms as the user's Khmer translations write them: សឡាត (namaz), មៀរ៉ាជ (Miraç),
ការគោរពប្រណិប័តន៍ (ibadet).
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "namaz-notitle-source.png"
SOURCE_HD = HERE / "namaz-notitle-source-4x.png"

COVER = (20, 16, 835, 1245)
CORNER = 12
CX = 421

# text, font, max width, ink height, centre y, colour, shadow colour (None = no shadow)
LINES = [
    ("ជីវិតនៃការគោរពប្រណិប័តន៍របស់យើង", "Hanuman.ttf", 330, 24, 135, (150, 138, 18), None),        # İbadet Hayatımız
    ("ការគោរពប្រណិប័តន៍ដ៏ជ្រាលជ្រៅដូចមៀរ៉ាជ", "Freehand.ttf", 460, 44, 210, (38, 28, 0), None),  # Miraç Enginlikli İbadet
    ("សឡាត", "Battambang.ttf", 520, 120, 305, (255, 255, 255), (40, 50, 20)),                      # NAMAZ
]


def fit(font_path, text, max_w, ink_h):
    size = 6
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(hd=False, round_corners=True):
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
    im = im.crop(tuple(v * k for v in COVER))
    if not round_corners:
        return im
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), CORNER * k, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


if __name__ == "__main__":
    hd = "--hd" in sys.argv
    out = HERE / f"khmer{'-hd' if hd else ''}.png"
    build(hd).save(out)
    print("wrote", out.name)
