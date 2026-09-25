"""Amazon KDP paperback cover calculator + print-ready full-wrap cover builder.

Implements the rules behind https://kdp.amazon.com/cover-calculator (paperback):

  spine        = page_count x paper thickness
                   white (B&W)        0.002252 in/page
                   cream (B&W)        0.0025   in/page
                   standard color     0.002252 in/page
                   premium color      0.002347 in/page
  bleed        = 0.125 in on the top, bottom and both outer edges
  full width   = bleed + back trim width + spine + front trim width + bleed
  full height  = bleed + trim height + bleed
  spine text   = only allowed with more than 79 pages; keep 0.0625 in clear each side of it
  safe zone    = keep text >= 0.125 in inside the trim (0.25 in recommended)
  barcode      = 2 x 1.2 in box, lower right of the back cover, 0.25 in from trim and spine
  output       = single PDF, 300 DPI, all panels in one flattened image

Usage
  python3 kdp_cover.py calc   --trim 6x9 --pages 320 --paper cream
  python3 kdp_cover.py template --trim 6x9 --pages 320 --paper cream -o template.png
  python3 kdp_cover.py build  --trim 6x9 --pages 320 --paper cream --edition khmer --volume 1 -o khmer-1-kdp
  python3 kdp_cover.py build  ... --front my_front.png --back my_back.png --spine-title "..." --blurb blurb.txt
"""
import argparse
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
ORIGINAL = HERE.parent / "original"
FONTS = HERE.parent / "fonts"

PAPER = {
    "white": 0.002252,
    "cream": 0.0025,
    "color-standard": 0.002252,
    "color-premium": 0.002347,
}
BLEED = 0.125
SPINE_TEXT_MIN_PAGES = 80
SPINE_TEXT_MARGIN = 0.0625
SAFE = 0.125
SAFE_RECOMMENDED = 0.25
BARCODE_W, BARCODE_H, BARCODE_INSET = 2.0, 1.2, 0.25
MIN_PAGES = 24
DPI = 300

# Per-series colours for the back-cover band and the spine (sampled from the original covers).
THEMES = {
    "asrin": {  # Asrın Getirdiği Tereddütler: orange band, dark-red spine / number box
        "band_y": (1060 - 11) / (1232 - 11),
        "band": [(0, (131, 54, 15)), (0.3, (187, 101, 38)), (0.7, (207, 122, 53)), (1, (142, 59, 18))],
        "band_line": (42, 14, 5),
        "spine": [(0, (74, 13, 8)), (0.5, (125, 29, 18)), (1, (74, 13, 8))],
        "spine_text": (247, 232, 204),
    },
    "cag": {  # Çağ ve Nesil: teal band, navy spine / number box
        "band_y": (1360 - 18) / (1588 - 18),
        "band": [(0, (0, 150, 130)), (0.5, (3, 180, 159)), (1, (0, 120, 105))],
        "band_line": (0, 95, 88),
        "spine": [(0, (14, 40, 66)), (0.5, (30, 68, 105)), (1, (14, 40, 66))],
        "spine_text": (233, 245, 250),
    },
    "kalbin": {  # Kalbin Zümrüt Tepeleri: green band, deep green spine, cream text
        "band_y": (829 - 22) / (954 - 22),
        "band": [(0, (86, 140, 86)), (0.5, (99, 152, 93)), (1, (80, 132, 84))],
        "band_line": (125, 174, 114),
        "spine": [(0, (52, 92, 54)), (0.5, (78, 128, 78)), (1, (52, 92, 54))],
        "spine_text": (244, 228, 179),
    },
    "ustadla": {  # Üstad'la Hasbihal: no band, orange textured art all over, brown spine
        "band_y": None,
        "spine": [(0, (150, 70, 30)), (0.5, (196, 104, 52)), (1, (150, 70, 30))],
        "spine_text": (255, 238, 214),
    },
}


@dataclass
class Spec:
    trim_w: float
    trim_h: float
    pages: int
    paper: str
    spine: float
    full_w: float
    full_h: float
    spine_x0: float          # left edge of spine, measured from the left edge of the full cover
    spine_x1: float
    spine_text_allowed: bool
    dpi: int = DPI

    def px(self, inches):
        return int(round(inches * self.dpi))

    @property
    def size_px(self):
        return self.px(self.full_w), self.px(self.full_h)

    def barcode_box(self):
        """(x0, y0, x1, y1) in inches from the top-left of the full cover."""
        x1 = BLEED + self.trim_w - BARCODE_INSET
        y1 = BLEED + self.trim_h - BARCODE_INSET
        return x1 - BARCODE_W, y1 - BARCODE_H, x1, y1


def calc(trim_w, trim_h, pages, paper):
    if paper not in PAPER:
        raise ValueError(f"paper must be one of {', '.join(PAPER)}")
    if pages < MIN_PAGES:
        raise ValueError(f"KDP paperbacks need at least {MIN_PAGES} pages")
    spine = pages * PAPER[paper]
    full_w = BLEED + trim_w + spine + trim_w + BLEED
    full_h = BLEED + trim_h + BLEED
    x0 = BLEED + trim_w
    return Spec(trim_w, trim_h, pages, paper, spine, full_w, full_h, x0, x0 + spine,
                pages >= SPINE_TEXT_MIN_PAGES)


def parse_trim(s):
    w, h = s.lower().replace("in", "").split("x")
    return float(w), float(h)


def report(spec):
    mm = lambda v: v * 25.4
    w, h = spec.size_px
    lines = [
        f"Trim size          {spec.trim_w:.3f} x {spec.trim_h:.3f} in",
        f"Pages / paper      {spec.pages} / {spec.paper} ({PAPER[spec.paper]} in per page)",
        f"Spine width        {spec.spine:.4f} in  ({mm(spec.spine):.2f} mm)",
        f"Full cover         {spec.full_w:.4f} x {spec.full_h:.4f} in  "
        f"({mm(spec.full_w):.2f} x {mm(spec.full_h):.2f} mm)",
        f"At {spec.dpi} DPI          {w} x {h} px",
        f"Bleed              {BLEED} in on every outer edge",
        f"Spine text         {'allowed' if spec.spine_text_allowed else 'NOT allowed (79 pages or fewer)'}"
        f", keep {SPINE_TEXT_MARGIN} in clear each side",
        f"Safe zone          text >= {SAFE} in inside trim ({SAFE_RECOMMENDED} in recommended)",
        "Barcode box        {:.3f},{:.3f} -> {:.3f},{:.3f} in (2 x 1.2 in, back lower right)".format(*spec.barcode_box()),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- drawing helpers

def cover_fit(img, w, h, anchor_x=0.5, anchor_y=0.5):
    """Scale img to fill w x h, cropping the overflow (anchor 0 = keep left/top, 1 = keep right/bottom)."""
    s = max(w / img.width, h / img.height)
    img = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x = int((img.width - w) * anchor_x)
    y = int((img.height - h) * anchor_y)
    return img.crop((x, y, x + w, y + h))


def fix_frame_corners(img):
    """The source screenshot has rounded corners with the app's navy frame behind them: inpaint those pixels."""
    arr = np.asarray(img.convert("RGB")).copy()
    h, w = arr.shape[:2]
    r, g, b = [arr[..., i].astype(int) for i in range(3)]
    navy = (b > r + 12) & (r < 45)
    corner = np.zeros((h, w), bool)
    c = int(0.03 * w)
    for ys in (slice(0, c), slice(h - c, h)):
        for xs in (slice(0, c), slice(w - c, w)):
            corner[ys, xs] = True
    mask = ((navy & corner) * 255).astype(np.uint8)
    if mask.any():
        mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
        arr = cv2.inpaint(arr, mask, 5, cv2.INPAINT_TELEA)
    return Image.fromarray(arr)


def load_font(name, size):
    return ImageFont.truetype(str(FONTS / name), size, layout_engine=ImageFont.Layout.RAQM)


def fit_text(font_name, text, max_w, max_h, lang=None, features=None):
    size = 6
    while True:
        f = load_font(font_name, size + 1)
        l, t, r, b = f.getbbox(text, language=lang, features=features)
        if r - l > max_w or b - t > max_h:
            return load_font(font_name, size)
        size += 1


def text_image(text, font, fill, lang=None, shadow=True, features=None):
    l, t, r, b = font.getbbox(text, language=lang, features=features)
    pad = max(4, font.size // 10)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        d.text((-l + pad + pad // 3, -t + pad + pad // 3), text, font=font, fill=(0, 0, 0, 160), language=lang,
               features=features)
    d.text((-l + pad, -t + pad), text, font=font, fill=fill, language=lang, features=features)
    return im


def gradient(w, h, stops, horizontal=True):
    n = w if horizontal else h
    xs = np.linspace(0, 1, n)
    pos = np.array([p for p, _ in stops])
    cols = np.array([c for _, c in stops], float)
    line = np.stack([np.interp(xs, pos, cols[:, i]) for i in range(3)], axis=1).astype(np.uint8)
    arr = np.broadcast_to(line[None, :, :], (h, w, 3)) if horizontal else np.broadcast_to(line[:, None, :], (h, w, 3))
    return Image.fromarray(arr.copy())


def wrap(text, font, max_w, lang=None):
    """Greedy wrap on spaces; Khmer (no spaces) can use U+200B zero-width spaces as break points."""
    out = []
    for para in text.split("\n"):
        tokens = para.replace("​", " ​").split(" ")
        line = ""
        for tok in tokens:
            joiner = "" if tok.startswith("​") or not line else " "
            trial = line + joiner + tok.replace("​", "")
            if line and font.getlength(trial, language=lang) > max_w:
                out.append(line)
                line = tok.replace("​", "")
            else:
                line = trial
        out.append(line)
    return out


# ---------------------------------------------------------------- template + build

def template(spec, out):
    W, H = spec.size_px
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im, "RGBA")
    p = spec.px
    red, blue, green, amber = (220, 40, 40, 90), (40, 90, 220, 255), (30, 160, 70, 255), (255, 200, 0, 140)
    for box in [(0, 0, W, p(BLEED)), (0, H - p(BLEED), W, H), (0, 0, p(BLEED), H), (W - p(BLEED), 0, W, H)]:
        d.rectangle(box, fill=red)
    d.rectangle((p(spec.spine_x0), 0, p(spec.spine_x1), H), fill=(120, 120, 120, 60))
    for x0 in (BLEED, spec.spine_x1):
        d.rectangle((p(x0 + SAFE), p(BLEED + SAFE), p(x0 + spec.trim_w - SAFE), p(BLEED + spec.trim_h - SAFE)),
                    outline=green, width=3)
    d.rectangle(tuple(p(v) for v in spec.barcode_box()), fill=amber, outline=(160, 110, 0, 255), width=3)
    for x in (spec.spine_x0, spec.spine_x1):
        d.line((p(x), 0, p(x), H), fill=blue, width=3)
    font = ImageFont.truetype(str(FONTS / "Cinzel-Medium.ttf"), p(0.2))
    small = ImageFont.truetype(str(FONTS / "Cinzel-Medium.ttf"), p(0.12))
    d.text((p(BLEED + spec.trim_w / 2), p(1)), "BACK", font=font, fill=(0, 0, 0), anchor="mm")
    d.text((p(spec.spine_x1 + spec.trim_w / 2), p(1)), "FRONT", font=font, fill=(0, 0, 0), anchor="mm")
    bx0, by0, bx1, by1 = spec.barcode_box()
    d.text((p((bx0 + bx1) / 2), p((by0 + by1) / 2)), "BARCODE", font=small, fill=(0, 0, 0), anchor="mm")
    d.text((p(BLEED + 0.3), p(spec.full_h / 2)),
           "red = bleed (trimmed)   green = safe zone   blue = spine   amber = barcode",
           font=small, fill=(0, 0, 0))
    d.text((p(BLEED + 0.3), p(spec.full_h / 2) + p(0.25)),
           f"{spec.full_w:.3f} x {spec.full_h:.3f} in  |  spine {spec.spine:.4f} in  |  {spec.pages} pages {spec.paper}",
           font=small, fill=(0, 0, 0))
    im.save(out, dpi=(spec.dpi, spec.dpi))


def default_front(edition, volume):
    sys.path.insert(0, str(ORIGINAL))
    if edition == "khmer":
        import make_khmer
        return make_khmer.build(volume, hd=True, round_corners=False)
    import make_volumes
    return make_volumes.build(volume, hd=True, round_corners=False)


def default_back():
    sys.path.insert(0, str(ORIGINAL))
    import make_volumes as mv
    art = Image.open(ORIGINAL / "asrin-getirdigi-tereddutler-notitle-source-4x-noauthor.png").convert("RGB")
    return art.crop(mv.scaled(mv.COVER, 4)).transpose(Image.FLIP_LEFT_RIGHT)


def build(spec, front, back, spine_title, spine_author, volume, blurb, lang, title_font, body_font,
          barcode_box=True, theme="asrin"):
    th = THEMES[theme]
    W, H = spec.size_px
    p = spec.px
    canvas = Image.new("RGB", (W, H), (20, 8, 4))

    # front: trim + right bleed, full height incl. top/bottom bleed
    fx0 = p(spec.spine_x1)
    front = fix_frame_corners(front)
    canvas.paste(cover_fit(front, W - fx0, H, anchor_x=1.0, anchor_y=0.8), (fx0, 0))

    # back: mirrored artwork, darkened for readable text, plus the same orange band as the front
    bw = p(spec.spine_x0)
    back_img = cover_fit(fix_frame_corners(back), bw, H, anchor_x=0.0, anchor_y=0.8)
    shade = gradient(bw, H, [(0, (0, 0, 0)), (1, (0, 0, 0))])
    mask = gradient(bw, H, [(0, (150,) * 3), (0.55, (120,) * 3), (1, (60,) * 3)], horizontal=False).convert("L")
    back_img.paste(shade, (0, 0), mask)
    if th.get("band_y"):                                # same relative height as the front band
        band_y = int(H * th["band_y"])
        back_img.paste(gradient(bw, H - band_y, th["band"]), (0, band_y))
        ImageDraw.Draw(back_img).rectangle((0, band_y, bw, band_y + p(0.03)), fill=th["band_line"])
    canvas.paste(back_img, (0, 0))

    # blurb inside the back safe zone
    if blurb:
        margin = SAFE_RECOMMENDED + 0.25
        bx0, by0 = p(BLEED + margin), p(BLEED + margin + 0.3)
        max_w = p(spec.trim_w - 2 * margin)
        font = load_font(body_font, p(0.16))
        y = by0
        d = ImageDraw.Draw(canvas)
        for line in wrap(blurb, font, max_w, lang):
            d.text((bx0, y), line, font=font, fill=(250, 238, 214), language=lang)
            y += int(font.size * 1.75)

    # spine
    sx0, sx1 = p(spec.spine_x0), p(spec.spine_x1)
    if sx1 > sx0:
        canvas.paste(gradient(sx1 - sx0, H, th["spine"]), (sx0, 0))
        if spec.spine_text_allowed and spine_title:
            avail = spec.spine - 2 * SPINE_TEXT_MARGIN
            top, bottom = p(BLEED + SAFE_RECOMMENDED), p(BLEED + spec.trim_h - SAFE_RECOMMENDED)
            num_h = 0
            if volume:
                nf = fit_text("CormorantGaramond-Medium.ttf", volume, p(avail * 0.9), p(avail * 1.3),
                              features=["lnum"])
                num = text_image(volume, nf, th["spine_text"], features=["lnum"])
                num_h = num.height
                canvas.paste(num, ((sx0 + sx1 - num.width) // 2, bottom - num.height), num)
            text = spine_title + (f"   {spine_author}" if spine_author else "")
            length = bottom - top - num_h - p(0.2)
            tf = fit_text(title_font, text, length, p(avail * 0.8), lang)
            ti = text_image(text, tf, th["spine_text"], lang).rotate(-90, expand=True)   # reads top to bottom
            canvas.paste(ti, ((sx0 + sx1 - ti.width) // 2, top + max(0, (length - ti.height) // 2)), ti)

    if barcode_box:
        ImageDraw.Draw(canvas).rectangle(tuple(p(v) for v in spec.barcode_box()), fill=(255, 255, 255))
    return canvas


def save_pdf(png, pdf, spec):
    """Lossless PDF whose page size is exactly the full cover size (what KDP checks)."""
    import img2pdf
    layout = img2pdf.get_layout_fun((img2pdf.in_to_pt(spec.full_w), img2pdf.in_to_pt(spec.full_h)))
    with open(pdf, "wb") as f:
        f.write(img2pdf.convert(png, layout_fun=layout))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["calc", "template", "build"])
    ap.add_argument("--trim", default="6x9", help="trim size in inches, e.g. 6x9, 5.5x8.5")
    ap.add_argument("--pages", type=int, required=True)
    ap.add_argument("--paper", default="cream", choices=list(PAPER))
    ap.add_argument("-o", "--out", default="kdp-cover")
    ap.add_argument("--edition", choices=["khmer", "turkish"], default="khmer")
    ap.add_argument("--volume", default="1")
    ap.add_argument("--front", help="front cover image (overrides --edition)")
    ap.add_argument("--back", help="back cover background image")
    ap.add_argument("--spine-title")
    ap.add_argument("--spine-author", default="")
    ap.add_argument("--blurb", help="text file with back-cover text")
    ap.add_argument("--no-barcode-box", action="store_true", help="you print your own barcode")
    ap.add_argument("--theme", choices=list(THEMES), default="asrin", help="band/spine colours")
    ap.add_argument("--spine-font", help="font file in covers/fonts for the spine title")
    a = ap.parse_args()

    spec = calc(*parse_trim(a.trim), a.pages, a.paper)
    print(report(spec))
    if a.action == "calc":
        return
    if a.action == "template":
        out = a.out if a.out.endswith(".png") else a.out + "-template.png"
        template(spec, out)
        print("wrote", out)
        return

    khmer = a.edition == "khmer"
    front = Image.open(a.front).convert("RGB") if a.front else default_front(a.edition, a.volume)
    back = Image.open(a.back).convert("RGB") if a.back else default_back()
    title = a.spine_title or ("ការងឿងឆ្ងល់នៃយុគសម័យ" if khmer else "ASRIN GETİRDİĞİ TEREDDÜTLER")
    blurb = Path(a.blurb).read_text(encoding="utf-8").strip() if a.blurb else ""
    lang = "km" if khmer else None
    im = build(spec, front, back, title, a.spine_author, a.volume, blurb, lang,
               a.spine_font or ("Moul.ttf" if khmer else "Cinzel-Medium.ttf"),
               "Battambang.ttf" if khmer else "Cinzel-Medium.ttf",
               barcode_box=not a.no_barcode_box, theme=a.theme)
    im.save(a.out + ".png", dpi=(spec.dpi, spec.dpi))
    save_pdf(a.out + ".png", a.out + ".pdf", spec)
    print("wrote", a.out + ".png", a.out + ".pdf")


if __name__ == "__main__":
    main()
