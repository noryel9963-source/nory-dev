"""Make an interior pass KDP's inside-margin (gutter) rule by shifting each page's content outward.

KDP minimum inside margin by page count: 24-150: 0.375 in, 151-300: 0.5, 301-500: 0.625,
501-700: 0.75, 701-828: 0.875 (outside/top/bottom: 0.25 in without bleed).
Odd pages (right-hand) move right, even pages move left; page size and page count stay the same,
text stays vector.

    python3 fix_gutter.py IN.pdf OUT.pdf [--shift 0.1] [--keep-page-fill]

Some interiors (exported from a browser) paint a full-page cream rectangle to imitate cream paper.
In print that becomes a grey tint on every page and colour running to the trim edge (bleed), so by
default that one fill is switched off; choose cream paper in KDP instead.
"""
import argparse
import re

import pymupdf

# full-page "paper colour" fill: <r g b> rg / <gs> gs / [marked-content tag] / x y w h re / f
PAGE_FILL = re.compile(rb"(\.9686 \.9529 \.9216 rg\n/\w+ gs\n(?:/\w+ <<[^>]*>>BDC\n)?[-\d. ]+ re\n)f\n")

GUTTER = [(150, .375), (300, .5), (500, .625), (700, .75), (828, .875)]


def required(pages):
    return next(m for lim, m in GUTTER if pages <= lim)


def margins(doc):
    W = doc[0].rect.width
    inside, outside = [], []
    for i, p in enumerate(doc):
        blocks = [b for b in p.get_text("blocks") if b[4].strip()]
        if not blocks:
            continue
        left, right = min(b[0] for b in blocks) / 72, (W - max(b[2] for b in blocks)) / 72
        odd = i % 2 == 0
        inside.append(left if odd else right)
        outside.append(right if odd else left)
    return min(inside), min(outside)


def remove_page_fill(doc):
    removed = 0
    for page in doc:
        for xref in page.get_contents():
            data = doc.xref_stream(xref)
            new, n = PAGE_FILL.subn(rb"\1n\n", data, count=1)
            if n:
                doc.update_stream(xref, new)
                removed += n
                break
    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--shift", type=float)
    ap.add_argument("--keep-page-fill", action="store_true")
    a = ap.parse_args()

    src = pymupdf.open(a.src)
    if not a.keep_page_fill:
        print(f"removed full-page cream fill on {remove_page_fill(src)} of {src.page_count} pages")
    need = required(src.page_count)
    ins, outs = margins(src)
    shift = a.shift if a.shift is not None else max(0.0, round(need - ins + 0.02, 3))
    print(f"{src.page_count} pages: inside {ins:.3f} in (KDP needs {need}), outside {outs:.3f} in -> shift {shift} in")
    if outs - shift < 0.25:
        raise SystemExit("shift would push text into the 0.25 in outside margin; needs re-typesetting instead")

    out = pymupdf.open()
    dx = shift * 72
    for i, p in enumerate(src):
        r = p.rect
        page = out.new_page(width=r.width, height=r.height)
        off = dx if i % 2 == 0 else -dx
        page.show_pdf_page(pymupdf.Rect(off, 0, r.width + off, r.height), src, i, clip=r)
    out.set_metadata(src.metadata)
    out.save(a.dst, garbage=3, deflate=True)
    ins2, outs2 = margins(pymupdf.open(a.dst))
    print(f"after: inside {ins2:.3f} in, outside {outs2:.3f} in ->", "OK" if ins2 >= need and outs2 >= 0.25 else "CHECK")


if __name__ == "__main__":
    main()
