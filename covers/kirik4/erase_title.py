"""Remove the "ümit burcu" title, the author name and the number box contents ("KIRIK 1 TESTİ") with LaMa.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "kirik-4-source.webp"
DST = HERE / "kirik-notitle-source.png"
TITLE = (230, 720, 580, 940)        # dark red / brown lower-case title (masked by ink detection)
BOXES = [(205, 1086, 575, 1154),    # author name on the yellow band
         (664, 1052, 812, 1182)]    # number box contents: small "KIRIK", big "1", small "TESTİ"
CONTEXT = (24, 1208)                 # rows handed to LaMa (multiple of 8)
COLOR_MATCH = 0.0
COLS = (18, 817)                    # cover only


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    x0, y0, x1, y1 = TITLE
    reg = gray[y0:y1, x0:x1]
    bg = cv2.dilate(reg, np.ones((31, 31), np.uint8)).astype(np.float32)   # local maximum (bright map)
    bg = cv2.GaussianBlur(bg, (0, 0), 6)
    ink = (((bg - reg.astype(int)) > 60) | (reg < 70)).astype(np.uint8) * 255   # dark letters
    ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    ink = cv2.dilate(ink, np.ones((15, 15), np.uint8))                  # glyph edges + dark drop shadow
    shadow = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 1]], np.uint8)
    mask[y0:y1, x0:x1] = cv2.dilate(ink, shadow, iterations=4)
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
