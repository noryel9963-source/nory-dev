"""Text-free HD art for the KDP back cover: the front keeps "Risale-i Nur Külliyatı'ndan" and the author, the
mirrored back must not show them backwards. Erases both from the 4x art with LaMa, crop by crop.

    python3 make_back.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "asa-notitle-source-4x.png"
DST = HERE / "asa-back-4x.png"
K = 4
# (text box in source px, LaMa context box in source px)
JOBS = [((230, 316, 726, 374), (200, 280, 760, 420)),      # "Risale-i Nur Külliyatı'ndan"
        ((318, 1070, 642, 1202), (280, 1030, 680, 1230))]  # author


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


if __name__ == "__main__":
    model = torch.jit.load(sys.argv[1], map_location="cpu").eval()
    im = np.asarray(Image.open(SRC).convert("RGB")).copy()
    for box, ctx in JOBS:
        cx0, cy0, cx1, cy1 = (v * K for v in ctx)
        x0, y0, x1, y1 = (v * K for v in box)
        crop = np.ascontiguousarray(im[cy0:cy1, cx0:cx1])
        reg = crop[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0, 1]
        bg = cv2.GaussianBlur(cv2.erode(reg, np.ones((101, 101), np.uint8)).astype(np.float32), (0, 0), 24)
        ink = ((reg.astype(int) - bg) > 28).astype(np.uint8) * 255
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        mask = np.zeros(crop.shape[:2], np.uint8)
        mask[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0] = cv2.dilate(ink, np.ones((29, 29), np.uint8))
        # LaMa works best near its training size: inpaint at half resolution, paste back only the masked pixels
        small = cv2.resize(crop, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        msmall = cv2.resize(mask, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST)
        filled = cv2.resize(lama(model, small, msmall), (crop.shape[1], crop.shape[0]), interpolation=cv2.INTER_CUBIC)
        soft = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 3)[..., None]
        im[cy0:cy1, cx0:cx1] = (crop * (1 - soft) + filled * soft).round().astype(np.uint8)
    Image.fromarray(im).save(DST)
    print("wrote", DST.name)
