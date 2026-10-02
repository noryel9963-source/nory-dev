"""Refill a small leftover speck where the Süreyya logo was (smooth gradient: normalised-convolution fill),
on both the normal and the 4x no-title artwork.

    python3 fix_speck.py
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SPECK = (370, 1150, 410, 1190)          # source px (inside the former logo box)


def refill(path, k):
    im = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    x0, y0, x1, y1 = (v * k for v in SPECK)
    pad = 40 * k
    X0, Y0, X1, Y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    reg = im[Y0:Y1, X0:X1]
    keep = np.ones(reg.shape[:2], np.float32)
    keep[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = 0
    s = 12 * k
    smooth = cv2.GaussianBlur(reg * keep[..., None], (0, 0), s) / np.maximum(cv2.GaussianBlur(keep, (0, 0), s), 1e-3)[..., None]
    soft = cv2.GaussianBlur(1 - keep, (0, 0), 2 * k)[..., None]
    im[Y0:Y1, X0:X1] = reg * (1 - soft) + smooth * soft
    Image.fromarray(im.round().clip(0, 255).astype(np.uint8)).save(path)
    print("fixed", path.name)


if __name__ == "__main__":
    refill(HERE / "namaz-notitle-source.png", 1)
    refill(HERE / "namaz-notitle-source-4x.png", 4)
