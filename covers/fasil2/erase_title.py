"""Remove the "Fasıldan Fasıla" title, the small "FASILDAN FASILA" mark and the author signature (LaMa; then the
smooth sky behind the title is replaced by a fitted gradient + grain). Pomegranate ornament and number box stay.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "fasil2-source.webp"
DST = HERE / "fasil2-notitle-source.png"
# (box, dilation): letters = anything that differs from its row's median colour (smooth sky / grey band)
# (box, dilation, threshold, row-median x range): letters = anything that differs from its row's median colour
REGIONS = [((110, 410, 572, 682), 13, 30, (12, 672)),     # "Fasıldan Fasıla" (dark brown on the orange sky)
           ((100, 884, 458, 960), 9, 40, (12, 470))]      # author signature (light, on the leather band)
BOXES = [(564, 804, 636, 848)]                            # small "FASILDAN FASILA" mark
SKY = []
KEEP = [(300, 380, 336, 416)]                            # pomegranate stem tip: never erase
TITLE_BOX = None                                          # LaMa alone is clean here (a fitted box left a seam)
CONTEXT = (8, 1000)                                       # rows handed to LaMa (multiple of 8)
COLS = (10, 674)


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    f = im.astype(np.float32)
    for (x0, y0, x1, y1), dil, thr, (rx0, rx1) in REGIONS:
        rows = np.median(f[y0:y1, rx0:rx1], axis=1)
        rows = cv2.GaussianBlur(rows[:, None, :], (0, 0), sigmaX=1, sigmaY=4)[:, 0, :]
        ink = (np.abs(f[y0:y1, x0:x1] - rows[:, None, :]).sum(-1) > thr).astype(np.uint8) * 255
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        mask[y0:y1, x0:x1] |= cv2.dilate(ink, np.ones((dil, dil), np.uint8))
    for x0, y0, x1, y1 in BOXES:
        mask[y0:y1, x0:x1] = 255
    for x0, y0, x1, y1 in KEEP:
        mask[y0:y1, x0:x1] = 0
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
    # the sky is a smooth teal gradient: refill the erased letters there with its own normalised-convolution colour
    # plus matching grain (LaMa leaves small specks); the minbar edges keep the LaMa fill
    src = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
    rng = np.random.default_rng(7)
    for x0, y0, x1, y1 in SKY:
        reg = src[y0 - 40:y1 + 40, x0 - 40:x1 + 40]
        m = (mask[y0 - 40:y1 + 40, x0 - 40:x1 + 40] > 127).astype(np.float32)
        teal = 1 - m
        blur = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
        smooth = blur(reg * teal[..., None], 20) / np.maximum(blur(teal, 20), 1e-3)[..., None]
        wide = blur(reg * teal[..., None], 70) / np.maximum(blur(teal, 70), 1e-3)[..., None]
        t = np.clip(blur(teal, 20) / 0.3, 0, 1)[..., None]       # few sky pixels nearby: trust the wide average
        smooth = smooth * t + wide * (1 - t)
        hf = (reg - blur(reg, 2))[teal > 0]
        grain = 1.4826 * np.median(np.abs(hf - np.median(hf, 0)), 0)
        noise = blur(rng.normal(0, 1, reg.shape[:2]).astype(np.float32), 0.8)
        fill = smooth + (noise / noise.std())[..., None] * grain
        soft = blur(m, 2)[..., None]
        out = reg * (1 - soft) + fill * soft
        sel = np.zeros(m.shape, bool)
        sel[40:-40, 40:-40] = soft[40:-40, 40:-40, 0] > 0.01
        im[y0 - 40:y1 + 40, x0 - 40:x1 + 40][sel] = out[sel].round().clip(0, 255).astype(np.uint8)
    # title box: the sky is a smooth gradient, so replace the whole box by a smooth polynomial surface fitted to sky
    # pixels well away from the letters (their glow tints nearby pixels), plus matching grain, feathered at the edges
    if TITLE_BOX is None:
        Image.fromarray(im).save(DST)
        Image.fromarray(mask).save(HERE / "_mask.png")
        sys.exit()
    x0, y0, x1, y1 = TITLE_BOX
    reg = src[y0:y1, x0:x1]
    far = cv2.dilate(mask[y0:y1, x0:x1], np.ones((41, 41), np.uint8)) == 0
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0].astype(np.float32)
    u, v = xx / (x1 - x0), yy / (y1 - y0)
    terms = [np.ones_like(u), u, v, u * u, u * v, v * v, u ** 3, u * u * v, u * v * v, v ** 3]
    A = np.stack([t[far] for t in terms], 1)
    fit = np.stack([np.stack(terms, -1) @ np.linalg.lstsq(A, reg[..., c][far], rcond=None)[0] for c in range(3)], -1)
    hf = (reg - cv2.GaussianBlur(reg, (0, 0), 2))[far]
    grain = 1.4826 * np.median(np.abs(hf - np.median(hf, 0)), 0)
    noise = cv2.GaussianBlur(np.random.default_rng(3).normal(0, 1, reg.shape[:2]).astype(np.float32), (0, 0), 0.8)
    fill = fit + (noise / noise.std())[..., None] * grain
    w = np.zeros(reg.shape[:2], np.float32)
    w[30:-30, 30:-30] = 1
    w = np.maximum(cv2.GaussianBlur(w, (0, 0), 14), (cv2.GaussianBlur(mask[y0:y1, x0:x1].astype(np.float32) / 255, (0, 0), 3) > 0.02))
    w = w[..., None]
    im[y0:y1, x0:x1] = (im[y0:y1, x0:x1] * (1 - w) + fill * w).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
