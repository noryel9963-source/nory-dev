"""Gülen Felsefesinde Barış İçinde Birlikte Yaşama ve İnsanî Diyalog (Abdullah Yüca): no original cover was available,
so the front is designed (front.tex, rendered by front-doc.tex): ការរួមរស់ដោយសន្តិភាព / និងការសន្ទនារវាងមនុស្សជាតិ with
ក្នុងទស្សនវិជ្ជារបស់ Gülen — the translation's title page. Vector art, rendered at 600 dpi instead of upscaled.

    xelatex front-doc.tex && xelatex front-doc.tex
    python3 make_khmer.py [--hd]
Writes khmer.png (1/4 size) or khmer-hd.png.
"""
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

HERE = Path(__file__).parent
PDF = HERE / "front-doc.pdf"
HD = HERE / "baris-front-600dpi.png"
CORNER = 14


def render():
    pix = pymupdf.open(PDF)[0].get_pixmap(dpi=600)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return im.crop((0, 0, im.width // 4 * 4, im.height // 4 * 4))   # whole multiple of the 1x size


if not HD.exists() or PDF.stat().st_mtime > HD.stat().st_mtime:
    render().save(HD)
_W, _H = Image.open(HD).size
COVER = (0, 0, _W // 4, _H // 4)


def build(hd=False, round_corners=True):
    im = Image.open(HD).convert("RGB")
    if not hd:
        im = im.resize((COVER[2], COVER[3]), Image.LANCZOS)
    if not round_corners:
        return im
    k = 4 if hd else 1
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), CORNER * k, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


if __name__ == "__main__":
    hd = "--hd" in sys.argv[1:]
    out = HERE / f"khmer{'-hd' if hd else ''}.png"
    build(hd).save(out)
    print("wrote", out.name)
