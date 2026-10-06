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
- KDP: A5, 234 pages, `--theme fasil` (no band, red-brown spine); print interior `fasil-1-interior-kdp.pdf` (cream fill removed).

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
  Terms as the user's translations write them (សឡាត, មៀរ៉ាជ, ការគោរពប្រណិប័តន៍) — confirmed by the Namaz
  translation itself. `fix_speck.py` refills a leftover speck where the logo was (normal + 4x art).
- Interior from Drive: 5 parts merged → A5, 413 pages; `fix_gutter.py` shifted 0.088 in (inside 0.645 ≥ 0.625 in),
  cream fill removed → `interior/namaz-interior-kdp.pdf`.
- KDP: `--theme namaz` (no band, deep blue spine, white text): `kdp/namaz-khmer-kdp-a5-413p-{cream,white}`;
  reading PDF `interior/namaz-with-cover.pdf`.

## Kırık Testi 1 (`kirik/`)

- `erase_title.py`: title, author and number-box contents removed with LaMa.
- `make_khmer.py [--hd] 1 2 ...`: **ក្អម / បែក** — the title the Khmer translation uses; Siemreap, dark red over
  dark brown like the original; number box redrawn with the digit and small ក្អម / បែក labels.
- KDP: B5, 286 pages (4 weekly parts merged), `--theme kirik`. Interior page 1 is a dark title page.

## Sohbet-i Cânan — Kırık Testi 2 (`kirik2/`)

- Same pipeline as `kirik/`. Title **ការសន្ទនា / ជាមួយដួងព្រលឹង / ជាទីស្រឡាញ់** — the heading the Khmer translation
  itself uses for Sohbet-i Cânan. KDP: A5, 253 pages (3 parts merged), `--theme kirik`; print interior
  `kirik-2-interior-kdp.pdf` (cream page fill removed; gutter 0.554 in already meets 0.5 in).

## Gurbet Ufukları — Kırık Testi 3 (`kirik3/`)

- Same pipeline as `kirik/`. Proposed title **ជើងមេឃ / នៃការនិរទេស** ("Horizons of Exile"; ជើងមេឃ and ការនិរទេស are
  the translation's words). KDP: A5, 337 pages (5 weekly parts merged), `--theme kirik`; print interior
  `kirik-3-interior-kdp.pdf` (0.1 in gutter shift for the 0.625 in rule, cream page fill removed).

## Ümit Burcu — Kırık Testi 4 (`kirik4/`)

- Same pipeline as `kirik/`. Title **ប៉មនៃ / ក្ដីសង្ឃឹម** — «ប៉មនៃក្ដីសង្ឃឹម», the name the translation's foreword
  gives. KDP: A5, 560 pages (6 weekly parts merged), `--theme kirik`; print interior `kirik-4-interior-kdp.pdf`
  (0.2 in gutter shift for the 0.75 in rule at 501–700 pages, cream page fill removed).

## İkindi Yağmurları — Kırık Testi 5 (`kirik5/`)

- Same pipeline as `kirik/`. Proposed title **ភ្លៀង / ពេលអាសើរ** ("Afternoon Rains"; ពេលអាសើរ is how the foreword writes
  "ikindi"). KDP: A5, 682 pages (7 weekly parts merged), `--theme kirik`; print interior `kirik-5-interior-kdp.pdf`
  (0.2 in gutter shift for the 0.75 in rule, cream page fill removed).

## Diriliş Çağrısı — Kırık Testi 6 (`kirik6/`)

- Same pipeline as `kirik/`. Proposed title **ការអំពាវនាវ / នៃការរស់ឡើងវិញ** ("Call to Revival"; ការអំពាវនាវ and
  ការរស់ឡើងវិញ are the translators' words). No interior in Drive yet, so no KDP cover.

## Ölümsüzlük İksiri — Kırık Testi 7 (`kirik7/`)

- Same pipeline as `kirik/`. Proposed title **ទឹកអម្រឹត / នៃភាពអមតៈ** ("Elixir of Immortality"; ទឹកអម្រឹត and ភាពអមតៈ are
  the translators' words). No interior in Drive yet, so no KDP cover.

## Vuslat Muştusu — Kırık Testi 8 (`kirik8/`)

- Same pipeline as `kirik/`. Proposed title **ដំណឹងរីករាយ / នៃការជួបជុំ** ("Good News of Reunion"; the translators' words).
  No interior in Drive yet, so no KDP cover.

## Kalb İbresi — Kırık Testi 9 (`kirik9/`)

- Same pipeline as `kirik/`, but the title sits in the sky at the top. Proposed title **ម្ជុល / នៃដួងចិត្ត**
  ("The Heart's Needle"; ម្ជុល and ដួងចិត្ត are the translators' words). No interior in Drive yet.

## Cemre Beklentisi — Kırık Testi 10 (`kirik10/`)

- Same pipeline as `kirik/`. Proposed title **ការរង់ចាំ / កម្ដៅនិទាឃរដូវ** ("Waiting for the Warmth of Spring"; cemre is
  the warmth that heralds spring). Two-digit number with side labels moved outward. No interior in Drive yet.

## Yaşatma İdeali — Kırık Testi 11 (`kirik11/`)

- New parchment design (no band/box): title, ribbon text, number and author removed with LaMa (ribbon kept).
  Proposed title **ឧត្តមគតិ / នៃការធ្វើឱ្យរស់** ("The Ideal of Making Others Live"), Battambang, dark brown;
  ក្អមបែក on the ribbon, 11 below. No interior in Drive yet (a KDP theme without band will be needed).

## Yenilenme Cehdi — Kırık Testi 12 (`kirik12/`)

- Same pipeline as `kirik10/`. Proposed title **ការខិតខំ / ដើម្បីការធ្វើឱ្យថ្មី** ("The Effort for Renewal"; the translators'
  words ការខិតខំ, ការធ្វើឱ្យថ្មី). No interior in Drive yet.

## Mefkûre Yolculuğu — Kırık Testi 13 (`kirik13/`)

- Same pipeline as `kirik10/`; title sits over the crowd, the Arabic calligraphy (Muhammad) is kept. Proposed title
  **ដំណើរ / នៃឧត្តមគតិ** ("Journey of the Ideal"). Number box is dark brown on this volume. No interior in Drive yet.

## Buhranlı Günler ve Ümit Atlasımız — Kırık Testi 14 (`kirik14/`)

- Title letters, author name and number-box digits removed with LaMa, then the plain red wall and the brown number box
  are refilled with their own smooth colour plus matching grain, so no blotches are left. Proposed title
  **ថ្ងៃនៃ / វិបត្តិ / និង / ផែនទីក្ដីសង្ឃឹម / របស់យើង** ("Days of Crisis and Our Map of Hope"). No interior in Drive yet.

## Ruhumuzun Heykelini Dikerken 1 (`heykel/`)

- `erase_title.py`: white script title, small corner title, author signature and number removed with LaMa
  (light-letter masks, no boxes).
- `make_khmer.py [--hd] [--font Freehand] 1`: **នៅពេលតាំង / រូបសំណាកនៃ / ព្រលឹងរបស់យើង** — the translation's own
  heading, confirmed by the user; Freehand (closest to the original script), white with a soft dark-blue halo,
  stepped right like the original. Number in Cormorant Garamond, orange like the original. No author.
- Interior from Drive: A5, 177 pages, page 2 blank; `fix_gutter.py` removed the cream fill, margins already OK
  (inside 0.576 in) → `interior/ruhumuzun-heykeli-1-interior-kdp.pdf`.
- KDP: A5, 177 pages → spine 0.4425 in (cream) / 0.3986 in (white), `--theme heykel` (red band, deep blue spine,
  white text): `kdp/heykel-khmer-1-kdp-a5-177p-{cream,white}`. Front = square-corner HD build, back = mirrored
  no-title art. Reading PDF `interior/ruhumuzun-heykeli-1-with-cover.pdf` (179 pages).

## Battambang everywhere (all books)

- Every `make_khmer.py` now uses Battambang for all Khmer text (titles, Kırık Testi side labels, spines);
  all covers, HD covers, KDP covers and reading PDFs rebuilt (`kdp/rebuild_all.py`).
- Prizma 6–9 and Kırık Testi 1 interiors: the built-in picture cover and its blank back page removed →
  188 / 186 / 254 / 234 / 284 pages; KDP covers renamed to the new page counts (spines recalculated).

## Asâ-yı Mûsâ (`asa/`)

- `erase_title.py`: gold title removed (green-channel letter mask on the red velvet), publisher logo removed from
  the ornate border (box). The "Risale-i Nur Külliyatı'ndan" line and "Bediüzzaman Said Nursî" are kept
  (user's rule for Risale-i Nur books). `make_back.py <big-lama.pt>` erases them from the 4x art for the KDP back
  (`asa-back-4x.png`), so the mirrored back shows no backwards text. Built from `asa-source-hq.webp`, the
  user's clearer screenshot of the same series design (the Sözler cover, 962 px wide; its "Sözler" title is erased);
  `asa-source.webp` is the original small Asâ-yı Mûsâ screenshot. The same clean art can serve Sözler later.
- `make_khmer.py [--hd]`: **ដំបងរបស់ / ព្យាការីមូសា** — the translation's own words (chapter 1
  "ផ្នែកទីមួយនៃដំបងរបស់ព្យាការីមូសា"); Battambang, gold with a faint dark emboss. No number.
- Interior from Drive ("Asayi Musa.pdf"): A5, 438 pages, page 2 blank; `fix_gutter.py` shifted 0.088 in
  (inside 0.645 ≥ 0.625 in) and removed the cream fill → `interior/asa-musa-interior-kdp.pdf`.
- KDP: A5, 438 pages → spine 1.095 in (cream) / 0.986 in (white), `--theme asa` (no band, dark red spine, gold
  text): `kdp/asa-khmer-kdp-a5-438p-{cream,white}`; reading PDF `interior/asa-musa-with-cover.pdf`.

## Prizma 1 (`prizma/`, interior added)

- Interior from Drive: 3 parts (pp 1–85, 86–170, 171–255) merged → A5 (not B5 like Prizma 2–9), 255 pages, page 2
  blank, no built-in cover. `fix_gutter.py`: cream fill removed, margins already OK (inside 0.545 in) →
  `interior/prizma-1-interior-kdp.pdf`.
- KDP: A5, 255 pages → spine 0.6375 in (cream), `--theme prizma`: `kdp/prizma-khmer-1-kdp-a5-255p-{cream,white}`;
  reading PDF `interior/prizma-1-with-cover.pdf`.

## Kalbin Zümrüt Tepeleri 4 (`kalbin/`, number 4)

- Same cover, number 4 (`make_khmer.py [--hd] 4`). Interior from Drive: A5, 337 pages; `fix_gutter.py` shifted
  0.07 in (inside 0.645 ≥ 0.625 in) and removed the cream fill → `interior/kalbin-4-interior-kdp.pdf`.
- KDP: `kdp/kalbin-khmer-4-kdp-a5-337p-{cream,white}`; reading PDF `interior/kalbin-4-with-cover.pdf`.

## Gönül Nağmeleri – Hutbeler (`gonul/`)

- `erase_title.py`: "GÖNÜL NAĞMELERİ", "HUTBELER" and the author removed (LaMa on everything that differs from the
  teal sky in each box), then the plain-sky parts refilled with the sky's own smooth colour + grain (no specks).
- `make_khmer.py [--hd]`: proposed **បទភ្លេង / នៃដួងចិត្ត / ខុតហ្ពះ** ("Melodies of the Heart – Sermons"):
  ខុតហ្ពះ is how this translation writes hutbe (69×, "ខុតហ្ពះ ១"…); បទភ្លេង and ដួងចិត្ត are its words too.
  Battambang, navy + white like the original. No author.
- Interior from Drive ("Gönül Nağmeleri- Hutbeler.pdf"): A5, 401 pages; `fix_gutter.py` shifted 0.061 in
  (inside 0.645 ≥ 0.625 in), cream fill removed → `interior/gonul-interior-kdp.pdf`.
- KDP: `--theme gonul` (deep teal spine; theme `back` colour = the teal sky, because the front's edges are the
  minbars): `kdp/gonul-khmer-kdp-a5-401p-{cream,white}`; reading PDF `interior/gonul-with-cover.pdf`.

## Asrın Getirdiği Tereddütler 1 — new interior edition

- The user uploaded a new translation PDF: A5, 251 pages (old one: B5, 264 pages, kept as
  `interior/asrin-getirdigi-tereddutler-1-interior-orig.pdf`). The old bottom-margin overflow (pp 184, 189) is gone;
  margins already OK (inside 0.563 in) → `interior/asrin-getirdigi-tereddutler-1-interior-kdp.pdf` (cream fill removed).
- No Khmer title page in this edition; the cover keeps the user's own title ការងឿងឆ្ងល់នៃយុគសម័យ.
- KDP: `kdp/asrin-khmer-1-kdp-a5-251p-{cream,white}` (replaces `khmer-1-kdp-176x250-264p-*`); reading PDF rebuilt.

## Asrın Getirdiği Tereddütler 4

- Same cover, number 4 (`original/make_khmer.py [--hd] 4`). Interior from Drive: A5, 354 pages; its own title page
  reads ការងឿងឆ្ងល់នៃយុគសម័យ ភាគទី ៤ (matches the cover). `fix_gutter.py` shifted 0.07 in (inside 0.645 ≥ 0.625 in),
  cream fill removed → `interior/asrin-getirdigi-tereddutler-4-interior-kdp.pdf`.
- KDP: `kdp/asrin-khmer-4-kdp-a5-354p-{cream,white}`; reading PDF `interior/asrin-getirdigi-tereddutler-4-with-cover.pdf`.

## Beyan — Yağmur Serisi 1 (`beyan/`)

- `erase_title.py`: "Beyan" script title (+ drop shadow), author signature and "Yağmur Serisi" logo removed
  (row-median deviation masks, LaMa); the title box is then replaced by a smooth polynomial sky fit + grain
  (the letters' glow left blotches otherwise), the grey band refilled with its own colour. Green number box kept.
- `make_khmer.py [--hd]`: **វោហារ** — the translation's own title (its pages 1 and 3: "វោហារ / Beyan"; the cover
  first proposed ការពន្យល់). Battambang, pale cream with a dark drop shadow like the original. No author.
- Interior from Drive ("Beyan.pdf"): A5, 263 pages, margins OK (inside 0.59 in), cream fill removed →
  `interior/beyan-1-interior-kdp.pdf`. KDP: `--theme beyan` (grey band, deep green spine like the number box):
  `kdp/beyan-khmer-1-kdp-a5-263p-{cream,white}`; reading PDF `interior/beyan-1-with-cover.pdf`.

## Bir İ'câz Hecelemesi (`icaz/`)

- `erase_title.py`: title (incl. the İ dots and the circumflex), author and Nil logo removed — masks catch anything
  lighter or darker than the local leather texture (the cream letters carry a dark emboss); the dark cartouche panel
  is then refilled with its own smooth colour + its weave tiled from a clean strip. Cartouche ornaments kept.
- `make_khmer.py [--hd]`: proposed **ការអានប្រកប / ភាពអច្ឆរិយៈមួយ** ("Spelling Out a Miracle": ភាពអច្ឆរិយៈ is the
  translators' word for the Qur'an's i'câz, អានប្រកប the Khmer for reading syllable by syllable); Battambang, cream
  with a faint dark emboss. No author. No interior yet.

## Enginliğiyle Bizim Dünyamız – İktisadî Mülâhazalar (`dunyamiz/`)

- `erase_title.py`: the three title lines and the author signature removed (LaMa, deviation-from-texture masks;
  hairline opening for the pen signature), the smooth orange band refilled with its own colour. Oval picture,
  mosque skyline and the empty right box kept.
- `make_khmer.py [--hd]`: **ពិភពរបស់យើង / ក្នុងភាពធំទូលាយរបស់វា**, the title printed in the translation (interior pp 1, 3;
  replaces the earlier proposal). No subtitle line (the translation has none). Battambang, cream with a soft shadow. No author.
- Interior from Drive: A5, 684 pages (no picture cover). `fix_gutter.py` shifted 0.18 in (inside 0.77 ≥ 0.75 in),
  cream fill removed → `interior/dunyamiz-interior-kdp.pdf`.
- KDP: theme `dunyamiz` (orange band, deep brown spine): `kdp/dunyamiz-khmer-kdp-a5-684p-{cream,white}`;
  reading PDF `interior/dunyamiz-with-cover.pdf`.

## Asrın Getirdiği Tereddütler 3

- Same cover, number 3. Interior from Drive: A5, 307 pages; title page ការងឿងឆ្ងល់នៃយុគសម័យ ភាគទី ៣ (matches).
  `fix_gutter.py` shifted 0.055 in (inside 0.645 ≥ 0.625 in), cream fill removed.
- KDP: `kdp/asrin-khmer-3-kdp-a5-307p-{cream,white}`; reading PDF `interior/asrin-getirdigi-tereddutler-3-with-cover.pdf`.

## Fasıldan Fasıla 2 (`fasil2/`, new design)

- `erase_title.py`: title, small "FASILDAN FASILA" mark and author signature removed (LaMa, row-median deviation
  masks); the pomegranate's stem tip is protected (`KEEP`). Number box "2" kept.
- `make_khmer.py [--hd]`: **ពីវគ្គមួយ / ទៅវគ្គមួយ** — the title the translators printed (interior pp 1 and 3,
  "ពីវគ្គមួយទៅវគ្គមួយ ភាគ ២"); volume 1's cover/spine switched from the proposed ពីជំពូកមួយ ទៅជំពូកមួយ to match.
  Dark brown, regular + Battambang Bold (`fonts/Battambang-Bold.ttf`, OFL) like "Fasıldan" / "Fasıla".
- Interior from Drive: A5, 250 pages, margins OK (inside 0.59 in), cream fill removed → `interior/fasil-2-interior-kdp.pdf`.
  KDP: `--theme fasil2` (brown leather band, deep brown spine): `kdp/fasil-khmer-2-kdp-a5-250p-{cream,white}`;
  reading PDF `interior/fasil-2-with-cover.pdf`.

## Lem'alar (`lemalar/`, Risale-i Nur — 2 volumes)

- Interior from Drive in 12 parts ("Lemalar - Part 1..12"), merged: A5, 1,166 pages — over KDP's 828, so split in
  two before the 26th Flash (ពន្លឺទីម្ភៃប្រាំមួយ, printed p. 575): vol 1 = PDF pp 1–580 (580p); vol 2 = the same
  title/copyright/contents pages (PDF pp 1–6) + pp 581–1166 (592p), page parity kept.
- `fix_gutter.py` (its cream-fill pattern now also matches pages without a `gs` line before the fill): inside
  0.77 in ≥ 0.75 in → `interior/lemalar-{1,2}-interior-kdp.pdf`.
- `make_khmer.py [--hd] 1|2`: **ពន្លឺទាំងឡាយ** (the translation's title page) + **ភាគទី ១ / ២**, gold on the
  Risale-i Nur red-velvet art already erased for Asâ-yı Mûsâ (`asa/asa-notitle-source*.png`, same series design);
  "Risale-i Nur Külliyatı'ndan" and the author kept as printed.
- KDP: theme `asa`: `kdp/lemalar-khmer-1-kdp-a5-580p-*`, `kdp/lemalar-khmer-2-kdp-a5-592p-*`;
  reading PDFs `interior/lemalar-{1,2}-with-cover.pdf`.

## Kalbin Solukları (`soluk/`)

- `erase_title.py`: "KALBİN SOLUKLARI" (navy with a white glow) and the author lines removed (LaMa, deviation from
  the soft sky); dove, dotted frame and ornamented rule kept.
- `make_khmer.py [--hd] 1|2`: **ដង្ហើម / នៃដួងចិត្ត** — the title in the translation's text layer (title page and the
  chapter of the same name); navy Battambang with a soft white glow. No author. Two volumes (user: "like Lem'alar"):
  **ភាគទី ១ / ២** under the ornamented rule, where the author was.
- Interior: 74 chapters, last at printed p. 819 (~830+ pages, over KDP's 828). Planned split before chapter 42
  (printed p. 417). `Kalbin Solukları.pdf` (7.5 MB) is too big for the Drive connector — waiting for it in parts.
- KDP theme `soluk` (no band, deep navy spine) is ready.

## Fâtiha Üzerine Mülâhazalar (`fatiha/`)

- Same series design as Bizim Dünyamız (gold band + red box). `erase_title.py`: "FATİHA ÜZERİNE / Mülâhazalar" and
  the author signature on the band removed (LaMa; band refilled with its own colour). Mosque, fountain, red box kept.
- `make_khmer.py [--hd]`: **ការពិចារណាលើ / ស៊ូរ៉ោះអាល់ហ្វាទីហះ** — the translation's title page; dark brown Battambang
  with a faint light emboss. No author.
- Interior from Drive: A5, 327 pages (no picture cover). `fix_gutter.py` shifted 0.088 in (inside 0.645 ≥ 0.625 in),
  cream fill removed → `interior/fatiha-interior-kdp.pdf`.
- KDP: theme `fatiha` (gold band, deep brown spine; `back` = cream sky → gold, since the front's edge is the mosque): `kdp/fatiha-khmer-kdp-a5-327p-{cream,white}`; reading PDF
  `interior/fatiha-with-cover.pdf`.

## Hitap Çiçekleri (`hitap/`)

- `erase_title.py`: red "HİTAP ÇİÇEKLERİ" (masked by redness so the blue water splash beside the H stays), the
  "M. Fethullah Gülen" signature and the NESİL logo removed (LaMa).
- `make_khmer.py [--hd]`: **ផ្កានៃ / ការអំពាវនាវ** — the translation's title page; red Battambang (the original's
  red) with a faint light emboss, kept clear of the splash. No author, no logo.
- Interior from Drive: A5, 260 pages (no picture cover); inside margin already 0.59 ≥ 0.5 in, so `fix_gutter.py`
  only removed the cream fill → `interior/hitap-interior-kdp.pdf`.
- KDP: theme `hitap` (no band, deep blue spine): `kdp/hitap-khmer-kdp-a5-260p-{cream,white}`; reading PDF
  `interior/hitap-with-cover.pdf`.

## İbadet Hayatımız: Oruç, Zekât, Hac (`oruc/`, `zekat/`, `hac/`)

- Same series design as Namaz (Süreyya). `erase_title.py`: series label, subtitle, title, author and Süreyya logo
  removed with solid LaMa boxes between the thin rules; the series-label strip is re-interpolated row by row (LaMa
  regrew letter bits there).
- `make_khmer.py [--hd]` — **proposed** titles (no translation in Drive yet), from the translators' words found in
  the other interiors (ការបួស "បួសនៅខែរ៉ម៉ាដន", ហ្សាកាត់ "បរិច្ចាគហ្សាកាត់", ហាជ្ជ "ធ្វើហាជ្ជ", ការអភ័យទោស,
  យុត្តិធម៌សង្គម, ការអំពាវនាវ); series line ជីវិតនៃការគោរពប្រណិប័តន៍របស់យើង as on Namaz:
  - Oruç: ការគោរពប្រណិប័តន៍ដែលពោរពេញដោយការអភ័យទោស / **ការបួស**
  - Zekât: ធាតុគ្រឹះនៃយុត្តិធម៌សង្គម / **ហ្សាកាត់**
  - Hac: ការឆ្លើយតបនឹងការអំពាវនាវរបស់អល់ឡោះ / **ហាជ្ជ**
- KDP themes `oruc`, `zekat`, `hac` (no band) are ready; waiting for the interiors.

## Fasıldan Fasıla 3 (`fasil3/`)

- Interior from Drive: A5, 306 pages; title page ពីវគ្គមួយ / ទៅវគ្គមួយ — ភាគ ៣. `fix_gutter.py` shifted 0.057 in
  (inside 0.645 ≥ 0.625 in), cream fill removed → `interior/fasil-3-interior-kdp.pdf`.
- `erase_title.py`: "FASILDAN FASILA" + soft shadows (wide deviation masks) and the author signature on the gold band
  removed (LaMa; band refilled with its own colour). Figure, floral art and number box "3" kept.
- `make_khmer.py [--hd]`: **ពីវគ្គមួយ / ទៅវគ្គមួយ**, red-brown regular + dark-brown Battambang Bold with a soft shadow.
- KDP theme `fasil3` (gold band, deep brown spine): `kdp/fasil-khmer-3-kdp-a5-306p-{cream,white}`.

## Fasıldan Fasıla 4 (`fasil4/`)

- Interior from Drive: A5, 257 pages; title page ពីវគ្គមួយ / ទៅវគ្គមួយ — ភាគ ៤. Inside margin already 0.553 ≥ 0.5 in;
  cream fill removed → `interior/fasil-4-interior-kdp.pdf`.
- `erase_title.py`: "fasıldan fasıla" (masked by low green: the paper scraps are yellow/cream), the small
  "FASILDAN FASILA" mark and the author signature on the leather band removed (LaMa). Pen, paper art, box "4" kept.
- `make_khmer.py [--hd]`: **ពីវគ្គមួយ** (dark brown regular) / **ទៅវគ្គមួយ** (red-brown Battambang Bold, shifted right
  like "fasıla").
- KDP theme `fasil4` (leather band, deep brown spine): `kdp/fasil-khmer-4-kdp-a5-257p-{cream,white}`.
