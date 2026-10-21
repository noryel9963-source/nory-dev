"""Ruhumuzun Heykelini Dikerken 2: remove the "Kendi dünyamıza doğru" cream script title, the small series title,
the author signature and the number (LaMa, light-letter masks). The dove and the arch stay.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "heykel2-source.webp"
DST = HERE / "heykel2-notitle-source.png"
# light letters on a darker background: (box, threshold above the local background, dilation)
REGIONS = [((100, 300, 452, 462), 35, 13),       # "Kendi" (left of the dove)
           ((270, 452, 660, 690), 35, 13),       # "dünyamıza doğru"
           ((675, 932, 734, 990), 30, 7),        # small "RUHUMUZUN HEYKELİNİ DİKERKEN"
           ((160, 1040, 565, 1125), 35, 11),     # author signature on the red band
           ((665, 1022, 750, 1124), 30, 11)]     # number in the box
BOXES = [(130, 444, 176, 468), (236, 444, 284, 470)]   # dark letter shadows left under "Kendi"
CONTEXT = (24, 1168)                            # rows handed to LaMa (multiple of 8)
COLS = (24, 784)                                # cover only


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    for (x0, y0, x1, y1), thr, dil in REGIONS:
        reg = gray[y0:y1, x0:x1]
        bg = cv2.GaussianBlur(cv2.erode(reg, np.ones((31, 31), np.uint8)).astype(np.float32), (0, 0), 6)
        ink = ((reg.astype(int) - bg) > thr).astype(np.uint8) * 255
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
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
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
