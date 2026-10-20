"""Remove "KUR'ÂN'IN SİHİRLİ UFKU / YUSUF sûresi" (gold) and the rose-gold author signature from the dark maroon
sky above the door. The sky is a smooth gradient, so the letters are refilled with the surrounding colour
(normalised convolution) plus a matching fine grain — no LaMa needed. The door, the glow and the stairs stay.

    python3 erase_title.py path/to/big-lama.pt
The signature crosses the door's red glow and stone arch, so that part goes to LaMa (keeps the stone texture).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "yusuf-source.webp"
DST = HERE / "yusuf-notitle-source.png"
# (box, threshold, dilation): letters = anything lighter than the local sky
REGIONS = [((80, 82, 600, 318), 14, 9),     # KUR'ÂN'IN SİHİRLİ UFKU / YUSUF / sûresi
           ((150, 308, 540, 402), 10, 9)]   # M. Fethullah Gülen
PAD = 40
LAMA = (0, 256, 708, 512)                  # rows/cols handed to LaMa for the signature (multiples of 8)


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    for (x0, y0, x1, y1), thr, dil in REGIONS:
        big = gray[y0 - PAD:y1 + PAD, x0 - PAD:x1 + PAD]
        bg = cv2.medianBlur(big, 61).astype(int)[PAD:-PAD, PAD:-PAD]
        ink = ((gray[y0:y1, x0:x1].astype(int) - bg) > thr).astype(np.uint8) * 255
        mask[y0:y1, x0:x1] |= cv2.dilate(ink, np.ones((dil, dil), np.uint8))
    return mask


def refill(im, mask, box):
    x0, y0, x1, y1 = box
    reg = im[y0 - PAD:y1 + PAD, x0 - PAD:x1 + PAD].astype(np.float32)
    m = (mask[y0 - PAD:y1 + PAD, x0 - PAD:x1 + PAD] > 127).astype(np.float32)
    keep = 1 - m
    blur = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
    smooth = blur(reg * keep[..., None], 10) / np.maximum(blur(keep, 10), 1e-3)[..., None]
    wide = blur(reg * keep[..., None], 35) / np.maximum(blur(keep, 35), 1e-3)[..., None]
    t = np.clip(blur(keep, 10) / 0.3, 0, 1)[..., None]
    smooth = smooth * t + wide * (1 - t)
    # grain: the sky's own fine noise (residual of the kept pixels)
    resid = (reg - blur(reg, 2))[keep > 0]
    sd = np.median(np.abs(resid), axis=0) * 1.4826
    rng = np.random.default_rng(7)
    smooth += blur(rng.normal(0, 1, reg.shape[:2]).astype(np.float32), 0.7)[..., None] * sd * 1.6
    soft = blur(m, 1.5)[..., None]
    out = reg * (1 - soft) + smooth * soft
    sel = np.zeros(m.shape, bool)
    sel[PAD:-PAD, PAD:-PAD] = True
    im[y0 - PAD:y1 + PAD, x0 - PAD:x1 + PAD][sel] = out[sel].round().clip(0, 255).astype(np.uint8)


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
    refill(im, mask, REGIONS[0][0])
    x0, y0, x1, y1 = LAMA
    sub, msub = np.ascontiguousarray(im[y0:y1, x0:x1]), np.ascontiguousarray(mask[y0:y1, x0:x1])
    msub[:308 - y0 - 6] = 0                 # title rows already refilled
    filled = lama(model, sub, msub)
    sel = msub > 127
    sub[sel] = filled[sel]
    im[y0:y1, x0:x1] = sub
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
