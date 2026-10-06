"""Khmer edition of the "Hac" cover (İbadet Hayatımız series like namaz/; all text, author and publisher logo
removed). Proposed title (no translation yet), built from the translators' own words: ហាជ្ជ (hajj: "ធ្វើហាជ្ជទៅពៃទុលឡោះ"), ការឆ្លើយតប (answer), ការអំពាវនាវ (call, as in Hitap Çiçekleri).
Series line as on Namaz: ជីវិតនៃការគោរពប្រណិប័តន៍របស់យើង.

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "hac-notitle-source.png"
SOURCE_HD = HERE / "hac-notitle-source-4x.png"

COVER = (37, 29, 822, 1232)
CORNER = 12
CX = 430

# text, font, max width, ink height, centre y, colour, shadow colour (None = no shadow)
LINES = [
    ("ជីវិតនៃការគោរពប្រណិប័តន៍របស់យើង", "Battambang.ttf", 290, 22, 104, (240, 212, 228), None),  # İbadet Hayatımız
    ("ការឆ្លើយតបនឹងការអំពាវនាវរបស់អល់ឡោះ", "Battambang.ttf", 440, 40, 165, (60, 20, 40), None),  # İlâhî Davete İcabet
    ("ហាជ្ជ", "Battambang.ttf", 380, 124, 272, (255, 255, 255), (80, 20, 60)),  # HAC
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
