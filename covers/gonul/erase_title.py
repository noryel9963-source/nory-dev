"""Remove "GÖNÜL NAĞMELERİ", "HUTBELER" and the author name from the Gönül Nağmeleri cover (LaMa, colour masks).

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "gonul-source.webp"
DST = HERE / "gonul-notitle-source.png"
# (box, kind, dilation): "navy" = dark blue letters on the teal sky, "white" = light letters
REGIONS = [((160, 132, 668, 262), "navy", 17),     # GÖNÜL
           ((163, 252, 625, 342), "navy", 17),     # NAĞMELERİ
           ((185, 338, 460, 472), "white", 17),    # HUTBELER
           ((160, 476, 470, 568), "navy", 17)]     # author
SKY = [(176, 132, 668, 262), (176, 252, 625, 342), (185, 338, 460, 472), (176, 476, 418, 568)]  # plain-sky parts
CONTEXT = (16, 1144)                               # rows handed to LaMa (multiple of 8)
COLS = (16, 768)


def mask_for(im):
    """Everything that differs from the plain teal sky inside each box (letters + their soft edges and shadow)."""
    mask = np.zeros(im.shape[:2], np.uint8)
    f = im.astype(np.float32)
    for (x0, y0, x1, y1), _kind, dil in REGIONS:
        reg = f[y0:y1, x0:x1]
        sky = np.array([54, 160, 166], np.float32)                       # sampled teal
        teal = (np.abs(reg - sky).sum(-1) < 60).astype(np.float32)
        bg = cv2.GaussianBlur(reg * teal[..., None], (0, 0), 25) / np.maximum(cv2.GaussianBlur(teal, (0, 0), 25), 1e-3)[..., None]
        ink = (np.abs(reg - bg).sum(-1) > 30).astype(np.uint8) * 255
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        mask[y0:y1, x0:x1] |= cv2.dilate(ink, np.ones((dil, dil), np.uint8))
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
        teal = (np.abs(reg - np.array([54, 160, 166], np.float32)).sum(-1) < 60).astype(np.float32) * (1 - m)
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
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
