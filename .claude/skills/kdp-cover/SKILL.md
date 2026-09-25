---
name: kdp-cover
description: Amazon KDP paperback cover sizing and print-ready full-wrap covers (back + spine + front). Use when the user mentions KDP, Amazon print, the KDP cover calculator, spine width, bleed, barcode area, trim size, or wants a book cover ready to upload for printing.
---

# KDP paperback cover skill

Tool: `covers/kdp/kdp_cover.py` (needs Pillow, numpy, opencv-python-headless, img2pdf; Khmer text needs Pillow with libraqm).

## The rules (same as https://kdp.amazon.com/cover-calculator, paperback)

| Item | Value |
|---|---|
| Spine width | pages × paper factor: white B&W **0.002252**, cream B&W **0.0025**, standard color **0.002252**, premium color **0.002347** in/page |
| Bleed | **0.125 in** on top, bottom and both outer edges (none at the spine) |
| Full width | 0.125 + back trim width + spine + front trim width + 0.125 |
| Full height | 0.125 + trim height + 0.125 |
| Spine text | only if the book has **more than 79 pages**; keep **0.0625 in** clear on each side of spine text |
| Safe zone | text/important art **≥ 0.125 in** inside the trim (0.25 in recommended) |
| Barcode | Amazon prints it in a **2 × 1.2 in** box, lower right of the back cover, 0.25 in from the trim and spine; keep that box a solid light color |
| Minimum pages | 24 |
| Interior inside (gutter) margin | 24–150 p: **0.375 in**, 151–300: **0.5**, 301–500: **0.625**, 501–700: **0.75**, 701–828: **0.875**; outside/top/bottom ≥ 0.25 in (no bleed) |
| File | one flattened PDF, page size = full cover size, **300 DPI** images, fonts rasterized/embedded |

Worked example: 6 × 9 in, 320 pages, cream → spine 0.8000 in, full cover 13.050 × 9.250 in (3915 × 2775 px at 300 DPI).

## Commands

```bash
cd covers/kdp
python3 kdp_cover.py calc     --trim 6x9 --pages 320 --paper cream            # print all dimensions
python3 kdp_cover.py template --trim 6x9 --pages 320 --paper cream -o 6x9     # guide PNG (bleed/safe/spine/barcode)
python3 kdp_cover.py build    --trim 6x9 --pages 320 --paper cream \
        --edition khmer --volume 1 -o khmer-1-kdp                             # PNG + upload-ready PDF
```

`build` options: `--front img` / `--back img` to use any artwork, `--spine-title`, `--spine-author`,
`--blurb file.txt` (back-cover text; for Khmer insert U+200B zero-width spaces where lines may break),
`--no-barcode-box` if the user supplies their own barcode, `--theme asrin|cag` for the series band/spine colours, `--spine-font Freehand.ttf` for the spine title font.

## Interior check / fix

`python3 fix_gutter.py IN.pdf OUT.pdf [--shift 0.1]` measures inside/outside margins (odd pages = right-hand),
shifts page content outward to meet the gutter rule (vector, same page count), and removes a full-page
"paper colour" fill if the PDF has one (it would print as a grey tint and run to the edge without bleed).
`python3 combine.py INTERIOR.pdf OUT.pdf --title ...` makes a front+interior+back reading PDF.

## Always

- Ask for the **real page count** (from the final interior PDF) and paper type before building; spine width depends on it. Rebuild the cover whenever the page count changes.
- Check the interior: gutter vs page count, text ≥ 0.25 in from edges, no full-page background colour.
- Check the front artwork covers the trim **plus bleed** (the tool scale-crops it; keep text ≥ 0.25 in from edges).
- Verify: PDF MediaBox (pt) = full size × 72; spine text only if pages > 79; nothing but light fill in the barcode box.
- Hardcover (case laminate) uses different wrap/hinge rules — this tool is paperback-only; do not reuse its numbers for hardcover without checking KDP's hardcover calculator.
