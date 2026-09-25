"""One reading PDF: front cover + interior + back cover, all at the interior's page size.

    python3 combine.py INTERIOR.pdf OUT.pdf --title "..." [--theme cag --front F.png --back B.png --spine-title ...]
Covers are cut from the same full-wrap design as the KDP print cover (without the barcode box).
"""
import argparse
import io

import pymupdf
from PIL import Image

import kdp_cover as k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("interior")
    ap.add_argument("out")
    ap.add_argument("--title", required=True, help="PDF document title")
    ap.add_argument("--theme", default="asrin", choices=list(k.THEMES))
    ap.add_argument("--front")
    ap.add_argument("--back")
    ap.add_argument("--volume", default="1")
    ap.add_argument("--spine-title", default="ការងឿងឆ្ងល់នៃយុគសម័យ")
    ap.add_argument("--spine-font", default="Moul.ttf")
    a = ap.parse_args()

    doc = pymupdf.open(a.interior)
    pw, ph = doc[0].rect.width, doc[0].rect.height
    spec = k.calc(pw / 72, ph / 72, doc.page_count, "cream")
    front = Image.open(a.front).convert("RGB") if a.front else k.default_front("khmer", a.volume)
    back = Image.open(a.back).convert("RGB") if a.back else k.default_back()
    wrap = k.build(spec, front, back, a.spine_title, "", a.volume, "", "km", a.spine_font, "Battambang.ttf",
                   barcode_box=False, theme=a.theme)
    p = spec.px
    top, bottom = p(k.BLEED), p(k.BLEED + spec.trim_h)
    panels = [wrap.crop((p(spec.spine_x1), top, p(spec.spine_x1 + spec.trim_w), bottom)),   # front
              wrap.crop((p(k.BLEED), top, p(k.BLEED + spec.trim_w), bottom))]               # back

    def page_with(im, at):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=92, dpi=(300, 300))
        pg = out.new_page(pno=at, width=pw, height=ph)
        pg.insert_image(pg.rect, stream=buf.getvalue())

    out = pymupdf.open()
    out.insert_pdf(doc)
    page_with(panels[0], 0)
    page_with(panels[1], -1)
    out.set_metadata({"title": a.title, "author": "", "creator": "", "producer": ""})
    out.save(a.out, garbage=3, deflate=True)
    print("wrote", a.out, pymupdf.open(a.out).page_count, "pages")


if __name__ == "__main__":
    main()
