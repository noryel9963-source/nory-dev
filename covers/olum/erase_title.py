"""Remove "ÖLÜM ÖTESİ / HAYAT" (navy letters on the golden clouds) with LaMa and the white author signature on the
blue band (refilled with the band's own gradient). The stairs, the birds and the orange box stay.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "olum-source.webp"
DST = HERE / "olum-notitle-source.png"
TITLE = (150, 296, 722, 528)          # navy letters: bluer than the yellow clouds
BAND = (52, 1018, 655, 1166)          # blue author band (left of the orange box)
SIGN = (150, 1045, 555, 1128)         # white signature: lighter than the band
BOXES = [(682, 298, 714, 380)]  # the thin İ (and its dot)
CONTEXT = (176, 664)                  # rows handed to LaMa (multiple of 8)
COLS = (47, 815)


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
    a = im.astype(int)
    mask = np.zeros(im.shape[:2], np.uint8)
    x0, y0, x1, y1 = TITLE
    ink = ((a[y0:y1, x0:x1, 2] - a[y0:y1, x0:x1, 0]) > -15).astype(np.uint8) * 255
    mask[y0:y1, x0:x1] = cv2.dilate(ink, np.ones((11, 11), np.uint8))
    for x0, y0, x1, y1 in BOXES:
        mask[y0:y1, x0:x1] = 255
    x0, y0, x1, y1 = SIGN
    g = a[y0:y1, x0:x1].sum(2)
    ink = (g > a[BAND[1] + 5:BAND[3] - 5, BAND[0] + 5:BAND[2] - 5].sum(2).mean() + 60).astype(np.uint8) * 255
    mask[y0:y1, x0:x1] = cv2.dilate(ink, np.ones((7, 7), np.uint8))

    c0, c1 = CONTEXT
    sub = np.ascontiguousarray(im[c0:c1, COLS[0]:COLS[1]])
    msub = np.ascontiguousarray(mask[c0:c1, COLS[0]:COLS[1]])
    filled = lama(model, sub, msub)
    sel = msub > 127
    sub[sel] = filled[sel]
    im[c0:c1, COLS[0]:COLS[1]] = sub

    # the band is a smooth gradient: refill the signature with its own colour (normalised convolution)
    x0, y0, x1, y1 = BAND
    reg = im[y0:y1, x0:x1].astype(np.float32)
    m = (mask[y0:y1, x0:x1] > 127).astype(np.float32)
    keep = 1 - m
    blur = lambda v, s: cv2.GaussianBlur(v, (0, 0), s)
    smooth = blur(reg * keep[..., None], 12) / np.maximum(blur(keep, 12), 1e-3)[..., None]
    wide = blur(reg * keep[..., None], 40) / np.maximum(blur(keep, 40), 1e-3)[..., None]
    t = np.clip(blur(keep, 12) / 0.3, 0, 1)[..., None]
    smooth = smooth * t + wide * (1 - t)
    soft = blur(m, 1.5)[..., None]
    im[y0:y1, x0:x1] = (reg * (1 - soft) + smooth * soft).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
