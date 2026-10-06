"""Remove "fasıldan fasıla" (dark brown / red-brown with a soft shadow, over the paper scraps), the small
"FASILDAN FASILA" mark and the author signature on the leather band (LaMa; masks catch anything lighter or darker
than the local texture). The pen, the paper art and the number box "4" stay.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "fasil4-source.webp"
DST = HERE / "fasil4-notitle-source.png"
# (box, threshold, dilation): letters = anything lighter OR darker than the local texture (cream letters carry a
# dark embossed shadow)
# (box, threshold, dilation, opening): opening removes the fine texture; 1 = keep hairlines (pen signature)
TITLE = [(200, 135, 580, 282), (265, 275, 650, 420)]   # fasıldan / fasıla: letters = low green (the scraps are yellow/cream)
REGIONS = [((170, 930, 560, 1015), 26, 11, 1)]  # author signature on the leather band
BOXES = [(682, 862, 752, 900)]                  # small "FASILDAN FASILA" mark
CONTEXT = (8, 1064)                             # rows handed to LaMa (multiple of 8)
COLS = (81, 783)

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
    for x0, y0, x1, y1 in TITLE:
        g = im[y0:y1, x0:x1, 1].astype(int)
        ink = (g < 150).astype(np.uint8) * 255
        mask[y0:y1, x0:x1] |= cv2.dilate(ink, np.ones((13, 13), np.uint8))
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
