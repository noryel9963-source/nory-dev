"""Khmer edition of "İnancın Gölgesinde" 1–2: នៅក្រោមម្លប់ / នៃជំនឿ (the translation's title, "នៅក្រោមម្លប់នៃជំនឿ ភាគទី ១ / ២"),
white letters with a red outline and a soft shadow, like the original; author removed. Volume 2 has the same cover
with "2" in the number box: the box is a flat yellow, so its "1" is painted over and the number redrawn in
Cormorant Garamond (red, same height).

    python3 make_khmer.py [--hd] 1|2
Writes khmer-N.png or khmer-N-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "inanc-notitle-source.png"
SOURCE_HD = HERE / "inanc-notitle-source-4x.png"

COVER = (33, 20, 726, 1060)          # cover inside the screenshot's dark frame (source px)
CORNER = 12

WHITE = (255, 255, 255)
RED = (176, 30, 40)
SHADE = (110, 30, 10)
# text, max width, ink height, centre x, centre y
LINES = [
    ("នៅក្រោមម្លប់", 470, 150, 380, 205),     # İNANCIN
    ("នៃជំនឿ", 420, 140, 380, 368),           # GÖLGESİNDE
]

NUM_AREA = (632, 922, 700, 1016)     # the printed "1" with a margin, inside the flat yellow box
BOX_YELLOW = (231, 184, 92)
NUM_INK, NUM_CENTRE, NUM_COLOUR = 79, (659, 968.5), (170, 48, 36)


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def renumber(im, volume, k):
    ImageDraw.Draw(im).rectangle(tuple(v * k for v in NUM_AREA), fill=BOX_YELLOW)
    text = str(volume)
    size = 10
    f = ImageFont.truetype(str(FONTS / "CormorantGaramond-Medium.ttf"), size)
    while f.getbbox(text)[3] - f.getbbox(text)[1] < NUM_INK * k:
        size += 1
        f = ImageFont.truetype(str(FONTS / "CormorantGaramond-Medium.ttf"), size)
    l, t, r, b = f.getbbox(text)
    cx, cy = NUM_CENTRE
    ImageDraw.Draw(im).text((cx * k - (l + r) / 2, cy * k - (t + b) / 2), text, font=f, fill=NUM_COLOUR)
    return im


def build(volume, hd=False, font="Battambang", round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    if str(volume) != "1":
        im = renumber(im, volume, k)
    sizes = [fit(FONTS / f"{font}.ttf", t, w * k, h * k).size for t, w, h, _, _ in LINES]
    stroke = round(2.5 * k)
    for text, max_w, ink_h, cx, cy in LINES:
        f = ImageFont.truetype(str(FONTS / f"{font}.ttf"), min(sizes), layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km", stroke_width=stroke)
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        outline = Image.new("L", (w, h), 0)
        ImageDraw.Draw(outline).text((-l + pad, -t + pad), text, font=f, fill=255, language="km",
                                     stroke_width=stroke, stroke_fill=255)
        fill = Image.new("L", (w, h), 0)
        ImageDraw.Draw(fill).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        sh = ImageChops.offset(outline.filter(ImageFilter.GaussianBlur(3 * k)), round(2 * k), round(3 * k))
        im.paste(SHADE, (x, y), sh.point(lambda v: int(v * 0.55)))
        im.paste(RED, (x, y), outline)
        im.paste(WHITE, (x, y), fill)
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
    vol = next(a for a in args if a.isdigit())
    out = HERE / f"khmer-{vol}{'-hd' if hd else ''}.png"
    build(vol, hd, font).save(out)
    print("wrote", out.name)
