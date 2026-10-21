"""Remove the black script "Yâr-ı Vefâdâr", the green "Münacat ve Naatlar" (on the cream medallion) and the cream
author signature on the green felt (LaMa). Letter mask on the medallion = dark pixels inside the cream area (the cream
area is closed over the letters, so the ornament's own dark-green panels are never touched).

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "vefadar-source.webp"
DST = HERE / "vefadar-notitle-source.png"
MEDALLION = (150, 380, 760, 900)      # cream-area search box
LETTERS = (195, 450, 668, 862)        # the letters themselves (keeps the top and bottom ornaments)
SIGN = (230, 1095, 600, 1215)         # author signature on the felt: lighter than the felt
CONTEXT = (32, 1336)                  # rows handed to LaMa (multiple of 8)
COLS = (28, 876)


def mask_for(im):
    a = im.astype(int)
    mask = np.zeros(im.shape[:2], np.uint8)
    x0, y0, x1, y1 = MEDALLION
    r = a[y0:y1, x0:x1]
    cream = ((r[..., 0] > 200) & (r[..., 1] > 165)).astype(np.uint8)
    area = cv2.morphologyEx(cream, cv2.MORPH_CLOSE, np.ones((41, 41), np.uint8))
    area = cv2.erode(area, np.ones((5, 5), np.uint8))
    ink = ((r.max(2) < 175) & (area > 0)).astype(np.uint8) * 255
    mask[y0:y1, x0:x1] = cv2.dilate(ink, np.ones((9, 9), np.uint8))
    keep = np.zeros_like(mask)
    lx0, ly0, lx1, ly1 = LETTERS
    keep[ly0:ly1, lx0:lx1] = 1
    mask *= keep
    x0, y0, x1, y1 = SIGN
    g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)[y0:y1, x0:x1].astype(np.float32)
    ink = ((g - cv2.GaussianBlur(g, (0, 0), 15)) > 25).astype(np.uint8) * 255
    mask[y0:y1, x0:x1] |= cv2.dilate(ink, np.ones((9, 9), np.uint8))
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
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
