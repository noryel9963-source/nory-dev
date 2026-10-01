"""Khmer edition of "Asâ-yı Mûsâ": ដំបងរបស់ / ព្យាការីមូសា (the translation's own words, chapter 1
"ផ្នែកទីមួយនៃដំបងរបស់ព្យាការីមូសា"). Gold letters with a faint dark emboss on the red velvet, like the
original; no author, no publisher logo, no "Risale-i Nur Külliyatı'ndan" line.

    python3 make_khmer.py [--hd] [--font Battambang]
Writes khmer.png (925x1437) or khmer-hd.png (3700x5748).
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "asa-notitle-source.png"
SOURCE_HD = HERE / "asa-notitle-source-4x.png"

COVER = (16, 11, 941, 1448)          # cover inside the screenshot's dark frame (source px)
CORNER = 12

# text, max width, ink height, centre x, centre y
LINES = [
    ("ដំបងរបស់", 420, 140, 478, 545),
    ("ព្យាការីមូសា", 430, 140, 478, 720),
]
GOLD = (200, 172, 108)
SHADE = (60, 8, 8)


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
    for text, max_w, ink_h, cx, cy in LINES:
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
    font = args[args.index("--font") + 1] if "--font" in args else "Battambang"
    out = HERE / f"khmer{'-hd' if hd else ''}.png"
    build(hd, font).save(out)
    print("wrote", out.name)
