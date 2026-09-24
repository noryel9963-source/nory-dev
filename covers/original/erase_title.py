"""Remove the Turkish title from the source cover with LaMa AI inpainting.

    python3 erase_title.py path/to/big-lama.pt
Writes asrin-getirdigi-tereddutler-notitle-source.png (same size and framing as the source).
Weights: https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "asrin-getirdigi-tereddutler-1-source.webp"
DST = HERE / "asrin-getirdigi-tereddutler-notitle-source.png"
TITLE = (90, 520, 770, 895)       # region containing the title (source coords)
SPLIT_Y = 790                     # above: big lines with a wide dark glow; below: small line on lava
CONTEXT = (392, 1016)             # rows given to LaMa as context (multiple of 8 tall)


def title_mask(im):
    x0, y0, x1, y1 = TITLE
    reg = im[y0:y1, x0:x1].astype(float) + 1
    r, g, b = reg[..., 0], reg[..., 1], reg[..., 2]
    letters = ((r > 140) & (g / r > 0.70) & (b / r > 0.42)).astype(np.uint8) * 255
    letters = cv2.morphologyEx(letters, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    shadow = np.array([[0, 0, 0], [0, 1, 0], [0, 0, 1]], np.uint8)
    top, bottom = letters.copy(), letters.copy()
    top[SPLIT_Y - y0:] = 0
    bottom[:SPLIT_Y - y0] = 0
    top = cv2.dilate(cv2.dilate(top, np.ones((31, 31), np.uint8)), shadow, iterations=6)
    bottom = cv2.dilate(cv2.dilate(bottom, np.ones((11, 11), np.uint8)), shadow, iterations=5)
    mask = np.zeros(im.shape[:2], np.uint8)
    mask[y0:y1, x0:x1] = np.maximum(top, bottom)
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
    mask = title_mask(im)
    c0, c1 = CONTEXT
    filled = lama(model, im[c0:c1], mask[c0:c1])
    sel = mask[c0:c1] > 127
    im[c0:c1][sel] = filled[sel]
    Image.fromarray(im).save(DST)
    print("wrote", DST.name)
