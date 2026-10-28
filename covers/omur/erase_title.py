"""Remove the white script "Allah yolunda / bir ömür" (over the dark jacket and the light-blue shirt) and the author
name "FARUK MERCAN" (LaMa). The black "M. FETHULLAH GÜLEN" title stays: the Khmer edition keeps the name in Latin.
Script mask = near-white, unsaturated pixels (the shirt is bluish, so it is never masked).

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "omur-source.webp"
DST = HERE / "omur-notitle-source.png"
SCRIPT = (60, 915, 925, 1275)         # Allah yolunda / bir ömür
BOXES = [(270, 1328, 728, 1394),       # FARUK MERCAN
         (236, 935, 478, 1110)]       # the script's strokes across the light-blue shirt
CONTEXT = (24, 1480)                  # rows handed to LaMa (multiple of 8)
COLS = (27, 981)


def mask_for(im):
    a = im.astype(int)
    mask = np.zeros(im.shape[:2], np.uint8)
    x0, y0, x1, y1 = SCRIPT
    r = a[y0:y1, x0:x1]
    g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    big = g[y0 - 40:y1 + 40, x0 - 40:x1 + 40]
    bg = cv2.medianBlur(big, 45).astype(int)[40:-40, 40:-40]
    lighter = (g[y0:y1, x0:x1].astype(int) - bg) > 22          # brighter than the local picture (soft edges too)
    ink = (((r.min(2) > 200) & (r.max(2) - r.min(2) < 30)) | (lighter & (r.max(2) - r.min(2) < 40)))
    ink = cv2.morphologyEx(ink.astype(np.uint8) * 255, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    mask[y0:y1, x0:x1] = cv2.dilate(ink, np.ones((15, 15), np.uint8))
    for x0, y0, x1, y1 in BOXES:
        mask[y0:y1, x0:x1] = 255
    return mask


def lama(model, img, mask):
    h, w = img.shape[:2]
    pw = (8 - w % 8) % 8
    ph = (8 - h % 8) % 8
    img = np.pad(img, ((0, ph), (0, pw), (0, 0)), mode="reflect")
    mask = np.pad(mask, ((0, ph), (0, pw)))
    t = torch.from_numpy(img).permute(2, 0, 1)[None].float() / 255
    m = (torch.from_numpy(mask)[None, None] > 127).float()
    with torch.inference_mode():
        o = model(t, m)
    return (o[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)[:h, :w]


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
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
