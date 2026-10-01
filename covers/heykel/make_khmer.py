"""Khmer edition of "Ruhumuzun Heykelini Dikerken": នៅពេលតាំង / រូបសំណាកនៃ / ព្រលឹងរបស់យើង
(the translation's own heading, confirmed by the user). White title with a soft dark halo on the sky, like the
original script; no author; the number redrawn in the red box.

    python3 make_khmer.py [--hd] [--font Battambang] 1 2 ...
Writes khmer-N.png (921x1385) or khmer-N-hd.png (3684x5540). Default volume 1.
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "heykel-notitle-source.png"
SOURCE_HD = HERE / "heykel-notitle-source-4x.png"

COVER = (33, 22, 953, 1400)          # cover inside the app frame (source px)
CORNER = 14

# text, max width, ink height, centre x, centre y — stepped to the right like the original three lines
LINES = [
    ("នៅពេលតាំង", 560, 125, 450, 235),
    ("រូបសំណាកនៃ", 560, 125, 500, 375),
    ("ព្រលឹងរបស់យើង", 620, 125, 520, 510),
]
INK = (255, 255, 255)
HALO = (6, 30, 70)

NUM_CX, NUM_BOTTOM, NUM_H = 867.5, 1354, 104
NUM_COLOR = (249, 173, 107)


def fit(font_path, text, max_w, ink_h, lang="km", features=None):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language=lang, features=features)
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(volume="1", hd=False, font="Battambang", round_corners=True):
    k = 4 if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    for text, max_w, ink_h, cx, cy in LINES:
        f = fit(FONTS / f"{font}.ttf", text, max_w * k, ink_h * k)
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
    for v in [a for a in args if a != "--hd"] or ["1"]:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd, font).save(out)
        print("wrote", out.name)
