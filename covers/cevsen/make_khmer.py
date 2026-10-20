"""Khmer edition of "Cevşen-i Kebîr": الجوشن الكبير / ចាវ់ស្ហាន់អាល់ខាប៊ៀរ / ការបួងសួងមួយរយវគ្គ ដោយព្រះនាមដ៏ល្អប្រសើររបស់អល់ឡោះ
— exactly the translation's title page (Arabic + Khmer title + subtitle), on the real cover the user sent (navy
leather, gold corner ornaments, no author, no series line): "CEVŞEN" erased by erase_title.py. Gold letters with a
faint dark emboss; Khmer in Battambang, the Arabic in Amiri (OFL, fonts/Amiri-Regular.ttf).

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys

import numpy as np
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "cevsen-notitle-source.png"          # the cover only (cut out of the screenshot, upscaled 4×)
SOURCE_HD = HERE / "cevsen-notitle-source-4x.png"

COVER = (0, 0, 728, 1052)
CORNER = 10
CX = 362
GOLD = (232, 168, 76)
SHADE = (8, 10, 24)

# text, font, language, max width, ink height, centre y
LINES = [
    ("الجوشن الكبير", "Amiri-Regular.ttf", "ar", 330, 96, 432),
    ("ចាវ់ស្ហាន់អាល់ខាប៊ៀរ", "Battambang.ttf", "km", 470, 92, 545),
    ("ការបួងសួងមួយរយវគ្គ", "Battambang.ttf", "km", 330, 34, 640),
    ("ដោយព្រះនាមដ៏ល្អប្រសើររបស់អល់ឡោះ", "Battambang.ttf", "km", 400, 34, 684),
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
        if ink_h == 34:                       # the two subtitle lines share one size
            sub_size = min(sub_size or f.size, f.size)
    for text, font, lang, max_w, ink_h, cy in LINES:
        f = fit(FONTS / font, text, lang, max_w * k, ink_h * k)
        if ink_h == 34:
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
    if not round_corners:   # print (KDP): the gold frame runs ~2 % from the edge, inside the 0.125 in bleed/trim zone —
        # extend the navy leather by 5 % on every side so the frame sits safely inside the trimmed page
        a = np.asarray(im)
        edge = np.concatenate([a[:6].reshape(-1, 3), a[-6:].reshape(-1, 3), a[:, :6].reshape(-1, 3),
                               a[:, -6:].reshape(-1, 3)])
        navy = tuple(int(v) for v in np.median(edge, 0))
        px, py = round(im.width * 0.05), round(im.height * 0.05)
        out = Image.new("RGB", (im.width + 2 * px, im.height + 2 * py), navy)
        out.paste(im, (px, py))
        return out
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
