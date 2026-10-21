"""Ruhumuzun Heykelini Dikerken 2 — "Kendi Dünyamıza Doğru": ឆ្ពោះទៅកាន់ / ពិភពផ្ទាល់ខ្លួន / របស់យើង, the subtitle
printed on the translation's title page (ពេលកសាងរូបសំណាក នៃព្រលឹងយើង ២ / ឆ្ពោះទៅកាន់ពិភពផ្ទាល់ខ្លួនរបស់យើង), which is
the cover's main title. Cream with a soft dark-brown halo, stepped right like the original; no author; the number
redrawn in the red box.

    python3 make_khmer.py [--hd] [--font Battambang] 2
Writes khmer-2.png or khmer-2-hd.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "heykel2-notitle-source.png"
SOURCE_HD = HERE / "heykel2-notitle-source-4x.png"

COVER = (24, 28, 784, 1165)          # cover inside the app frame (source px)
CORNER = 14

# text, max width, ink height, centre x, centre y — stepped to the right like the original three lines
LINES = [
    ("ឆ្ពោះទៅកាន់", 330, 110, 262, 392),
    ("ពិភពផ្ទាល់ខ្លួន", 420, 110, 450, 508),
    ("របស់យើង", 330, 110, 520, 624),
]
INK = (252, 234, 200)
HALO = (60, 20, 6)

NUM_CX, NUM_BOTTOM, NUM_H = 706.5, 1091, 59
NUM_COLOR = (250, 171, 107)


def fit(font_path, text, max_w, ink_h, lang="km", features=None):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language=lang, features=features)
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(volume="2", hd=False, font="Battambang", round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    # one size for all lines (the smallest fit), so the short first line is not larger than the others
    size = min(fit(FONTS / f"{font}.ttf", t, w * k, h * k).size for t, w, h, _, _ in LINES)
    f = ImageFont.truetype(str(FONTS / f"{font}.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    for text, max_w, ink_h, cx, cy in LINES:
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(30 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        halo = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(4 * k)), round(2 * k), round(3 * k))
        im.paste(HALO, (x, y), halo.point(lambda v: int(v * 0.6)))
        im.paste(INK, (x, y), glyphs)
    nf = fit(FONTS / "CormorantGaramond-Medium.ttf", volume, 300 * k, NUM_H * k, None, ["lnum"])
    l, t, r, b = nf.getbbox(volume, features=["lnum"])
    ImageDraw.Draw(im).text((NUM_CX * k - (l + r) / 2, NUM_BOTTOM * k - b), volume, font=nf, fill=NUM_COLOR,
                            features=["lnum"])
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
    font = "Battambang"
    if "--font" in args:
        font = args[args.index("--font") + 1]
        args = [a for a in args if a not in ("--font", font)]
    for v in [a for a in args if a != "--hd"] or ["2"]:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd, font).save(out)
        print("wrote", out.name)
