"""Shared builder for single books whose covers come from herkul.app (Bahar Neşîdesi, Sonsuz Nur 1–2, Derin
Müslümanlık, Çekirdekten Çınara). One BOOKS entry per book: the source is resized to SIZE, ERASE boxes go to LaMa,
ROWFILL boxes (author signature on a smooth band) are refilled row by row between their edges, and LINES are set
in Battambang. Each book folder has a 3-line make_khmer.py that calls build(KEY, ...).

    python3 common.py <big-lama.pt> <RealESRGAN_x4plus.pth> KEY ...   # erase + 4x upscale
    python3 ../<folder>/make_khmer.py [--hd]
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

COVERS = Path(__file__).parent.parent
FONTS = COVERS / "fonts"
WHITE, NAVY, RED = (255, 250, 238), (24, 52, 110), (190, 28, 50)

# folder: size, erase boxes, row-fill boxes, lines (text, max w, ink h, cx, cy, colour, shadow, bold)
BOOKS = {
    "bahar": dict(size=(330, 499), crop=(4, 4, 326, 495),
                  erase=[(14, 276, 172, 346), (150, 280, 182, 314), (150, 312, 170, 346), (12, 342, 296, 420), (136, 408, 298, 438), (126, 432, 196, 494)],
                  rowfill=[], lines=[("ចម្រៀងនៃ", 140, 48, 88, 314, RED, (255, 255, 255), True),
                                     ("និទាឃរដូវ", 270, 62, 155, 384, RED, (255, 255, 255), True)]),
    "sonsuz1": dict(size=(400, 600), crop=(0, 0, 400, 600),
                    erase=[(108, 232, 296, 428)], rowfill=[(55, 532, 322, 582)],
                    lines=[("ការវិភាគអំពីជីវិតរបស់ព្យាការីមូហាំម៉ាត់", 250, 22, 220, 262, (225, 230, 255), (5, 10, 40), False),
                           ("ពន្លឺនិរន្ត", 270, 80, 220, 365, (238, 222, 170), (5, 10, 40), True)]),
    "derin": dict(size=(400, 640), crop=(0, 0, 400, 640),
                  erase=[(40, 125, 262, 230), (45, 395, 252, 445), (110, 548, 310, 580)], rowfill=[],
                  lines=[("សីលធម៌ជ្រៅជ្រះ", 230, 52, 145, 160, (236, 240, 245), (4, 30, 36), True),
                         ("នៃឥស្លាម", 200, 46, 120, 212, (236, 240, 245), (4, 30, 36), True),
                         ("សីលធម៌ក្រោមពន្លឺ", 200, 24, 130, 410, (236, 240, 245), (4, 30, 36), False),
                         ("គម្ពីរគួរអាន និងស៊ុណ្ណះ", 200, 24, 130, 436, (236, 240, 245), (4, 30, 36), False)]),
    "cekirdek": dict(size=(400, 600), crop=(0, 0, 400, 600),
                     erase=[(62, 312, 352, 500), (50, 282, 222, 318)], rowfill=[(55, 535, 300, 585)],
                     lines=[("ពីគ្រាប់ធញ្ញជាតិ", 280, 60, 205, 365, NAVY, (255, 255, 255), True),
                            ("ទៅដើមឈើ", 240, 64, 215, 430, NAVY, (255, 255, 255), True),
                            ("(ការបណ្ដុះស្មារតីផ្លូវចិត្តចំពោះកូនៗ)", 260, 22, 225, 485, NAVY, None, False)]),
}
BOOKS["irsad"] = dict(size=(400, 600), crop=(0, 0, 400, 600),
                      erase=[(70, 70, 330, 250)], rowfill=[(55, 535, 275, 588)],
                      lines=[("មាគ៌ានៃការផ្ដល់", 250, 56, 200, 125, WHITE, (20, 40, 110), True),
                             ("មគ្គុទេសក៍", 220, 56, 200, 190, WHITE, (20, 40, 110), True),
                             ("(ការទាក់វះ)", 150, 24, 200, 238, WHITE, (20, 40, 110), False)])
BOOKS["mizrap"] = dict(size=(400, 600), crop=(0, 0, 400, 600),
                       erase=[(90, 115, 330, 275), (95, 495, 330, 570)], rowfill=[],
                       lines=[("ក្រចកដេញ", 220, 60, 200, 168, (222, 178, 92), (40, 18, 6), True),
                              ("ដែលបាក់", 200, 56, 200, 228, (222, 178, 92), (40, 18, 6), True),
                              ("កំណាព្យ", 110, 30, 200, 282, (222, 178, 92), (40, 18, 6), False)])
BOOKS["kader"] = dict(size=(400, 600), crop=(0, 0, 400, 600),
                      erase=[(60, 200, 340, 232), (55, 226, 345, 312)], rowfill=[(55, 535, 275, 588)],
                      lines=[("តាមទស្សនៈនៃគម្ពីរ និងស៊ុនណះ", 270, 20, 200, 216, (45, 25, 20), None, False),
                             ("កទ្រ៍", 230, 92, 200, 268, (150, 28, 30), (255, 235, 210), True)])
BOOKS["altin"] = dict(size=(450, 600), crop=(0, 0, 450, 600),
                      erase=[(55, 70, 395, 215)], rowfill=[(60, 552, 305, 592)],
                      lines=[("ក្នុងបរិយាកាសមាស", 320, 62, 225, 118, (60, 35, 20), None, True),
                             ("នៃគម្ពីរគួរអាន", 280, 50, 225, 185, (60, 35, 20), None, False)])
BOOKS["sonsuz2"] = dict(BOOKS["sonsuz1"])


def src(key, hd=False):
    return COVERS / key / f"{key}-notitle-source{'-4x' if hd else ''}.png"


def erase(key, lama_path):
    import cv2
    import torch
    b = BOOKS[key]
    im = Image.open(COVERS / key / f"{key}-source.jpg").convert("RGB").resize(b["size"], Image.LANCZOS)
    im = np.asarray(im.crop(b["crop"])).copy()
    ox, oy = b["crop"][:2]
    mask = np.zeros(im.shape[:2], np.uint8)
    for x0, y0, x1, y1 in b["erase"]:
        mask[y0 - oy:y1 - oy, x0 - ox:x1 - ox] = 255
    h, w = im.shape[:2]
    ph, pw = (8 - h % 8) % 8, (8 - w % 8) % 8
    img = np.pad(im, ((0, ph), (0, pw), (0, 0)), mode="reflect")
    m = np.pad(mask, ((0, ph), (0, pw)))
    model = torch.jit.load(lama_path, map_location="cpu").eval()
    with torch.inference_mode():
        o = model(torch.from_numpy(img).permute(2, 0, 1)[None].float() / 255,
                  (torch.from_numpy(m)[None, None] > 127).float())
    filled = (o[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)[:h, :w]
    a = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 3)[..., None]
    a = np.where(mask[..., None] > 127, 1.0, a)
    im = (im * (1 - a) + filled * a).round().astype(np.uint8)
    f = im.astype(np.float32)
    for x0, y0, x1, y1 in b["rowfill"]:
        x0, x1, y0, y1 = x0 - ox, x1 - ox, y0 - oy, y1 - oy
        t = np.linspace(0, 1, x1 - x0)[:, None]
        for y in range(y0, y1):
            im[y, x0:x1] = (f[y, x0 - 6:x0].mean(0) * (1 - t) + f[y, x1:x1 + 6].mean(0) * t).round().astype(np.uint8)
    Image.fromarray(im).save(src(key))
    print("wrote", src(key).name)


def fit(font, text, max_w, ink_h):
    size = 6
    while True:
        f = ImageFont.truetype(str(font), size + 1, layout_engine=ImageFont.Layout.RAQM)
        l, t, r, b = f.getbbox(text, language="km")
        if r - l > max_w or b - t > ink_h:
            return ImageFont.truetype(str(font), size, layout_engine=ImageFont.Layout.RAQM)
        size += 1


def cover_box(key):
    w, h = Image.open(src(key)).size
    return (0, 0, w, h)


def build(key, hd=False, round_corners=True):
    b, k = BOOKS[key], (4 if hd else 1)
    im = Image.open(src(key, hd)).convert("RGB")
    ox, oy = b["crop"][:2]
    for text, max_w, ink_h, cx, cy, ink, shade, bold in b["lines"]:
        f = fit(FONTS / ("Battambang-Bold.ttf" if bold else "Battambang.ttf"), text, max_w * k, ink_h * k)
        l, t, r, bb = f.getbbox(text, language="km")
        pad = int(16 * k)
        w, h = r - l + 2 * pad, bb - t + 2 * pad
        g = Image.new("L", (w, h), 0)
        ImageDraw.Draw(g).text((-l + pad, -t + pad), text, font=f, fill=255, language="km")
        x, y = int((cx - ox) * k - w / 2), int((cy - oy) * k - h / 2)
        if shade:
            sh = ImageChops.offset(g.filter(ImageFilter.GaussianBlur(2.5 * k)), round(1.5 * k), round(2 * k))
            im.paste(shade, (x, y), sh.point(lambda p: int(p * 0.65)))
        im.paste(ink, (x, y), g)
    if not round_corners:
        return im
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), 8 * k, fill=255)
    out = im.convert("RGBA")
    out.putalpha(mask)
    return out


if __name__ == "__main__":
    lama, esr, *keys = sys.argv[1:]
    for key in keys:
        erase(key, lama)
        subprocess.run([sys.executable, str(COVERS / "original" / "upscale.py"), esr, str(src(key)), str(src(key, True))],
                       check=True)
