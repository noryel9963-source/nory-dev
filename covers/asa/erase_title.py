"""Remove the "Asâ-yı Mûsâ" title, the "Risale-i Nur Külliyatı'ndan" line, the author name and the publisher logo
(LaMa; gold-letter masks on the red velvet, a box for the logo on the ornate border).

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "asa-source.webp"
DST = HERE / "asa-notitle-source.png"
# gold letters on the red velvet: (box, green-channel lift above the local background, dilation)
REGIONS = [((178, 262, 592, 304), 28, 7),      # "Risale-i Nur Külliyatı'ndan"
           ((212, 340, 562, 702), 28, 9),      # title
           ((245, 845, 515, 968), 28, 7)]      # author
BOXES = [(338, 993, 414, 1093)]                # publisher logo on the ornate border
CONTEXT = (0, 1176)                            # rows handed to LaMa (multiple of 8)
COLS = (0, 768)


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    green = im[..., 1]
    for (x0, y0, x1, y1), thr, dil in REGIONS:
        reg = green[y0:y1, x0:x1]
        bg = cv2.GaussianBlur(cv2.erode(reg, np.ones((25, 25), np.uint8)).astype(np.float32), (0, 0), 6)
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
