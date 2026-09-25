"""Remove the red "ÖLÇÜ VEYA YOLDAKİ IŞIKLAR" title (with its drop shadow) and the author signature (LaMa).

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "olcu-source.webp"
DST = HERE / "olcu-notitle-source.png"
TITLE = (150, 400, 715, 1000)       # orange-red capitals (masked by colour)
BOXES = [(160, 405, 715, 655),      # ÖLÇÜ   (smooth gradient behind: solid blocks fill most evenly)
         (295, 655, 480, 725),      # VEYA
         (160, 740, 660, 850),      # YOLDAKİ
         (160, 860, 620, 995),      # IŞIKLAR
         (135, 1118, 575, 1212)]    # author signature on the orange band
CONTEXT = (8, 1256)                 # rows handed to LaMa (multiple of 8)
COLOR_MATCH = 0.0
COLS = (15, 845)                    # cover only


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    a = im.astype(int)
    x0, y0, x1, y1 = TITLE
    reg = a[y0:y1, x0:x1]
    red = ((reg[..., 0] - reg[..., 2] > 110) & (reg[..., 1] < 175)).astype(np.uint8) * 255   # letters
    red = cv2.morphologyEx(red, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    red = cv2.dilate(red, np.ones((9, 9), np.uint8))
    shadow = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 1]], np.uint8)                          # drop shadow
    mask[y0:y1, x0:x1] = cv2.dilate(red, shadow, iterations=6)
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
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
