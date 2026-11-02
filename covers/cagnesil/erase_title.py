"""Çağ ve Nesil 4–9 (cover images from herkul.app, 400×600, same series layout): remove the script title (white with
a soft dark shadow; vol 4 dark red), the small "Çağ ve Nesil" logo and the white author signature on the teal band
(LaMa). The art, the band and the number box (original digit) stay.

    python3 erase_title.py path/to/big-lama.pt 4 5 6 7 8 9
Writes cag-N-notitle-source.png.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

HERE = Path(__file__).parent
# title box (x0, y0, x1, y1) and how to mask it: "box" = the whole box (smooth backgrounds; the letters' soft shadows
# ghosted with a letter mask), "light" = letters brighter or darker than the local art (vol 6: detailed leaves)
TITLE = {4: ((40, 30, 345, 200), "box"), 5: ((40, 55, 345, 272), "box"), 6: ((35, 95, 362, 232), "light"),
         7: ((80, 92, 320, 272), "fit"), 8: ((40, 35, 340, 248), "box"), 9: ((60, 122, 345, 302), "box")}
LOGO = (342, 472, 392, 514)                     # small "Çağ ve Nesil" logo above the band
AUTHOR = (60, 528, 285, 584)                    # white signature on the teal band


def mask_for(im, vol):
    gray = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY).astype(int)
    mask = np.zeros(im.shape[:2], np.uint8)
    (x0, y0, x1, y1), pol = TITLE[vol]
    if pol in ("box", "fit"):
        mask[y0:y1, x0:x1] = 255
    else:
        big = gray[y0 - 30:y1 + 30, x0 - 30:x1 + 30].astype(np.uint8)
        bg = cv2.medianBlur(big, 41).astype(int)[30:-30, 30:-30]
        ink = (np.abs(gray[y0:y1, x0:x1] - bg) > 16).astype(np.uint8) * 255
        ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        mask[y0:y1, x0:x1] = cv2.dilate(ink, np.ones((9, 9), np.uint8))
    x0, y0, x1, y1 = LOGO
    mask[y0:y1, x0:x1] = 255
    x0, y0, x1, y1 = AUTHOR
    mask[y0:y1, x0:x1] = 255
    return mask


def surface_fill(im, box, ring=30, bottom=445):
    """Fill a box in a smooth sky with a cubic surface fitted to a ring around it, plus the ring's own grain."""
    x0, y0, x1, y1 = box
    X0, Y0, X1, Y1 = max(x0 - ring, 0), max(y0 - ring, 0), min(x1 + ring, im.shape[1]), min(y1 + ring, bottom)
    reg = im[Y0:Y1, X0:X1].astype(np.float32)
    h, w = reg.shape[:2]
    inside = np.zeros((h, w), bool)
    inside[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    yy, xx = np.mgrid[0:h, 0:w] / np.array([h, w])[:, None, None]
    terms = np.stack([xx ** i * yy ** j for i in range(4) for j in range(4 - i)], -1).reshape(-1, 10)
    keep = ~inside.ravel()
    fit = np.zeros_like(reg)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(terms[keep], reg[..., c].ravel()[keep], rcond=None)
        fit[..., c] = (terms @ coef).reshape(h, w)
    sd = np.median(np.abs((reg - cv2.GaussianBlur(reg, (0, 0), 1.5))[~inside]), axis=0) * 1.4826
    noise = cv2.GaussianBlur(np.random.default_rng(5).normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.6)
    fit += noise[..., None] * sd * 1.8
    a = cv2.GaussianBlur(inside.astype(np.float32), (0, 0), 4)
    a = np.where(inside, np.maximum(a, 0.0), a)[..., None]
    a = np.where(inside[..., None], 1.0, a)
    out = im.copy()
    out[Y0:Y1, X0:X1] = (reg * (1 - a) + fit * a).round().clip(0, 255).astype(np.uint8)
    return out


def lama(model, img, mask):
    h, w = img.shape[:2]
    pw, ph = (8 - w % 8) % 8, (8 - h % 8) % 8
    img = np.pad(img, ((0, ph), (0, pw), (0, 0)), mode="reflect")
    mask = np.pad(mask, ((0, ph), (0, pw)))
    t = torch.from_numpy(img).permute(2, 0, 1)[None].float() / 255
    m = (torch.from_numpy(mask)[None, None] > 127).float()
    with torch.inference_mode():
        o = model(t, m)
    return (o[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255).round().astype(np.uint8)[:h, :w]


if __name__ == "__main__":
    model = torch.jit.load(sys.argv[1], map_location="cpu").eval()
    for vol in [int(a) for a in sys.argv[2:]] or list(TITLE):
        im = np.asarray(Image.open(HERE / f"cag-{vol}-source.jpg").convert("RGB").resize((400, 600))).copy()
        mask = mask_for(im, vol)
        filled = lama(model, im, mask)
        # feathered blend: hard box edges show in smooth skies (vol 7)
        a = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 5)
        a = np.maximum(a, (mask > 127).astype(np.float32) * 0.0)[..., None]
        a = np.where(mask[..., None] > 127, 1.0, a)
        im = (im * (1 - a) + filled * a).round().astype(np.uint8)
        (bx0, by0, bx1, by1), pol = TITLE[vol]
        if pol == "fit":
            im = surface_fill(im, (bx0, by0, bx1, by1))
            im = surface_fill(im, LOGO, ring=20, bottom=514)
        # the band is a smooth horizontal gradient: refill the signature box row by row between its edges
        x0, y0, x1, y1 = AUTHOR
        f = im.astype(np.float32)
        for y in range(y0, y1):
            left, right = f[y, x0 - 8:x0].mean(0), f[y, x1:x1 + 8].mean(0)
            t = np.linspace(0, 1, x1 - x0)[:, None]
            im[y, x0:x1] = (left * (1 - t) + right * t).round().astype(np.uint8)
        Image.fromarray(im).save(HERE / f"cag-{vol}-notitle-source.png")
        Image.fromarray(mask).save(HERE / f"_mask-{vol}.png")
        print("wrote", f"cag-{vol}-notitle-source.png")
