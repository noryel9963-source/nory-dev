"""Restore the Arabic honorifics lost in the Prizma 8 / 9 interiors.

The translator's export set part of each honorific in the Khmer font, which has no Arabic letters: the PDF holds
.notdef glyphs (code 0xFFFF, printed as empty boxes) where the words were. Every gap is one of two fixed phrases,
next to the part that survived in Amiri:
  6 missing glyphs after «عليه»  → «السلام»     (عليه السلام, after a prophet's name)
  7 missing glyphs (3 + 4) after «ر…» → «الله عنه»  (رضي الله عنه, after a Companion's name)
The boxes are removed (redaction, text only — nothing else on the page is touched) and the words are set in
Amiri at the size of the surviving Arabic (14.9 pt), on the line's baseline, next to the surviving half (the gap's right edge).

    python3 restore_honorifics.py IN.pdf OUT.pdf
"""
import sys
from pathlib import Path

import pymupdf

FONTS = Path(__file__).resolve().parent.parent / "fonts"
WORDS = {6: "السلام", 7: "الله عنه"}
SIZE = 14.9
CSS = "@font-face {font-family: am; src: url(Amiri-Regular.ttf);} " \
      f"* {{font-family: am; font-size: {SIZE}px; line-height: 1.6; margin: 0; padding: 0;}}"
ARCH = pymupdf.Archive(str(FONTS))
AMIRI = pymupdf.Font(fontfile=str(FONTS / "Amiri-Regular.ttf"))


def runs(page):
    """Yield (count, rect, baseline_y) for each run of .notdef glyphs (spaces inside a run allowed)."""
    chars = [c for b in page.get_texttrace() for c in b["chars"]]
    i = 0
    while i < len(chars):
        if chars[i][1] != 0:
            i += 1
            continue
        j, n, rect, base = i, 0, None, chars[i][2][1]
        while j < len(chars) and (chars[j][1] == 0 or chars[j][0] == 32):
            if chars[j][1] == 0:
                n += 1
                r = pymupdf.Rect(chars[j][3])
                rect = r if rect is None else rect | r
            j += 1
        yield n, rect, base
        i = j


def baseline_offset(doc):
    """Distance from an htmlbox's top edge to the baseline of its first line (measured once)."""
    tmp = pymupdf.open()
    p = tmp.new_page(width=300, height=200)
    p.insert_htmlbox(pymupdf.Rect(0, 50, 300, 150), '<p dir="rtl">الله</p>', css=CSS, archive=ARCH)
    ys = [c[2][1] for b in p.get_texttrace() for c in b["chars"]]
    return ys[0] - 50


def main(src, dst):
    doc = pymupdf.open(src)
    off = baseline_offset(doc)
    fixed, odd = 0, []
    for pno, page in enumerate(doc):
        found = list(runs(page))
        if not found:
            continue
        for n, rect, _ in found:
            if n not in WORDS:
                odd.append((pno + 1, n))
                continue
            r = pymupdf.Rect(rect.x0 + 0.5, rect.y0 + 0.5, rect.x1 - 0.5, rect.y1 - 0.5)
            page.add_redact_annot(r, fill=False)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)
        for n, rect, base in found:
            if n not in WORDS:
                continue
            # a box just wider than the word, flush with the gap's right edge; centred text (right-aligned RTL
            # text in a wide box gets split over two lines by the layout engine)
            w = AMIRI.text_length(WORDS[n], SIZE) + 6
            box = pymupdf.Rect(rect.x1 - w, base - off, rect.x1, base - off + 40)
            page.insert_htmlbox(box, f'<p dir="rtl" style="text-align:center">{WORDS[n]}</p>',
                                css=CSS, archive=ARCH)
            fixed += 1
    doc.subset_fonts()          # each insert embeds Amiri again; subsetting keeps the file at its original size
    doc.save(dst, garbage=4, deflate=True)
    left = sum(1 for p in pymupdf.open(dst) for b in p.get_texttrace() for c in b["chars"] if c[1] == 0)
    print(f"restored {fixed} honorifics; unrecognised runs: {odd or 'none'}; .notdef glyphs left: {left}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
