"""Build exact-looking volume covers from the original cover image.

The artwork, title and author name are kept pixel-for-pixel from the source;
only the volume number box is repainted and a new number is drawn in it.

    python3 make_volumes.py 1 2 3 4
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
SOURCE = HERE / "asrin-getirdigi-tereddutler-1-source.webp"
FONT = HERE.parent / "fonts" / "CormorantGaramond-Medium.ttf"

# Measured on the source screenshot (836x1244 incl. the app's navy frame).
COVER = (9, 11, 824, 1232)          # left, top, right, bottom of the cover itself
CORNER = 14                         # rounded-corner radius of the cover
PATCH = (702, 1070, 800, 1188)      # region holding the original "1"
DIGIT_CENTER_X = 745
DIGIT_BOTTOM = 1169                 # bottom of the digit's baseline serif
DIGIT_HEIGHT = 91                   # cap height of the original "1"
DIGIT_COLOR = (250, 232, 178)


def clean_box(im):
    """Erase the old number by interpolating each row between its edges."""
    px = im.load()
    x0, y0, x1, y1 = PATCH
    rnd = random.Random(1)
    for y in range(y0, y1):
        left = [px[x, y] for x in range(x0 - 8, x0)]
        right = [px[x, y] for x in range(x1, x1 + 8)]
        lc = [sum(c[i] for c in left) / len(left) for i in range(3)]
        rc = [sum(c[i] for c in right) / len(right) for i in range(3)]
        for x in range(x0, x1):
            t = (x - x0) / (x1 - x0)
            n = rnd.gauss(0, 1.2)
            px[x, y] = tuple(int(lc[i] + (rc[i] - lc[i]) * t + n) for i in range(3))


def fit_font(text):
    """Pick a font size whose digit height matches the original."""
    size = 60
    while True:
        font = ImageFont.truetype(str(FONT), size)
        l, t, r, b = font.getbbox(text, features=["lnum"])
        if b - t >= DIGIT_HEIGHT:
            return font
        size += 1


def draw_number(im, number):
    font = fit_font(number)
    draw = ImageDraw.Draw(im)
    l, t, r, b = font.getbbox(number, features=["lnum"])
    x = DIGIT_CENTER_X - (l + r) / 2
    y = DIGIT_BOTTOM - b
    draw.text((x + 2, y + 2), number, font=font, fill=(70, 12, 8), features=["lnum"])   # soft shadow
    draw.text((x, y), number, font=font, fill=DIGIT_COLOR, features=["lnum"])


def rounded(im):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), CORNER, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def build(volume):
    im = Image.open(SOURCE).convert("RGB")
    if volume != "1":
        clean_box(im)
        draw_number(im, volume)
    return rounded(im.crop(COVER))


if __name__ == "__main__":
    for v in sys.argv[1:] or ["1", "2", "3", "4"]:
        out = HERE / f"asrin-getirdigi-tereddutler-{v}.png"
        build(v).save(out)
        print("wrote", out.name)
