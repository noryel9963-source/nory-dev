"""Remove "CEVŞEN" from the real Cevşen-i Kebîr cover (navy leather, gold corner ornaments). The user's phone
screenshot shows the cover at only 182×263 px, so cevsen-crop.png (the cover cut out of cevsen-source.png) is first
upscaled 4× (cevsen-crop-4x.png, Real-ESRGAN). The leather around the title is a smooth navy, so the whole title box
is replaced by a quadratic colour fit of the surrounding ring plus grain of the same strength (LaMa left ghosts).

    python3 erase_title.py
Writes cevsen-notitle-source.png (728×1052; upscale it again for the HD art).
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "cevsen-crop-4x.png"
DST = HERE / "cevsen-notitle-source.png"
TITLE = (100, 470, 600, 615)          # CEVŞEN (+ cedilla) — the dotted borders stay outside this box


def lama(model, img, mask):
    h, w = img.shape[:2]
    ph, pw = (8 - h % 8) % 8, (8 - w % 8) % 8
    img = np.pad(img, ((0, ph), (0, pw), (0, 0)), mode="reflect")
    mask = np.pad(mask, ((0, ph), (0, pw)))
    t = torch.from_numpy(img).permute(2, 0, 1)[None].float() / 255
    m = (torch.from_numpy(mask)[None, None] > 127).float()
    with torch.inference_mode():
        o = model(t, m)
    return (o[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)[:h, :w]


def smooth_fill(im, box, ring=40, seed=0):
    x0, y0, x1, y1 = box
    X0, Y0, X1, Y1 = x0 - ring, y0 - ring, x1 + ring, y1 + ring
    reg = im[Y0:Y1, X0:X1].astype(np.float64)
    yy, xx = np.mgrid[Y0:Y1, X0:X1]
    inside = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    u, v = (xx - X0) / (X1 - X0), (yy - Y0) / (Y1 - Y0)
    basis = np.stack([np.ones_like(u), u, v, u * u, u * v, v * v], -1)
    gold = (reg[..., 0] > 80) & (reg[..., 0] - reg[..., 2] > 25)      # the dotted borders: not background
    use = ~inside & ~cv2.dilate(gold.astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool)
    coef, *_ = np.linalg.lstsq(basis[use], reg[use], rcond=None)
    fit = basis @ coef
    res = reg[use] - fit[use]
    std = 1.4826 * np.median(np.abs(res - np.median(res, 0)), 0)      # robust grain strength
    noise = cv2.GaussianBlur(np.random.default_rng(seed).normal(0, 1, reg.shape[:2]), (0, 0), 0.8)
    noise *= 1 / max(noise.std(), 1e-6)
    out = fit + noise[..., None] * std
    w = np.zeros(reg.shape[:2]); w[inside] = 1
    w = cv2.GaussianBlur(w, (0, 0), 4)
    im[Y0:Y1, X0:X1] = (reg * (1 - w[..., None]) + out * w[..., None]).round().clip(0, 255).astype(np.uint8)


if __name__ == "__main__":
    im = np.asarray(Image.open(SRC).convert("RGB")).copy()
    smooth_fill(im, TITLE)
    Image.fromarray(im).save(DST)
    print("wrote", DST.name)
