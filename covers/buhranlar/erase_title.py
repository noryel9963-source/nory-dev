"""Remove the "Buhranlar anaforunda İnsan" title (light script) and the series logo (dark) with LaMa.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "buhranlar-2-source.webp"
DST = HERE / "buhranlar-notitle-source.png"
TITLE = (200, 360, 620, 690)      # light script letters
LOGO = (596, 836, 707, 906)       # small dark "Çağ ve Nesil" logo
CONTEXT = (240, 904)              # rows handed to LaMa (multiple of 8 tall)


def mask_for(im):
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY).astype(int)
    mask = np.zeros(im.shape[:2], np.uint8)
    x0, y0, x1, y1 = TITLE
    reg = gray[y0:y1, x0:x1]
    bg = cv2.erode(reg.astype(np.uint8), np.ones((41, 41), np.uint8)).astype(int)    # min filter
    bg = cv2.GaussianBlur(bg.astype(np.float32), (0, 0), 10)
    ink = ((reg - bg) > 45).astype(np.uint8) * 255
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    ink = cv2.dilate(ink, np.ones((19, 19), np.uint8))
    mask[y0:y1, x0:x1] = cv2.dilate(ink, np.array([[0, 0, 0], [0, 1, 0], [0, 0, 1]], np.uint8), iterations=9)
    x0, y0, x1, y1 = LOGO
    reg = gray[y0:y1, x0:x1]
    bg = cv2.dilate(reg.astype(np.uint8), np.ones((31, 31), np.uint8)).astype(int)    # max filter
    ink = ((bg - reg) > 18).astype(np.uint8) * 255
    mask[y0:y1, x0:x1] = cv2.dilate(ink, np.ones((13, 13), np.uint8))
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
    filled = lama(model, im[c0:c1], mask[c0:c1])
    sel = mask[c0:c1] > 127
    im[c0:c1][sel] = filled[sel]
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
