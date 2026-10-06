"""Remove the "İBADET HAYATIMIZ" series label, subtitle, "ZEKÂT" title, author name and Süreyya logo of the
"Zekât" cover (İbadet Hayatımız series, like namaz/). Solid LaMa boxes between the thin rules (the
background is a smooth gradient), as in namaz/.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "zekat-source.webp"
DST = HERE / "zekat-notitle-source.png"
# (box, threshold, dilation): letters = anything lighter OR darker than the local texture (cream letters carry a
# dark embossed shadow)
# (box, threshold, dilation, opening): opening removes the fine texture; 1 = keep hairlines (pen signature)
REGIONS = []
BOXES = [(272, 61, 588, 86),      # İBADET HAYATIMIZ (between the rules, y 58 / 89)
         (150, 98, 752, 165),     # Sosyal Adaletin Temel Unsuru
         (155, 165, 737, 336),    # ZEKÂT + shadow (above the rule at y 339)
         (360, 334, 402, 350),    # Ķ comma, crossing the rule
         (205, 344, 667, 412),    # M. FETHULLAH GÜLEN
         (390, 1084, 500, 1196)]  # Süreyya logo
STRIPS = [(268, 60, 592, 87)]   # series label between its rules: each row re-interpolated from its two ends
CONTEXT = (16, 1216)
COLS = (35, 829)

def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    for (x0, y0, x1, y1), thr, dil, op in REGIONS:
        pad = 30
        big = gray[y0 - pad:y1 + pad, x0 - pad:x1 + pad]
        bg = cv2.medianBlur(big, 41).astype(int)[pad:-pad, pad:-pad]
        reg = gray[y0:y1, x0:x1].astype(int)
        ink = (np.abs(reg - bg) > thr).astype(np.uint8) * 255
        if op > 1:
            ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((op, op), np.uint8))
        mask[y0:y1, x0:x1] |= cv2.dilate(ink, np.ones((dil, dil), np.uint8))
    for x0, y0, x1, y1 in BOXES:
        mask[y0:y1, x0:x1] = 255
    return mask


def lama(model, img, mask):
    h, w = img.shape[:2]
    pw = (8 - w % 8) % 8
    img = np.pad(img, ((0, 0), (0, pw), (0, 0)), mode="reflect")
    mask = np.pad(mask, ((0, 0), (0, pw)))
    t = torch.from_numpy(img).permute(2, 0, 1)[None].float() / 255
    m = (torch.from_numpy(mask)[None, None] > 127).float()
    with torch.inference_mode():
        o = model(t, m)
    return (o[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)[:, :w]


if __name__ == "__main__":
    model = torch.jit.load(sys.argv[1], map_location="cpu").eval()
    im = np.asarray(Image.open(SRC).convert("RGB")).copy()
    mask = mask_for(im)
    c0, c1 = CONTEXT
    x0, x1 = COLS
    sub = np.ascontiguousarray(im[c0:c1, x0:x1])
    msub = np.ascontiguousarray(mask[c0:c1, x0:x1])
    filled = lama(model, sub, msub)
    sel = msub > 127
    sub[sel] = filled[sel]
    im[c0:c1, x0:x1] = sub
    rng = np.random.default_rng(0)
    for x0, y0, x1, y1 in STRIPS:     # smooth horizontal gradient: LaMa regrows letter bits here, so interpolate
        left = im[y0:y1, x0 - 6:x0].astype(np.float32).mean(1)
        right = im[y0:y1, x1:x1 + 6].astype(np.float32).mean(1)
        t = np.linspace(0, 1, x1 - x0)[None, :, None]
        fill = left[:, None] * (1 - t) + right[:, None] * t + rng.normal(0, 1.2, (y1 - y0, x1 - x0, 1))
        im[y0:y1, x0:x1] = fill.round().clip(0, 255).astype(np.uint8)
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
