"""Kırık Testi 21 (cover image from herkul.app): remove the dark-brown
title, the "KIRIK TESTİ" letters on the gold ribbon, the author and the Süreyya logo (LaMa, dark-letter masks and a
box). The ribbon, the red 17, the torn-paper window and the linen ground stay.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "kirik-21-source.jpg"
DST = HERE / "kirik-notitle-source.png"
# (box, threshold below the local background, dilation)
REGIONS = [((110, 195, 970, 475), 25, 19), ((410, 497, 680, 555), 14, 11), ((180, 1415, 880, 1500), 25, 13)]
BOXES = []                # Süreyya logo
CONTEXT = (0, 1680)
COLS = (0, 1105)


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    for (x0, y0, x1, y1), thr, dil in REGIONS:
        reg = gray[y0:y1, x0:x1]
        bg = cv2.GaussianBlur(cv2.dilate(reg, np.ones((25, 25), np.uint8)).astype(np.float32), (0, 0), 6)
        ink = ((bg - reg.astype(np.float32)) > thr).astype(np.uint8) * 255
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        mask[y0:y1, x0:x1] |= cv2.dilate(ink, np.ones((dil, dil), np.uint8))
    for x0, y0, x1, y1 in BOXES:
        mask[y0:y1, x0:x1] = 255
    return mask


def lama(model, img, mask):
    h, w = img.shape[:2]
    pw, ph = (8 - w % 8) % 8, (8 - h % 8) % 8
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
