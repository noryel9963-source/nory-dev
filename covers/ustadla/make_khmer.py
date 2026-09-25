"""Khmer edition of the "Üstad'la Hasbihal" cover (title, author and publisher logo removed).

    python3 make_khmer.py [--hd] [--font Battambang]
Writes khmer.png (1148x1782) or khmer-hd.png (2296x3564, from the 2x Real-ESRGAN upscale).
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
SOURCE = HERE / "ustadla-notitle-source.png"
SOURCE_HD = HERE / "ustadla-notitle-source-2x.png"
HD_SCALE = 2

COVER = (12, 12, 1160, 1794)          # cover inside the white margin (source px)

# ការសន្ទនាជាមួយឧស្ដាស — "Conversation with the Üstad" (Üstad'la Hasbihal); ការសន្ទនា as in the
# translation, ឧស្ដាស as the user's other Khmer texts spell Üstad. Brown, two centred lines like the original.
TITLE = [
    # text, max width, ink height, center x, center y
    ("ការសន្ទនា", 700, 135, 588, 1100),
    ("ជាមួយឧស្ដាស", 720, 135, 588, 1268),
]
INK = (108, 18, 6)
SHADOW = (60, 20, 5)


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(hd=False, font="Battambang", round_corners=False):
    k = HD_SCALE if hd else 1
    im = Image.open(SOURCE_HD if hd else SOURCE).convert("RGB")
    for text, max_w, ink_h, cx, cy in TITLE:
        f = fit(FONTS / f"{font}.ttf", text, max_w * k, ink_h * k)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        shadow = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(2 * k)), round(1.5 * k), round(2 * k))
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        im.paste(SHADOW, (x, y), shadow.point(lambda v: int(v * 0.35)))
        im.paste(INK, (x, y), glyphs)
    return im.crop(tuple(v * k for v in COVER))


if __name__ == "__main__":
    args = sys.argv[1:]
    hd = "--hd" in args
    font = args[args.index("--font") + 1] if "--font" in args else "Battambang"
    out = HERE / f"khmer{'-hd' if hd else ''}.png"
    build(hd, font).save(out)
    print("wrote", out.name)
