"""Remove the author signature from the bottom band of the (title-free) cover artwork.

The bands are smooth colour gradients, so the signature rectangle is rebuilt as a Coons patch:
a smooth surface interpolated from the band colours just outside the rectangle on all four sides.

    python3 erase_author.py
Writes *-noauthor.png next to each input; make_khmer.py in both books uses those files.
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).parent

# (image, scale k, rectangle to rebuild in 1x source coords)
ASRIN = (115, 1088, 565, 1205)
CAG = (205, 1402, 748, 1552)
BUH = (92, 934, 492, 1040)
YIT = (100, 938, 512, 1044)
KAL = (95, 838, 482, 940)
PRI = (140, 1316, 712, 1474)
KEN = (120, 1062, 560, 1170)
YOL = (128, 1112, 572, 1216)
ZIH = (162, 1328, 692, 1440)
CIZ = (160, 1345, 692, 1460)
RUH = (150, 1338, 680, 1452)
JOBS = [
    ("original/asrin-getirdigi-tereddutler-notitle-source.png", 1, ASRIN),
    ("original/asrin-getirdigi-tereddutler-notitle-source-4x.png", 4, ASRIN),
    ("cag-ve-nesil/cag-ve-nesil-notitle-source.png", 1, CAG),
    ("cag-ve-nesil/cag-ve-nesil-notitle-source-4x.png", 4, CAG),
    ("buhranlar/buhranlar-notitle-source.png", 1, BUH),
    ("buhranlar/buhranlar-notitle-source-4x.png", 4, BUH),
    ("yitirilmis/yitirilmis-notitle-source.png", 1, YIT),
    ("yitirilmis/yitirilmis-notitle-source-4x.png", 4, YIT),
    ("kalbin/kalbin-notitle-source.png", 1, KAL),
    ("kalbin/kalbin-notitle-source-4x.png", 4, KAL),
    ("prizma/prizma-notitle-source.png", 1, PRI),
    ("prizma/prizma-notitle-source-4x.png", 4, PRI),
    ("kendi/kendi-notitle-source.png", 1, KEN),
    ("kendi/kendi-notitle-source-4x.png", 4, KEN),
    ("yol/yol-notitle-source.png", 1, YOL),
    ("yol/yol-notitle-source-4x.png", 4, YOL),
    ("zihin/zihin-notitle-source.png", 1, ZIH),
    ("zihin/zihin-notitle-source-4x.png", 4, ZIH),
    ("cizgimizi/cizgimizi-notitle-source.png", 1, CIZ),
    ("cizgimizi/cizgimizi-notitle-source-4x.png", 4, CIZ),
    ("ruhumuzu/ruhumuzu-notitle-source.png", 1, RUH),
    ("ruhumuzu/ruhumuzu-notitle-source-4x.png", 4, RUH),
]


def coons_fill(arr, box, k):
    x0, y0, x1, y1 = [v * k for v in box]
    a = arr.astype(np.float32)
    s = 3 * k                                             # border strip thickness
    sm = lambda v: cv2.GaussianBlur(v[None], (0, 0), sigmaX=6 * k, sigmaY=0.1)[0] if v.ndim == 2 else v
    top = sm(a[y0 - s:y0].mean(0)[x0:x1])
    bot = sm(a[y1:y1 + s].mean(0)[x0:x1])
    left = cv2.GaussianBlur(a[y0:y1, x0 - s:x0].mean(1)[:, None], (0, 0), sigmaX=0.1, sigmaY=6 * k)[:, 0]
    right = cv2.GaussianBlur(a[y0:y1, x1:x1 + s].mean(1)[:, None], (0, 0), sigmaX=0.1, sigmaY=6 * k)[:, 0]
    h, w = y1 - y0, x1 - x0
    u = np.linspace(0, 1, w)[None, :, None]
    v = np.linspace(0, 1, h)[:, None, None]
    c00, c10, c01, c11 = top[0], top[-1], bot[0], bot[-1]
    patch = ((1 - v) * top[None] + v * bot[None] + (1 - u) * left[:, None] + u * right[:, None]
             - ((1 - u) * (1 - v) * c00 + u * (1 - v) * c10 + (1 - u) * v * c01 + u * v * c11))
    patch += np.random.default_rng(1).normal(0, 0.8, patch.shape)   # keep the print from looking plastic
    out = arr.copy()
    out[y0:y1, x0:x1] = np.clip(patch, 0, 255).astype(np.uint8)
    return out


def destreak(arr, k, rows, cols, skip_cols):
    """Vertical-only blur over a strip: removes horizontal streaks the 4x upscaler left in a smooth band."""
    y0, y1 = rows[0] * k, rows[1] * k
    blurred = cv2.GaussianBlur(arr[y0:y1].astype(np.float32), (0, 0), sigmaX=0.1, sigmaY=5 * k)
    out = arr.copy()
    keep = np.ones(arr.shape[1], bool)
    keep[:cols[0] * k] = keep[cols[1] * k:] = False
    keep[skip_cols[0] * k:skip_cols[1] * k] = False
    out[y0:y1, keep] = blurred[:, keep].astype(np.uint8)
    return out


if __name__ == "__main__":
    for path, k, box in JOBS:
        src = HERE / path
        if not src.exists():
            print("skip (missing)", path)
            continue
        arr = coons_fill(np.asarray(Image.open(src).convert("RGB")), box, k)
        if box is CAG and k == 4:
            arr = destreak(arr, k, rows=(1384, 1428), cols=(30, 1079), skip_cols=(0, 0))
        if box is RUH and k == 4:
            arr = destreak(arr, k, rows=(1282, 1310), cols=(14, 1009), skip_cols=(0, 0))
        if box is CIZ and k == 4:
            arr = destreak(arr, k, rows=(1288, 1318), cols=(25, 1020), skip_cols=(0, 0))
        if box is ZIH and k == 4:
            arr = destreak(arr, k, rows=(1270, 1300), cols=(27, 1020), skip_cols=(0, 0))
        if box is YOL and k == 4:
            arr = destreak(arr, k, rows=(1074, 1102), cols=(18, 842), skip_cols=(0, 0))
        if box is KEN and k == 4:
            arr = destreak(arr, k, rows=(1030, 1056), cols=(23, 815), skip_cols=(0, 0))
        if box is PRI and k == 4:
            arr = destreak(arr, k, rows=(1282, 1310), cols=(19, 1009), skip_cols=(0, 0))
        if box is KAL and k == 4:
            arr = destreak(arr, k, rows=(826, 852), cols=(21, 643), skip_cols=(0, 0))
        if box is YIT and k == 4:
            arr = destreak(arr, k, rows=(918, 952), cols=(14, 715), skip_cols=(0, 0))
        if box is BUH and k == 4:
            arr = destreak(arr, k, rows=(920, 950), cols=(3, 707), skip_cols=(0, 0))
        out = src.with_name(src.stem + "-noauthor.png")
        Image.fromarray(arr).save(out)
        print("wrote", out.relative_to(HERE))
