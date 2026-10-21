"""Remove "VARLIĞIN / METAFİZİK BOYUTU" (white with a dark shadow) and the gold subtitle line from the starry sky with
LaMa (boxes: the letters' shadows are too soft for a deviation mask), and the white author signature on the orange
band (cubic surface fit of the band + grain). The globe, the stars and the box stay.

    python3 erase_title.py path/to/big-lama.pt
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "varlik-source.webp"
DST = HERE / "varlik-notitle-source.png"
TITLE = [(190, 296, 728, 444),        # VARLIĞIN
         (196, 444, 724, 527),        # METAFİZİK BOYUTU
         (196, 538, 726, 588),
         (526, 266, 594, 304)]        # the breve of Ğ        # RUH, MELEK, CİN VE ŞEYTANLARIN VARLIĞI VE MAHİYETLERİ
BAND = (50, 1131, 726, 1306)          # orange author band (left of the box)
SIGN = (165, 1165, 625, 1268)         # white signature: lighter than the band
CONTEXT = (40, 760)                   # rows handed to LaMa (multiple of 8)
COLS = (46, 896)


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
    a = im.astype(int)
    mask = np.zeros(im.shape[:2], np.uint8)
    for x0, y0, x1, y1 in TITLE:
        mask[y0:y1, x0:x1] = 255
    x0, y0, x1, y1 = SIGN
    g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)[y0:y1, x0:x1].astype(np.float32)
    ink = ((g - cv2.GaussianBlur(g, (0, 0), 15)) > 6).astype(np.uint8) * 255   # lighter than the band around it
    mask[y0:y1, x0:x1] = cv2.dilate(ink, np.ones((11, 11), np.uint8))

    c0, c1 = CONTEXT
    sub = np.ascontiguousarray(im[c0:c1, COLS[0]:COLS[1]])
    msub = np.ascontiguousarray(mask[c0:c1, COLS[0]:COLS[1]])
    filled = lama(model, sub, msub)
    sel = msub > 127
    sub[sel] = filled[sel]
    im[c0:c1, COLS[0]:COLS[1]] = sub

    # the band is a smooth gradient: fit a cubic surface to the band around the signature (the letters' soft glow
    # is excluded by a wide dilation) and paint it, plus the band's own grain, over the signature
    x0, y0, x1, y1 = BAND
    reg = im[y0:y1, x0:x1].astype(np.float32)
    m = cv2.dilate(mask[y0:y1, x0:x1], np.ones((25, 25), np.uint8)) > 127
    h, w = m.shape
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    terms = np.stack([xx ** i * yy ** j for i in range(4) for j in range(4 - i)], -1).reshape(-1, 10)
    keep = ~m.ravel()
    fit = np.zeros_like(reg)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(terms[keep], reg[..., c].ravel()[keep], rcond=None)
        fit[..., c] = (terms @ coef).reshape(h, w)
    resid = (reg - cv2.GaussianBlur(reg, (0, 0), 2))[~m]
    sd = np.median(np.abs(resid), axis=0) * 1.4826
    noise = cv2.GaussianBlur(np.random.default_rng(3).normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.7)
    fit += noise[..., None] * sd * 1.6
    soft = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 4)[..., None]
    im[y0:y1, x0:x1] = (reg * (1 - soft) + fit * soft).round().clip(0, 255).astype(np.uint8)
    Image.fromarray(im).save(DST)
    Image.fromarray(mask).save(HERE / "_mask.png")
    print("wrote", DST.name)
