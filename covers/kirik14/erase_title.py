"""Remove the "buhranlı günler ve ümit atlasımız" title, the author name and the number-box contents (LaMa, solid boxes).

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "kirik-14-source.webp"
DST = HERE / "kirik-notitle-source.png"
TITLE = (421, 250, 775, 740)        # five-line light title on the red wall (letter mask, not a box)
BOXES = [(225, 1065, 575, 1128),    # author name
         (662, 1040, 822, 1180)]    # number box contents
CONTEXT = (8, 1192)                 # rows handed to LaMa (multiple of 8)
COLOR_MATCH = 1.0
COLS = (29, 826)                    # cover only
SMOOTH = [((412, 180, 826, 820), (409, 238, 787, 752)),    # red wall (stone column is left of x 412), title
          ((662, 1008, 822, 1188), (662, 1040, 822, 1180))] # brown number box (orange stripe left of 662)


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    x0, y0, x1, y1 = TITLE
    reg = gray[y0:y1, x0:x1]
    bg = cv2.GaussianBlur(cv2.erode(reg, np.ones((31, 31), np.uint8)).astype(np.float32), (0, 0), 6)
    ink = ((reg.astype(int) - bg) > 25).astype(np.uint8) * 255      # light letters on the dark wall
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    mask[y0:y1, x0:x1] = cv2.dilate(ink, np.ones((23, 23), np.uint8))
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
    sub = np.ascontiguousarray(im[:, x0:x1])
    msub = np.ascontiguousarray(mask[:, x0:x1])
    filled = lama(model, sub[c0:c1], msub[c0:c1])
    sel = msub[c0:c1] > 127
    # LaMa's fill comes out a little lighter than this fine orange texture: shift it to the local
    # colour of the surrounding (unmasked) pixels, measured with normalised Gaussian averages.
    m = sel.astype(np.float32)
    orig = sub[c0:c1].astype(np.float32)
    f = filled.astype(np.float32)

    def correction(sigma):
        blur = lambda a: cv2.GaussianBlur(a, (0, 0), sigma)
        w_bg = blur(1 - m)[..., None]
        bg_mean = blur(orig * (1 - m)[..., None]) / np.maximum(w_bg, 1e-3)
        fill_mean = blur(f * m[..., None]) / np.maximum(blur(m)[..., None], 1e-3)
        trust = np.clip((w_bg - 0.02) / 0.1, 0, 1)    # no correction where no surrounding pixels reach
        return (bg_mean - fill_mean) * trust, trust

    fine, t_fine = correction(14)                      # thin letters: very local colour
    wide, _ = correction(40)                           # big boxes (logo): fallback
    f = np.clip(f + (fine + wide * (1 - t_fine)) * COLOR_MATCH, 0, 255).astype(np.uint8)
    sub[c0:c1][sel] = f[sel]
    im[:, x0:x1] = sub
    # The red wall and the brown number box are smooth gradients: LaMa leaves blotches there (and pulls
    # orange in from the stripe), so refill them with their own normalised-convolution colour plus grain.
    src = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
    for (wx0, wy0, wx1, wy1), (tx0, ty0, tx1, ty1) in SMOOTH:
        reg = src[wy0:wy1, wx0:wx1]
        m = (mask[wy0:wy1, wx0:wx1] > 127).astype(np.float32)
        keep = 1 - m
        blur = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
        smooth = blur(reg * keep[..., None], 18) / np.maximum(blur(keep, 18), 1e-3)[..., None]
        wide = blur(reg * keep[..., None], 45) / np.maximum(blur(keep, 45), 1e-3)[..., None]
        t = np.clip(blur(keep, 18) / 0.15, 0, 1)[..., None]
        smooth = smooth * t + wide * (1 - t)
        hf = (reg - blur(reg, 2))[keep > 0]
        grain = 1.4826 * np.median(np.abs(hf - np.median(hf, 0)), 0)   # robust: ignore edges
        rng = np.random.default_rng(14)
        noise = blur(rng.normal(0, 1, reg.shape[:2]).astype(np.float32), 0.8)
        noise = noise / noise.std()
        fill = np.clip(smooth + noise[..., None] * grain, 0, 255)
        soft = blur(m, 2)[..., None]
        out = reg * (1 - soft) + fill * soft
        area = np.zeros(mask.shape, bool)
        area[ty0:ty1, tx0:tx1] = True
        sel = area[wy0:wy1, wx0:wx1] & (soft[..., 0] > 0.01)
        im[wy0:wy1, wx0:wx1][sel] = out[sel].round().astype(np.uint8)
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
