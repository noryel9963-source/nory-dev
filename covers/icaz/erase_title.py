"""Remove the "BİR İ'CÂZ HECELEMESİ" title (inside the cartouche), the author name and the Nil logo (LaMa;
light-letter masks on the brown leather, a box for the logo). The cartouche ornaments stay.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "icaz-source.webp"
DST = HERE / "icaz-notitle-source.png"
# (box, threshold, dilation): letters = anything lighter OR darker than the local texture (cream letters carry a
# dark embossed shadow)
REGIONS = [((192, 402, 620, 648), 22, 13),     # title (cream on the dark cartouche) incl. the İ dots and the hat
           ((238, 828, 582, 914), 22, 11)]     # author (light orange on the leather)
BOXES = [(390, 1052, 450, 1142)]               # Nil logo
PANEL = (186, 396, 626, 656)                   # dark cartouche panel around the title
WEAVE = (230, 648, 590, 676)                   # clean strip of the panel (below the title, above the ornament)
CONTEXT = (16, 1200)                           # rows handed to LaMa (multiple of 8)
COLS = (16, 804)


def mask_for(im):
    mask = np.zeros(im.shape[:2], np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    for (x0, y0, x1, y1), thr, dil in REGIONS:
        pad = 30
        big = gray[y0 - pad:y1 + pad, x0 - pad:x1 + pad]
        bg = cv2.medianBlur(big, 41).astype(int)[pad:-pad, pad:-pad]
        reg = gray[y0:y1, x0:x1].astype(int)
        ink = (np.abs(reg - bg) > thr).astype(np.uint8) * 255
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))   # ignore the fine canvas weave
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
    # LaMa echoes the letters' embossed shadows on the dark panel: refill the masked pixels there with the panel's
    # own smooth colour (normalised convolution) plus the panel's weave copied from a clean strip below the title
    src = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
    x0, y0, x1, y1 = PANEL
    reg, m = src[y0:y1, x0:x1], (mask[y0:y1, x0:x1] > 127).astype(np.float32)
    keep = 1 - m
    blur = lambda a, s: cv2.GaussianBlur(a, (0, 0), s)
    smooth = blur(reg * keep[..., None], 18) / np.maximum(blur(keep, 18), 1e-3)[..., None]
    wide = blur(reg * keep[..., None], 60) / np.maximum(blur(keep, 60), 1e-3)[..., None]
    t = np.clip(blur(keep, 18) / 0.3, 0, 1)[..., None]
    smooth = smooth * t + wide * (1 - t)
    sx0, sy0, sx1, sy1 = WEAVE                                  # clean panel strip: its fine texture, tiled
    patch = src[sy0:sy1, sx0:sx1]
    patch = patch - blur(patch, 6)
    reps = (int(np.ceil(reg.shape[0] / patch.shape[0])), int(np.ceil(reg.shape[1] / patch.shape[1])), 1)
    weave = np.tile(patch, reps)[:reg.shape[0], :reg.shape[1]]
    soft = blur(m, 2)[..., None]
    out = reg * (1 - soft) + (smooth + weave) * soft
    im[y0:y1, x0:x1] = out.round().clip(0, 255).astype(np.uint8)
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
