"""Khmer edition of the "Çağ ve Nesil" cover on the original artwork (title removed by erase_title.py).

    python3 make_khmer.py [--hd] [--font Freehand] 1 2 ...
Uses the no-author artwork (../erase_author.py). Writes khmer-N.png (1049x1570) or khmer-N-hd.png (4196x6280).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "cag-ve-nesil-notitle-source-noauthor.png"
SOURCE_HD = HERE / "cag-ve-nesil-notitle-source-4x-noauthor.png"

COVER = (30, 18, 1079, 1588)          # cover inside the app frame (source px)
CORNER = 18

# សម័យកាល និងជំនាន់ — "The Era and the Generation"; laid out like the original
# (big word upper left, small connector in the middle, big word lower right).
TITLE = [
    # text, max width, ink height, center x, center y, font scale
    ("សម័យកាល", 470, 170, 440, 965, 1.0),
    ("និង", 110, 70, 520, 1090, 0.45),
    ("ជំនាន់", 400, 175, 745, 1150, 1.0),
]
INK = (18, 12, 8)

# volume box
PATCH = (930, 1382, 1020, 1520)
DIGIT_CENTER_X, DIGIT_BOTTOM, DIGIT_HEIGHT = 973.5, 1507, 116
DIGIT_COLOR = (80, 137, 190)


def scaled(v, k):
    return tuple(int(round(c * k)) for c in v) if isinstance(v, tuple) else int(round(v * k))


def fit(font_path, text, max_w, ink_h, lang="km", features=None):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language=lang, features=features)
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def draw_title(im, k, font_path):
    for text, max_w, ink_h, cx, cy, _ in TITLE:
        font = fit(font_path, text, max_w * k, ink_h * k)
        l, t, r, b = font.getbbox(text, language="km")
        pad = int(30 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=font, fill=255, language="km")
        # soft drop shadow like the original calligraphy
        shadow = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(5 * k)), round(5 * k), round(6 * k))
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        im.paste((90, 60, 30), (x, y), shadow.point(lambda v: int(v * 0.55)))
        im.paste(INK, (x, y), glyphs)


def clean_box(im, k):
    x0, y0, x1, y1 = scaled(PATCH, k)
    arr = np.asarray(im).copy()
    region = arr[y0:y1, x0:x1]
    b = region[..., 2].astype(int) - region[..., 0].astype(int)
    digit = ((region[..., 2] > 150) & (b > 80)).astype(np.uint8) * 255
    grow = 2 * scaled(4, k) + 1
    mask = cv2.dilate(digit, np.ones((grow, grow), np.uint8))
    arr[y0:y1, x0:x1] = cv2.inpaint(region, mask, scaled(6, k), cv2.INPAINT_TELEA)
    return Image.fromarray(arr)


def draw_number(im, number, k):
    font = fit(FONTS / "CormorantGaramond-Medium.ttf", number, 400 * k, DIGIT_HEIGHT * k, None, ["lnum"])
    l, t, r, b = font.getbbox(number, features=["lnum"])
    ImageDraw.Draw(im).text((DIGIT_CENTER_X * k - (l + r) / 2, DIGIT_BOTTOM * k - b), number, font=font,
                            fill=DIGIT_COLOR, features=["lnum"])


def rounded(im, k):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), CORNER * k, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


def build(volume, hd=False, font="Freehand", round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    draw_title(im, k, FONTS / f"{font}.ttf")
    # always redraw the number: the HD upscale left streaks around the original "1"
    im = clean_box(im, k)
    draw_number(im, volume, k)
    im = im.crop(scaled(COVER, k))
    return rounded(im, k) if round_corners else im


if __name__ == "__main__":
    args = sys.argv[1:]
    hd = "--hd" in args
    font = "Freehand"
    if "--font" in args:
        font = args[args.index("--font") + 1]
        args = [a for a in args if a not in ("--font", font)]
    for v in [a for a in args if a != "--hd"] or ["1"]:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd, font).save(out)
        print("wrote", out.name)
