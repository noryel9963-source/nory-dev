"""Khmer edition of "Cevşen-i Kebîr" (Risale-i Nur collection): الجوشن الكبير / ចាវ់ស្ហាន់អាល់ខាប៊ៀរ / ការបួងសួងមួយរយវគ្គ
ដោយព្រះនាមដ៏ល្អប្រសើររបស់អល់ឡោះ — exactly the translation's title page (Arabic + Khmer title + subtitle).
No screenshot of the Turkish cover: built on the Risale-i Nur red-velvet art erased for Asâ-yı Mûsâ (as Lem'alar,
Mektubat); "Risale-i Nur Külliyatı'ndan" and the author line stay as printed. Gold letters with a faint dark emboss;
Khmer in Battambang, the Arabic in Amiri (OFL, fonts/Amiri-Regular.ttf).

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
ASA = HERE.parent / "asa"
SOURCE = ASA / "asa-notitle-source.png"
SOURCE_HD = ASA / "asa-notitle-source-4x.png"

COVER = (16, 11, 941, 1448)          # cover inside the screenshot's dark frame (source px)
CORNER = 12
CX = 478
GOLD = (200, 172, 108)
SHADE = (60, 8, 8)

# text, font, language, max width, ink height, centre y
LINES = [
    ("الجوشن الكبير", "Amiri-Regular.ttf", "ar", 400, 120, 470),
    ("ចាវ់ស្ហាន់អាល់ខាប៊ៀរ", "Battambang.ttf", "km", 470, 104, 615),
    ("ការបួងសួងមួយរយវគ្គ", "Battambang.ttf", "km", 380, 40, 728),
    ("ដោយព្រះនាមដ៏ល្អប្រសើររបស់អល់ឡោះ", "Battambang.ttf", "km", 420, 40, 778),
]


def fit(font_path, text, lang, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language=lang)
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(hd=False, round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    sub_size = None
    for text, font, lang, max_w, ink_h, cy in LINES:
        f = fit(FONTS / font, text, lang, max_w * k, ink_h * k)
        if ink_h == 40:                       # the two subtitle lines share one size
            sub_size = min(sub_size or f.size, f.size)
    for text, font, lang, max_w, ink_h, cy in LINES:
        f = fit(FONTS / font, text, lang, max_w * k, ink_h * k)
        if ink_h == 40:
            f = ImageFont.truetype(str(FONTS / font), sub_size, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language=lang)
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language=lang)
        x, y = int(CX * k - w / 2), int(cy * k - h / 2)
        shade = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(1.5 * k)), round(1.5 * k), round(2 * k))
        im.paste(SHADE, (x, y), shade.point(lambda v: int(v * 0.55)))
        im.paste(GOLD, (x, y), glyphs)
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
