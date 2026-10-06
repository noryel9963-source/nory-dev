# Khmer book-cover project — handoff notes

Work lives in `covers/` (see `covers/README.md` for every book) and the KDP rules/tools in
`.claude/skills/kdp-cover/SKILL.md` + `covers/kdp/`. Branch: `claude/new-session-sms95p`.

## Setup for a new session
```bash
pip install torch torchvision spandrel pymupdf pillow opencv-python-headless img2pdf fonttools
S=/tmp/models && mkdir -p $S
curl -L -o $S/RealESRGAN_x4plus.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
curl -L -o $S/RealESRGAN_x2plus.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth
curl -L -o $S/big-lama.pt https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt
```
Interiors are NOT in git (`covers/interior/` is ignored): re-download them from Google Drive
(the user's Drive holds the Khmer PDFs, often split into "Week N"/"Part N" files — merge in order).

## Per-book pipeline
1. Save screenshot as `covers/<book>/<book>-source.webp`; measure cover bounds, title/author/number boxes.
2. `erase_title.py <big-lama.pt>` (copy the closest existing book's script) → `*-notitle-source.png`.
3. `python3 covers/original/upscale.py <RealESRGAN_x4plus.pth> in.png out-4x.png`.
4. Author removal: add the book to `covers/erase_author.py` (or a box in erase_title) — the user wants NO author name.
5. `make_khmer.py [--hd] N` (copy closest series builder) → `khmer-N.png` / `khmer-N-hd.png`.
6. Interior: `covers/kdp/fix_gutter.py IN OUT [--shift X]` (gutter rule + removes cream page fill).
7. KDP cover: `covers/kdp/kdp_cover.py build --trim WxH --pages P --paper cream|white --theme T ...` (both papers).
8. Reading PDF: `covers/kdp/combine.py INTERIOR OUT --title ...`.
9. Commit + push; send files to the user.

## Title rules the user confirmed / conventions
- Use the Khmer title printed in the translation (title page, foreword) when one exists; otherwise build it
  from the translators' own vocabulary and ask the user to confirm.
- Risale-i Nur books (Bediüzzaman Said Nursî, e.g. Asâ-yı Mûsâ, Sözler): KEEP the "Risale-i Nur Külliyatı'ndan"
  line and the author name as printed (user's rule); only the title (and publisher logo) is replaced.
  The no-author rule applies to the M. Fethullah Gülen books.
- **All Khmer text on every cover and spine is Battambang** (user's decision; numbers stay Cormorant Garamond).
  Prizma series title ព្រិស្មា; Kırık Testi series ក្អមបែក, dark red + dark brown lines.
- After any builder change, `python3 covers/kdp/rebuild_all.py [keys]` rebuilds the finished books' KDP covers
  (cream + white) and reading PDFs (page counts, themes, spine titles all listed there).
- KDP back cover = plain colour taken from the front's outer edge (soft vertical gradient) + the series band,
  no white barcode box (user: not needed; KDP prints its own barcode; `--barcode-box` re-enables it);
  no picture, logo or mirrored art (user's choice). `--back` images are no longer used. A theme `back`
  gradient overrides the edge colour when the front's edge is not its background (Gönül Nağmeleri).
- Interiors must not contain their own cover: Prizma 6–9 and Kırık Testi 1 had a picture cover + blank page —
  removed (pages 1–2; originals kept as `*-interior-orig.pdf`).

## Status
Done (cover + KDP covers + reading PDF): Asrın Getirdiği Tereddütler 1 (new A5 251p edition), 3 (A5 307p) and 4 (A5 354p); Çağ ve Nesil 1; Kalbin Zümrüt Tepeleri 1–4;
Üstad'la Hasbihal; Prizma 1–9 (1 is A5, 2–9 B5); Kırık Testi 1–5; Fasıldan Fasıla 1–2 (title ពីវគ្គមួយ ទៅវគ្គមួយ from the translation; `fasil2/`); Ruhumuzun Heykelini Dikerken 1 (`heykel/`);
Asâ-yı Mûsâ (`asa/`, Said Nursî — title ដំបងរបស់ព្យាការីមូសា from the translation); Namaz (`namaz/`, A5 413p); Gönül Nağmeleri: Hutbeler (`gonul/`, A5 401p);
Beyan 1 (`beyan/`, title វោហារ from the translation, A5 263p);
Enginliğiyle Bizim Dünyamız (`dunyamiz/`, title ពិភពរបស់យើង / ក្នុងភាពធំទូលាយរបស់វា from the translation, A5 684p).
Lem'alar (`lemalar/`, Risale-i Nur, title ពន្លឺទាំងឡាយ, 2 vols A5 580p + 592p, split before the 26th Flash);
Fâtiha Üzerine Mülâhazalar (`fatiha/`, title ការពិចារណាលើ / ស៊ូរ៉ោះអាល់ហ្វាទីហះ from the translation, A5 327p);
Hitap Çiçekleri (`hitap/`, title ផ្កានៃ / ការអំពាវនាវ from the translation, A5 260p).
Cover only: Kalbin Solukları (`soluk/`, ដង្ហើម / នៃដួងចិត្ត, 2 vols, split planned before chapter 42) — PDF (7.5 MB) too big for the Drive connector, needs parts.
Cover only (waiting for interior PDF): Çağ ve Nesil 2 (Buhranlar) and 3 (Yitirilmiş); Ölçü; Kırık Testi 6–14; Bir İ'câz Hecelemesi (`icaz/`).

## Open questions for the user
- Confirm proposed titles: Çağ ve Nesil 1–3, Kendi İklimimiz (Prizma 5), Ölçü, Kırık Testi 3, 5, 6, 14, Gönül Nağmeleri, Bir İ'câz Hecelemesi (ការអានប្រកបភាពអច្ឆរិយៈមួយ).
- Author name still appears inside interiors (copyright/title pages) — left untouched pending the user's decision.
- Prizma 9 and Kırık Testi 1 interiors: the copyright page names the wrong source book (Prizma 8 / Prizma 2).
