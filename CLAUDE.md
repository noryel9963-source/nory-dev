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
- Prizma series: title ព្រិស្មា, font Siemreap. Kırık Testi series: ក្អមបែក, Siemreap, dark red + dark brown lines.
- Font Suwannaphum (covers/fonts/Suwannaphum-*.ttf) is also available; the user chose Suwannaphum Regular for Kırık Testi 14.

## Status
Done (cover + KDP covers + reading PDF): Asrın Getirdiği Tereddütler 1; Çağ ve Nesil 1; Kalbin Zümrüt Tepeleri 1–3;
Üstad'la Hasbihal; Prizma 2–9; Kırık Testi 1–5; Fasıldan Fasıla 1.
Cover only (waiting for interior PDF): Çağ ve Nesil 2 (Buhranlar) and 3 (Yitirilmiş); Prizma 1; Ölçü; Namaz; Kırık Testi 6–14.

## Open questions for the user
- Confirm proposed titles: Çağ ve Nesil 1–3, Kendi İklimimiz (Prizma 5), Fasıldan Fasıla, Ölçü, Namaz, Kırık Testi 3, 5, 6, 14.
- Author name still appears inside interiors (copyright/title pages) — left untouched pending the user's decision.
- Prizma 6–9 + Kırık Testi 1 interiors start with a full-page picture cover (reaches edge, shows author): remove/replace?
- Asrın Getirdiği Tereddütler 1 interior: text overflows bottom margin on pages 184 and 189.
