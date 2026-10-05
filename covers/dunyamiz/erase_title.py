"""Remove the "ENGİNLİĞİYLE BİZİM DÜNYAMIZ -İktisadî Mülâhazalar-" title and the author signature (LaMa; masks
catch anything lighter or darker than the local texture). The oval picture, mosque skyline and boxes stay.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "dunyamiz-source.webp"
DST = HERE / "dunyamiz-notitle-source.png"
# (box, threshold, dilation): letters = anything lighter OR darker than the local texture (cream letters carry a
# dark embossed shadow)
# (box, threshold, dilation, opening): opening removes the fine texture; 1 = keep hairlines (pen signature)
REGIONS = [((98, 515, 832, 842), 26, 13, 2),  # three title lines (cream on the orange handwriting texture)
           ((150, 1192, 612, 1294), 16, 9, 1)] # author signature on the smooth orange band
BAND = (150, 1192, 612, 1294)                  # smooth band: refilled with its own colour after LaMa
BOXES = []
CONTEXT = (24, 1344)                           # rows handed to LaMa (multiple of 8)
COLS = (27, 909)


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
    # the band under the art is a smooth gradient: refill the signature with its own colour (normalised convolution)
    src = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
    x0, y0, x1, y1 = BAND
    reg, m = src[y0 - 30:y1 + 30, x0 - 30:x1 + 30], (mask[y0 - 30:y1 + 30, x0 - 30:x1 + 30] > 127).astype(np.float32)
    keep = 1 - m
    blur = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
    smooth = blur(reg * keep[..., None], 12) / np.maximum(blur(keep, 12), 1e-3)[..., None]
    wide = blur(reg * keep[..., None], 40) / np.maximum(blur(keep, 40), 1e-3)[..., None]
    t = np.clip(blur(keep, 12) / 0.3, 0, 1)[..., None]
    smooth = smooth * t + wide * (1 - t)
    soft = blur(m, 1.5)[..., None]
    out = reg * (1 - soft) + smooth * soft
    sel = np.zeros(m.shape, bool)
    sel[30:-30, 30:-30] = True
    im[y0 - 30:y1 + 30, x0 - 30:x1 + 30][sel] = out[sel].round().clip(0, 255).astype(np.uint8)
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
