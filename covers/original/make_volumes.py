"""Build exact-looking volume covers from the original cover image.

The artwork, title and author name are kept pixel-for-pixel from the source;
only the volume number box is repainted and a new number is drawn in it.

    python3 make_volumes.py 1 2 3 4          # 815x1221, from the screenshot
    python3 make_volumes.py --hd 1 2 3 4     # 3260x4884, from the 4x AI upscale (run upscale.py first)
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
SOURCE = HERE / "asrin-getirdigi-tereddutler-1-source.webp"
SOURCE_HD = HERE / "asrin-getirdigi-tereddutler-1-source-4x.png"
FONT = HERE.parent / "fonts" / "CormorantGaramond-Medium.ttf"

# Measured on the source screenshot (836x1244 incl. the app's navy frame).
COVER = (9, 11, 824, 1232)          # left, top, right, bottom of the cover itself
CORNER = 14                         # rounded-corner radius of the cover
PATCH = (702, 1070, 800, 1188)      # region holding the original "1"
DIGIT_CENTER_X = 745
DIGIT_BOTTOM = 1169                 # bottom of the digit's baseline serif
DIGIT_HEIGHT = 91                   # cap height of the original "1"
DIGIT_COLOR = (250, 232, 178)


def scaled(v, k):
    return tuple(int(round(c * k)) for c in v) if isinstance(v, tuple) else int(round(v * k))


def clean_box(im, k):
    """Erase the old number: inpaint only the (dilated) digit pixels inside PATCH."""
    x0, y0, x1, y1 = scaled(PATCH, k)
    arr = np.asarray(im).copy()
    region = arr[y0:y1, x0:x1]
    bright = (region.astype(int).sum(axis=2) > 450).astype(np.uint8) * 255
    grow = 2 * scaled(4, k) + 1
    mask = cv2.dilate(bright, np.ones((grow, grow), np.uint8))
    arr[y0:y1, x0:x1] = cv2.inpaint(region, mask, scaled(6, k), cv2.INPAINT_TELEA)
    return Image.fromarray(arr)


def fit_font(text, height):
    """Pick a font size whose digit height matches the original."""
    size = int(height * 0.6)
    while True:
        font = ImageFont.truetype(str(FONT), size)
        l, t, r, b = font.getbbox(text, features=["lnum"])
        if b - t >= height:
            return font
        size += 1


def draw_number(im, number, k):
    font = fit_font(number, DIGIT_HEIGHT * k)
    draw = ImageDraw.Draw(im)
    l, t, r, b = font.getbbox(number, features=["lnum"])
    x = DIGIT_CENTER_X * k - (l + r) / 2
    y = DIGIT_BOTTOM * k - b
    draw.text((x + 2 * k, y + 2 * k), number, font=font, fill=(70, 12, 8), features=["lnum"])   # soft shadow
    draw.text((x, y), number, font=font, fill=DIGIT_COLOR, features=["lnum"])


def rounded(im, k):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), CORNER * k, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def build(volume, hd=False):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    if volume != "1":
        im = clean_box(im, k)
        draw_number(im, volume, k)
    return rounded(im.crop(scaled(COVER, k)), k)


if __name__ == "__main__":
    args = sys.argv[1:]
    hd = "--hd" in args
    volumes = [a for a in args if a != "--hd"] or ["1", "2", "3", "4"]
    for v in volumes:
        out = HERE / f"asrin-getirdigi-tereddutler-{v}{'-hd' if hd else ''}.png"
        build(v, hd).save(out)
        print("wrote", out.name)
