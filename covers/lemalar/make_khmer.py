"""Khmer edition of "Lem'alar" (Risale-i Nur), split into two volumes: ពន្លឺទាំងឡាយ (the translation's own title,
interior pp 1 and 3) + ភាគទី ១ / ភាគទី ២. Built on the Risale-i Nur red-velvet art erased for Asâ-yı Mûsâ (same
series design): "Risale-i Nur Külliyatı'ndan" and the author stay as printed (Risale-i Nur rule), no logo.
Gold letters with a faint dark emboss, like asa/make_khmer.py.

    python3 make_khmer.py [--hd] 1|2
Writes khmer-N.png or khmer-N-hd.png.
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
KH_DIGITS = "០១២៣៤៥៦៧៨៩"

GOLD = (200, 172, 108)
SHADE = (60, 8, 8)


def lines(volume):
    # text, max width, ink height, centre x, centre y
    return [
        ("ពន្លឺទាំងឡាយ", 470, 150, 478, 590),
        (f"ភាគទី {''.join(KH_DIGITS[int(c)] for c in str(volume))}", 260, 66, 478, 735),
    ]


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(volume, hd=False, font="Battambang", round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    for text, max_w, ink_h, cx, cy in lines(volume):
        f = fit(FONTS / f"{font}.ttf", text, max_w * k, ink_h * k)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
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
    args = sys.argv[1:]
    hd = "--hd" in args
    vol = next(a for a in args if a.isdigit())
    out = HERE / f"khmer-{vol}{'-hd' if hd else ''}.png"
    build(vol, hd).save(out)
    print("wrote", out.name)
