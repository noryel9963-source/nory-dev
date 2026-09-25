"""Khmer edition of the "Prizma" (1-4) cover on the original artwork (title removed by erase_title.py).

    python3 make_khmer.py [--hd] [--font Siemreap] 1 2 3 4
Uses the no-author artwork (../erase_author.py). Writes khmer-N.png (990x1485) or khmer-N-hd.png (3960x5940).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "prizma-notitle-source-noauthor.png"
SOURCE_HD = HERE / "prizma-notitle-source-4x-noauthor.png"

COVER = (19, 9, 1009, 1494)           # cover inside the app frame (source px)
CORNER = 14

# ព្រិស្មា — "Prism": the spelling the user chose (the translation's title page has ព្រិស្ម),
# in Siemreap (Khmer OS Siemreap design), light blue-white with the original's soft dark drop shadow.
TITLE = [
    # text, max width, ink height, center x, center y, unused
    ("ព្រិស្មា", 640, 235, 508, 622, 1.0),
]
INK = (220, 240, 254)
SHADOW = (5, 20, 60)

# volume box (teal box, light cyan digit)
PATCH = (858, 1298, 975, 1430)
DIGIT_CENTER_X, DIGIT_BOTTOM, DIGIT_HEIGHT = 912.5, 1417, 109
DIGIT_COLOR = (102, 208, 224)


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
        im.paste(SHADOW, (x, y), shadow.point(lambda v: int(v * 0.6)))
        im.paste(INK, (x, y), glyphs)


def clean_box(im, k):
    x0, y0, x1, y1 = scaled(PATCH, k)
    arr = np.asarray(im).copy()
    region = arr[y0:y1, x0:x1]
    g, bl = region[..., 1].astype(int), region[..., 2].astype(int)
    digit = ((g > 150) & (bl > 165)).astype(np.uint8) * 255         # light cyan digit on the teal box
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


def build(volume, hd=False, font="Siemreap", round_corners=True):
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
    font = "Siemreap"
    if "--font" in args:
        font = args[args.index("--font") + 1]
        args = [a for a in args if a not in ("--font", font)]
    for v in [a for a in args if a != "--hd"] or ["1", "2", "3", "4"]:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd, font).save(out)
        print("wrote", out.name)
