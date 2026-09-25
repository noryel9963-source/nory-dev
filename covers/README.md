# Book Cover Studio

Recreates the "Asrın Getirdiği Tereddütler" cover style entirely in code (HTML canvas):
cosmic sky with nebula and planets, sunburst through clouds, glowing lava field,
Cinzel small-caps title, script author name and a volume box.

- Open `index.html` in a browser, edit title lines / author / volumes, click **Render covers**.
- **Download PNG** under each cover saves it at 836×1244.
- `index.html?solo=2` renders only volume 2 at full size (handy for screenshots).
- `preview-1.png`, `preview-2.png` are sample renders.

Fonts (SIL Open Font License) are bundled in `fonts/`: Cinzel, Pinyon Script.

## Original-art covers (`original/`)

`original/make_volumes.py` builds volume covers straight from the original cover image, so the
artwork, title and author name are identical to the source. Only the number box is repainted
(the old digit is erased by interpolating the box background) and the new number is drawn in
Cormorant Garamond with lining figures, sized to match the original "1". The old digit is
removed with OpenCV inpainting (only the digit pixels are touched).

    cd covers/original
    python3 make_volumes.py 1 2 3 4          # 815x1221   (needs Pillow, numpy, opencv-python-headless)
    python3 make_volumes.py --hd 1 2 3 4     # 3260x4884  HD versions (*-hd.png)

### HD (4x AI upscale)

`upscale.py` upscales the source 4x with Real-ESRGAN (`RealESRGAN_x4plus`) on CPU (~4 min) and
writes `asrin-getirdigi-tereddutler-1-source-4x.png`, which `--hd` uses. The upscale sharpens the
lettering a lot; painted areas (lava, clouds) get a slightly smoother, painterly look.

    pip install torch torchvision spandrel
    curl -LO https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
    python3 upscale.py RealESRGAN_x4plus.pth

Volume 1 output is the untouched original (just cropped out of the app frame).
For higher quality, replace `asrin-getirdigi-tereddutler-1-source.webp` with a larger scan and
update the measured coordinates at the top of the script.

## Khmer edition (`original/make_khmer.py`)

Title: **ការងឿងឆ្ងល់នៃយុគសម័យ**, set in two lines (ការងឿងឆ្ងល់ / នៃយុគសម័យ) on the original artwork.

1. `erase_title.py big-lama.pt` removes the Turkish title with LaMa AI inpainting
   (weights: https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt).
2. `upscale.py RealESRGAN_x4plus.pth asrin-getirdigi-tereddutler-notitle-source.png asrin-getirdigi-tereddutler-notitle-source-4x.png` for HD.
3. `python3 make_khmer.py [--hd] [--font Moul] 1 2 3 4` writes `khmer-N.png` / `khmer-N-hd.png`.

The title uses the same cream-to-gold fill, dark outline and drop shadow as the original. Default
font is **Moul** (the traditional Khmer title face); other bundled options: Angkor, Koulen, Bokor,
Hanuman, Battambang, Siemreap, Dangrek, Freehand. Text shaping uses Pillow with libraqm.

## Amazon KDP print covers (`kdp/`)

`kdp/kdp_cover.py` implements the KDP paperback cover calculator (spine width per paper type,
0.125 in bleed, spine-text rule, safe zone, barcode box) and builds a full-wrap, upload-ready PDF
(back + spine + front, 300 DPI, lossless, page size = full cover size). See
`.claude/skills/kdp-cover/SKILL.md` for the rules and commands.

    cd covers/kdp
    python3 kdp_cover.py build --trim 6x9 --pages 320 --paper cream --edition khmer --volume 1 -o khmer-1-kdp

## Çağ ve Nesil (`cag-ve-nesil/`)

- `erase_title.py` removes the calligraphy title and the small series logo (LaMa).
- `make_khmer.py [--hd] [--font Freehand] 1 2 ...` sets **សម័យកាល និងជំនាន់** (proposed title: the translation
  uses សម័យកាល for "Çağ" and ជំនាន់ for "Nesil") in the original's diagonal calligraphic layout, in Freehand.
- KDP (A5, 168 pages): `python3 kdp_cover.py build --trim 5.833x8.263 --pages 168 --paper cream --theme cag
  --front <square-corner HD front> --back <mirrored no-title art> --spine-title "សម័យកាល និងជំនាន់"
  --spine-font Freehand.ttf --volume 1 -o cag-khmer-1-kdp-a5-168p-cream`

## Author name removed (Khmer editions)

`erase_author.py` rebuilds the signature area of both bottom bands as a smooth Coons-patch
gradient (plus a vertical de-streak of the Çağ ve Nesil HD band), writing `*-noauthor.png`
artwork. Both `make_khmer.py` builders and `kdp/kdp_cover.py` use that artwork, so the Khmer
covers, KDP covers and `kdp/combine.py` reading PDFs carry no author name (PDF author field is empty).

## Buhranlar anaforunda İnsan — Çağ ve Nesil 2 (`buhranlar/`)

- `erase_title.py` removes the light script title (with its shadow) and the series logo (LaMa);
  `../original/upscale.py` makes the 4x art; `../erase_author.py` removes the signature.
- `make_khmer.py [--hd] 2` sets the proposed title **មនុស្ស / ក្នុងទឹកគួច / នៃវិបត្តិ**
  ("Man in the whirlpool of crises"; វិបត្តិ = crisis as used in the series' Khmer translation) in Freehand,
  cream with a soft shadow, three lines like the original. No author name.

## Yitirilmiş cennete doğru — Çağ ve Nesil 3 (`yitirilmis/`)

Same pipeline (erase_title.py → upscale → ../erase_author.py → make_khmer.py [--hd] 3). Proposed title
**ឆ្ពោះទៅកាន់ / ឋានសួគ៌ / ដែលបាត់បង់** ("Toward the Lost Paradise"; ឋានសួគ៌ and បាត់បង់ are the words the
series' Khmer translation uses), dark teal Freehand script with a soft shadow like the original. No author name.

## Kalbin Zümrüt Tepeleri 1 (`kalbin/`)

- `erase_title.py`: black script title removed with LaMa (mask = near-black letters + hairlines darker
  than the soft-blur background). Author removed by `../erase_author.py`.
- `make_khmer.py [--hd] 1`: **ភ្នំមរកត / នៃដួងចិត្ត** — the title the Khmer translation itself uses
  («ភ្នំមរកតនៃដួងចិត្ត»), black Freehand script, stepped two lines like the original.
- KDP: A5, 368 pages → spine 0.92 in (cream) / 0.8287 in (white), `--theme kalbin` (green band/spine).
- Volumes 2 (443 pages) and 3 (387 pages): same cover, number 2/3 (`make_khmer.py [--hd] 2 3`); KDP covers
  `kalbin-khmer-{2,3}-kdp-a5-*`. The Kalbin 1–3 and Çağ ve Nesil interiors were fixed for print with
  `kdp/fix_gutter.py` (0.1 in outward shift for the 0.625 in gutter rule; full-page cream fill removed).

## Üstad'la Hasbihal (`ustadla/`)

- Source: `ustadla-source-hq.webp` (1176×1810; replaced an earlier tiny JPEG). `erase_title.py` removes the
  title (letter mask), the author name (Mahmut Açıl) and the publisher logo (box masks) with LaMa, then shifts
  the fill to the local colour of the surrounding texture (two-scale normalised Gaussian means) so no ghost remains.
- HD: `../original/upscale.py RealESRGAN_x2plus.pth ustadla-notitle-source.png ustadla-notitle-source-2x.png`
  (upscale.py now reads the model's scale, so x2 and x4 models both work).
- `make_khmer.py [--hd]`: **ការសន្ទនា / ជាមួយឧស្ដាស** ("Conversation with the Üstad"; ការសន្ទនា as in the
  translation, ឧស្ដាស as in the user's other Khmer texts), Battambang, dark red-brown like the original.
- KDP: A5, 283 pages, `--theme ustadla` (no band, brown spine). Interior: parts 1–5 merged,
  cream page fill removed with `kdp/fix_gutter.py` (gutter 0.59 in already meets 0.5 in).

## Prizma 1–4 (`prizma/`)

- `erase_title.py`: light "PRİZMA" title (+ its dark drop shadow, + the İ dot) and the prism series logo removed
  with LaMa; LaMa's context is limited to the cover (frame/band excluded) and colour matching is off
  (`COLOR_MATCH = 0`) because on these soft light streaks it made the fill darker.
- `make_khmer.py [--hd] 1 2 3 4`: **ព្រិស្មា** (the user's spelling; the translation's title page has ព្រិស្ម)
  in **Siemreap** (Khmer OS Siemreap design), light blue-white with a soft shadow, sized like the original.
  Author removed by `../erase_author.py`; the number is redrawn in each teal box.
- KDP (B5 6.929×9.842 in, `--theme prizma`: purple band, teal spine): vol 2 = 222 p, vol 3 = 244 p,
  vol 4 = 284 p. Vol 1: cover only (no interior yet). Interiors: margins fine (1.18 in inside), no page fill;
  page 1 is a dark TikZ title page that reaches the page edge.

## Kendi İklimimiz — Prizma 5 (`kendi/`)

- `erase_title.py`: dark navy title over the bright world map + series logo removed with LaMa (mask =
  pixels much darker than the local maximum); LaMa rebuilds the map and light squares.
- `make_khmer.py [--hd] 5`: proposed **បរិយាកាស / ផ្ទាល់ខ្លួនរបស់យើង** ("Our Own Atmosphere"; បរិយាកាស is the
  translation's word), Siemreap like the other Prizma volumes, dark navy with a white glow (`GLOW = True`).
- KDP: B5, 219 pages, `--theme prizma`. Interior has no title page (starts with the contents); margins fine.

## Yol Mülâhazaları — Prizma 6 (`yol/`)

- `erase_title.py`: dark title over the sun + series logo removed with LaMa (it rebuilds the sunburst).
- `make_khmer.py [--hd] 6`: **ការត្រិះរិះ / លើផ្លូវ** — the Khmer title on the translation's own first page;
  Siemreap, dark navy with a white glow. KDP: B5, 190 pages, `--theme prizma6` (cyan band, navy spine).
- Interior page 1 is a full-page cover image (reaches the page edge; shows the author name).

## Zihin Harmanı — Prizma 7 (`zihin/`)

- `erase_title.py`: light title (with the İ dots) + series logo removed with LaMa; `COLOR_MATCH = 1` here
  because the fill came out slightly darker than the page-text background.
- `make_khmer.py [--hd] 7`: **ការប្រមូលផល / នៃគំនិត** — the Khmer title on the translation's own first page;
  Siemreap, light blue-white with a soft shadow. KDP: B5, 188 pages, `--theme prizma`.
- Interior page 1 is a full-page picture cover (reaches the page edge; shows the author name).

## Çizgimizi Hecelerken — Prizma 8 (`cizgimizi/`)

- `erase_title.py`: dark title (incl. the swash Ç) + series logo removed with LaMa; the lower half of the
  crystal prism behind the letters is rebuilt as light (it fades into the burst).
- `make_khmer.py [--hd] 8`: **ខណៈប្រកប / ផ្លូវរបស់យើង** — the Khmer title on the translation's own first page;
  Siemreap, dark navy with a white glow. KDP: B5, 256 pages, `--theme prizma`.
- Interior page 1 is a full-page picture cover (reaches the page edge; shows the author name in Khmer).

## Kendi Ruhumuzu Ararken — Prizma 9 (`ruhumuzu/`)

- `erase_title.py`: white title + series logo removed with LaMa (wider mask + colour match against dark specks).
- `make_khmer.py [--hd] 9`: **ស្វែងរក / ព្រលឹងរបស់ / ខ្លួនយើង** — the Khmer title on the translation's own
  first page; Siemreap, white with a soft shadow. Also removes the faint "Copyrighted material" watermark
  under the number (`WATERMARK` strip). Cover crop sits inside the screenshot's thin light border.
- KDP: B5, 236 pages, `--theme prizma`. `kdp_cover.fix_frame_corners` now also repairs a thin light rim.

## Fasıldan Fasıla 1 (`fasil/`)

- `erase_title.py`: ornate title, volume number, author signature and the "7. BASKI" corner ribbon removed
  with LaMa (solid box/polygon masks; plain yellow background).
- `make_khmer.py [--hd] [--font Moul] 1 2 ...`: proposed **ពីជំពូកមួយ ទៅជំពូកមួយ** ("From Chapter to Chapter"),
  Moul, red-brown gradient with a dark outline like the original; number drawn under the title. No author.
- No interior yet, so no KDP cover. When it comes: this cover has no band — add a theme with `band_y: None`.

## Ölçü veya Yoldaki Işıklar (`olcu/`)

- `erase_title.py`: red title (solid per-line blocks over the smooth gradient) + author signature removed (LaMa).
- `make_khmer.py [--hd]`: proposed **រង្វាស់ / ឬ / ពន្លឺ / លើផ្លូវ** ("The Measure, or Lights on the Way"),
  Battambang, orange-red with a soft shadow, same layout as the original. The right box stays empty (no number).
- No interior yet, so no KDP cover.

## Namaz — İbadet Hayatımız (`namaz/`)

- `erase_title.py`: series label, subtitle, "NAMAZ", author name and Süreyya logo removed (LaMa, solid boxes);
  the thin gold lines and the dot separator are kept.
- `make_khmer.py [--hd]`: series **ជីវិតនៃការគោរពប្រណិប័តន៍របស់យើង** (Hanuman, gold), subtitle
  **ការគោរពប្រណិប័តន៍ដ៏ជ្រាលជ្រៅដូចមៀរ៉ាជ** (Freehand, dark brown), title **សឡាត** (Battambang, white + shadow).
  Terms as the user's translations write them (សឡាត, មៀរ៉ាជ, ការគោរពប្រណិប័តន៍). No interior yet.

## Kırık Testi 1 (`kirik/`)

- `erase_title.py`: title, author and number-box contents removed with LaMa.
- `make_khmer.py [--hd] 1 2 ...`: **ក្អម / បែក** — the title the Khmer translation uses; Siemreap, dark red over
  dark brown like the original; number box redrawn with the digit and small ក្អម / បែក labels.
- KDP: B5, 286 pages (4 weekly parts merged), `--theme kirik`. Interior page 1 is a dark title page.
