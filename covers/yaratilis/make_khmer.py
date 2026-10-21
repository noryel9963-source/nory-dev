"""Khmer edition of "Yaratılış Gerçeği ve Evrim": ការពិតនៃ / ការបង្កើត / និងទ្រឹស្ដី / វិវត្តន៍ — the title printed on
the translation's title page (ការពិតនៃការបង្កើត / និងទ្រឹស្ដីវិវត្តន៍). White for "YARATILIŞ GERÇEĞİ", pink-cream for
"VE EVRİM", like the original; Battambang with a soft dark shadow. No author.

    python3 make_khmer.py [--hd]
Writes khmer.png or khmer-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "yaratilis-notitle-source.png"
SOURCE_HD = HERE / "yaratilis-notitle-source-4x.png"

COVER = (30, 20, 880, 1295)          # cover inside the screenshot's dark frame (source px)
CORNER = 14
CX = 452

WHITE, PINK = (250, 252, 253), (254, 221, 179)
SHADOW = (24, 16, 40)
# text, max width, ink height, centre y
# text, max width, ink height, centre y, colour
LINES = [
    ("ការពិតនៃ", 580, 140, 236, WHITE),        # YARATILIŞ
    ("ការបង្កើត", 580, 140, 368, WHITE),       # GERÇEĞİ
    ("និងទ្រឹស្ដី", 340, 86, 520, PINK),        # VE
    ("វិវត្តន៍", 340, 86, 612, PINK),           # EVRİM
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
    # one size per colour (the smallest fit), so the two white lines and the two pink lines match
    size = {}
    for text, max_w, ink_h, cy, colour in LINES:
        n = fit(FONTS / f"{font}.ttf", text, max_w * k, ink_h * k).size
        size[colour] = min(size.get(colour, n), n)
    for text, max_w, ink_h, cy, colour in LINES:
        f = ImageFont.truetype(str(FONTS / f"{font}.ttf"), size[colour], layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(CX * k - w / 2), int(cy * k - h / 2)
        sh = glyphs.filter(ImageFilter.GaussianBlur(4 * k)).transform(glyphs.size, Image.AFFINE,
                                                                      (1, 0, -2 * k, 0, 1, -3 * k))
        im.paste(SHADOW, (x, y), sh.point(lambda v: int(v * 0.6)))
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
