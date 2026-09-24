"""Khmer-title version of the cover, on the original artwork with the Turkish title erased.

    python3 make_khmer.py                 # volumes 1-4, 815x1221
    python3 make_khmer.py --hd 1 2        # HD 3260x4884 (needs the -notitle-source-4x.png upscale)
    python3 make_khmer.py --font Koulen 1

Pipeline: erase_title.py (LaMa) -> upscale.py (Real-ESRGAN, for --hd) -> this script.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import make_volumes as mv

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "asrin-getirdigi-tereddutler-notitle-source.png"
SOURCE_HD = HERE / "asrin-getirdigi-tereddutler-notitle-source-4x.png"

# ការងឿងឆ្ងល់នៃយុគសម័យ — "The Doubts/Perplexities of the Era"
TITLE = ["ការងឿងឆ្ងល់", "នៃយុគសម័យ"]
# (max width, target ink height, vertical center) per line, in source coords
LINES = [(700, 185, 655), (640, 130, 835)]
CENTER_X = 425
FILL_TOP, FILL_BOTTOM = (255, 250, 232), (226, 192, 132)   # cream -> gold, like the original
OUTLINE = (58, 22, 8)


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        font = ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = font.getbbox(text, language="km")
        if (r - l) > max_w or (b - t) > ink_h:
            return ImageFont.truetype(str(font_path), size - 1, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def draw_title(im, k, font_path):
    for text, (max_w, ink_h, cy) in zip(TITLE, LINES):
        font = fit(font_path, text, max_w * k, ink_h * k)
        l, t, r, b = font.getbbox(text, language="km")
        pad = int(40 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        origin = (-l + pad, -t + pad)
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text(origin, text, font=font, fill=255, language="km")
        outline = Image.new("L", (w, h), 0)
        ImageDraw.Draw(outline).text(origin, text, font=font, fill=255, language="km",
                                     stroke_width=max(1, round(1.2 * k)), stroke_fill=255)
        shadow = outline.filter(ImageFilter.GaussianBlur(4 * k))
        shadow = ImageChops.offset(shadow, round(3 * k), round(4 * k))

        grad = np.linspace(0, 1, h)[:, None, None]
        fill = (np.array(FILL_TOP) * (1 - grad) + np.array(FILL_BOTTOM) * grad).astype(np.uint8)
        fill = Image.fromarray(np.broadcast_to(fill, (h, w, 3)).copy())

        x = int(CENTER_X * k - w / 2)
        y = int(cy * k - h / 2)
        im.paste((0, 0, 0), (x, y), shadow.point(lambda v: int(v * 0.85)))
        im.paste(OUTLINE, (x, y), outline)
        im.paste(fill, (x, y), glyphs)


def build(volume, hd=False, font="Moul"):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    draw_title(im, k, FONTS / f"{font}.ttf")
    if volume != "1":
        im = mv.clean_box(im, k)
        mv.draw_number(im, volume, k)
    return mv.rounded(im.crop(mv.scaled(mv.COVER, k)), k)


if __name__ == "__main__":
    args = sys.argv[1:]
    hd = "--hd" in args
    font = "Moul"
    if "--font" in args:
        font = args[args.index("--font") + 1]
        args = [a for a in args if a not in ("--font", font)]
    volumes = [a for a in args if a != "--hd"] or ["1", "2", "3", "4"]
    for v in volumes:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd, font).save(out)
        print("wrote", out.name)
