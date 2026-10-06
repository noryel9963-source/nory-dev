"""Khmer edition of the "Zekât" cover (İbadet Hayatımız series like namaz/; all text, author and publisher logo
removed). Proposed title (no translation yet), built from the translators' own words: ហ្សាកាត់ (zakat: "បរិច្ចាគហ្សាកាត់"), យុត្តិធម៌សង្គម (social justice), ធាតុគ្រឹះ (basic element).
Series line as on Namaz: ជីវិតនៃការគោរពប្រណិប័តន៍របស់យើង.

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "zekat-notitle-source.png"
SOURCE_HD = HERE / "zekat-notitle-source-4x.png"

COVER = (35, 21, 829, 1215)
CORNER = 12
CX = 432

# text, font, max width, ink height, centre y, colour, shadow colour (None = no shadow)
LINES = [
    ("ជីវិតនៃការគោរពប្រណិប័តន៍របស់យើង", "Battambang.ttf", 300, 22, 73, (95, 50, 48), None),  # İbadet Hayatımız
    ("ធាតុគ្រឹះនៃយុត្តិធម៌សង្គម", "Battambang.ttf", 480, 42, 132, (70, 35, 32), None),  # Sosyal Adaletin Temel Unsuru
    ("ហ្សាកាត់", "Battambang.ttf", 500, 124, 250, (255, 255, 255), (110, 40, 50)),  # ZEKÂT
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
