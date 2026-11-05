"""Çağ ve Nesil 4–10 on the herkul.app covers (erase_title.py): Khmer title in the place of the script title, white
with a soft dark shadow like the original (vol 4: dark red, like its title); no author, no logo; the original number
box stays. Titles from the translations (chapter titles / title pages / forewords).

    python3 make_khmer.py [--hd] 4 5 6 7 8 9 10
Writes khmer-N.png (400x600) or khmer-N-hd.png (1600x2400).
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"
COVER = (0, 0, 400, 600)
CORNER = 8
WHITE, RED = (255, 250, 236), (128, 22, 16)

# text, max width, ink height, centre x, centre y — per volume (400x600 source px)
TITLES = {
    4: [("ចំណែកមាស", 290, 66, 200, 92), ("នៃពេលវេលា", 290, 60, 205, 165)],                 # chapter 1
    5: [("ពេលដែលថ្ងៃទាំងឡាយ", 300, 52, 205, 115), ("រសាត់ទៅរក", 300, 38, 215, 172),
        ("រដូវផ្ការីក", 280, 50, 215, 240)],                                                  # chapter 2
    6: [("គំនិត", 220, 74, 190, 128), ("ដែលដុះបៃតង", 300, 66, 205, 200)],                    # «គំនិតដែលដុះបៃតង»
    7: [("ជើងមេឃ", 220, 82, 200, 150), ("ដែលពន្លឺលេចមក", 240, 46, 200, 222)],                # «ជើងមេឃដែលពន្លឺលេចមក»
    8: [("ចលនាមួយ", 270, 60, 185, 90), ("ដែលគំរូ", 250, 60, 200, 158), ("មកពីខ្លួនឯង", 280, 60, 200, 226)],
    9: [("សំឡេងស្រែក", 280, 66, 200, 178), ("នៃភាពស្ងៀម", 280, 66, 205, 252)],
    # new Süreyya design (erase_title_10.py): gold title on the purple gradient where the Turkish title was
    10: [("ផ្លូវនៃអ្នកដែលបាន", 300, 56, 200, 392), ("ឧទ្ទិសខ្លួនចំពោះអល់ឡោះ", 340, 56, 200, 456)],   # chapter
}
GOLD = (242, 218, 84)


def fit(font_path, text, max_w, ink_h):
    size = 8
    while True:
        f = ImageFont.truetype(str(font_path), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font_path), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def build(volume="6", hd=False, font="Battambang", round_corners=True):
    v, k = int(volume), (4 if hd else 1)
    im = Image.open(HERE / f"cag-{v}-notitle-source{'-4x' if hd else ''}.png").convert("RGB")
    ink, shade = {4: (RED, (255, 236, 200)), 10: (GOLD, (30, 8, 30))}.get(v, (WHITE, (40, 20, 10)))
    for text, max_w, ink_h, cx, cy in TITLES[v]:
        f = fit(FONTS / f"{font}.ttf", text, max_w * k, ink_h * k)
        l, t, r, b = f.getbbox(text, language="km")
        pad = int(20 * k)
        w, h = r - l + 2 * pad, b - t + 2 * pad
        glyphs = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glyphs).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int(cx * k - w / 2), int(cy * k - h / 2)
        sh = ImageChops.offset(glyphs.filter(ImageFilter.GaussianBlur(2.5 * k)), round(1.5 * k), round(2 * k))
        im.paste(shade, (x, y), sh.point(lambda p: int(p * 0.6)))
        im.paste(ink, (x, y), glyphs)
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
    for v in [a for a in args if a.isdigit()] or [str(n) for n in TITLES]:
        out = HERE / f"khmer-{v}{'-hd' if hd else ''}.png"
        build(v, hd).save(out)
        print("wrote", out.name)
