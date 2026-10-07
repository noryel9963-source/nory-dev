"""Make a printer package (zip) for finished books: interior PDF + full-wrap cover for cream and for white paper +
PRINT-INFO.txt (Khmer + English: size, pages, binding, bleed, spine widths, ask for the printer's own spine).

    python3 print_package.py prizma-6 cag-1 ...     # keys from rebuild_all.BOOKS
Writes ../print/<key>-print.zip (covers/print/ is git-ignored: the files are copies of committed/Drive files).
"""
import shutil
import sys
import zipfile
from pathlib import Path

import pymupdf

from rebuild_all import BOOKS, KDP, KDP_INTERIOR, COVERS

OUT = COVERS / "print"
SIZE_NAME = {"5.833x8.263": "A5", "6.929x9.842": "B5"}
SPINE_IN = {"cream": 0.0025, "white": 0.002252}


def mm(inches):
    return inches * 25.4


def package(key):
    folder, volume, _, trim, pages, theme, spine, out, interior, title = BOOKS[key]
    src = COVERS / "interior" / f"{interior}-interior{'-kdp' if key in KDP_INTERIOR else ''}.pdf"
    doc = pymupdf.open(src)
    assert doc.page_count == pages, f"{key}: interior has {doc.page_count} pages, rebuild_all says {pages}"
    w_in, h_in = (float(v) for v in trim.split("x"))
    size = SIZE_NAME.get(trim, trim + " in")
    d = OUT / key
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    shutil.copy(src, d / f"1-INTERIOR-{size}-{pages}pages.pdf")
    lines = []
    for paper in ("cream", "white"):
        cover = KDP / f"{out}-{paper}.pdf"
        shutil.copy(cover, d / f"2-COVER-{paper}-paper.pdf")
        r = pymupdf.open(cover)[0].rect
        lines.append(f"  {paper.capitalize():5} file : {r.width / 72 * 25.4:.1f} × {r.height / 72 * 25.4:.1f} mm, "
                     f"spine {mm(pages * SPINE_IN[paper]):.1f} mm ({SPINE_IN[paper]} in per page)")
    km_paper = {"cream": "ក្រែម", "white": "ស"}
    (d / "PRINT-INFO.txt").write_text(f"""{title}  ({key}) — PRINT SPECIFICATION / ព័ត៌មានសម្រាប់ការបោះពុម្ព
{'=' * 86}

FILES / ឯកសារ
  1-INTERIOR-{size}-{pages}pages.pdf   Inside pages / ទំព័រខាងក្នុង — {pages} pages, black only / ខ្មៅតែមួយពណ៌
  2-COVER-cream-paper.pdf      Full cover for CREAM paper / គម្របពេញ សម្រាប់ក្រដាសពណ៌{km_paper['cream']}
  2-COVER-white-paper.pdf      Full cover for WHITE paper / គម្របពេញ សម្រាប់ក្រដាសពណ៌{km_paper['white']}
  -> Use ONE cover file only, the one that matches the paper. / ប្រើគម្របតែមួយ ដែលត្រូវនឹងក្រដាស។

BOOK / សៀវភៅ
  Finished size / ទំហំ        : {size} — {mm(w_in):.0f} × {mm(h_in):.0f} mm
  Pages / ចំនួនទំព័រ          : {pages} ({(pages + 1) // 2} sheets / សន្លឹក)
  Binding / ការចង            : Perfect bound (glued spine) / ចងកាវខ្នង
  Interior print / ខាងក្នុង   : Black & white / ស-ខ្មៅ — print at 100 %, do NOT scale (binding margin already inside)
  Cover print / គម្រប         : Full colour (CMYK), one side; matte or gloss lamination / ពណ៌ពេញ ស្រោបមែត ឬភ្លឺ

COVER SHEET / សន្លឹកគម្រប (back + spine + front, one page)
  Bleed / ផ្នែកកាត់ចោល        : 3.2 mm (0.125 in) on every edge — trim it off / កាត់ចេញគ្រប់ជ្រុង
{chr(10).join(lines)}

IMPORTANT FOR THE PRINTER / សំខាន់សម្រាប់រោងពុម្ព
  The spine widths above are for Amazon KDP paper. If your paper is thicker or thinner, the spine must change.
  Please tell us your spine width (mm) for {pages} pages — we will send a corrected cover.
  ទំហំខ្នងខាងលើ គណនាតាមក្រដាសរបស់ Amazon KDP។ ប្រសិនបើក្រដាសរបស់លោកអ្នកក្រាស់ ឬស្តើងជាងនេះ
  សូមប្រាប់ទំហំខ្នង (មម) សម្រាប់ {pages} ទំព័រ — យើងនឹងផ្ញើគម្របថ្មីដែលត្រូវទំហំ។
""", encoding="utf-8")
    z = OUT / f"{key}-print.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(d.iterdir()):
            zf.write(f, f"{key}/{f.name}")
    print("wrote", z.relative_to(COVERS), f"({z.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    for k in sys.argv[1:]:
        package(k)
