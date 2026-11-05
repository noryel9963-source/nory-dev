"""Çağ ve Nesil 10 (Hakk'a Adanmışlar Yolu, new Süreyya design, herkul.app 826×1230): remove the yellow title,
the author signature and the Süreyya logo from the purple gradient at the bottom (LaMa on a letter mask: pixels
that differ from the local median), then smooth the refilled area so no ghost letters remain.
The flower, the drop and the gold "Çağ ve Nesil 10" badge stay.
    python3 erase_title_10.py path/to/big-lama.pt  → cag-10-notitle-source(-full).png
    python3 ../original/upscale.py RealESRGAN_x4plus.pth cag-10-notitle-source-full.png X.png → resize to
    1600×2400 = cag-10-notitle-source-4x.png
"""
import sys
from pathlib import Path
import cv2
import numpy as np
import torch
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from erase_title import lama

HERE = Path(__file__).parent
REGION = (40, 775, 790, 1228)        # title + author + logo (826×1230 pixels)

im = np.asarray(Image.open(HERE / "cag-10-source.jpg").convert("RGB")).copy()
g = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
bg = cv2.medianBlur(g, 61).astype(int)
x0, y0, x1, y1 = REGION
ink = np.zeros(g.shape, np.uint8)
d = np.abs(g.astype(int) - bg)
ink[y0:y1, x0:x1] = (d[y0:y1, x0:x1] > 14).astype(np.uint8) * 255
ink = cv2.morphologyEx(ink, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
mask = cv2.dilate(ink, np.ones((25, 25), np.uint8))
model = torch.jit.load(sys.argv[1], map_location="cpu").eval()
filled = lama(model, im, mask)
# soften whatever texture LaMa left inside the mask (the background is a smooth gradient)
soft = cv2.GaussianBlur(filled.astype(np.float32), (0, 0), 12)
rng = np.random.default_rng(3)
soft += cv2.GaussianBlur(rng.normal(0, 1.5, g.shape).astype(np.float32), (0, 0), 0.7)[..., None]
a = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 4)
a = np.where(mask > 127, 1.0, a)[..., None]
out = im * (1 - a) + soft * a
full = Image.fromarray(out.round().clip(0, 255).astype(np.uint8))
full.save(HERE / "cag-10-notitle-source-full.png")          # 826×1230: upscale.py ×4, then resize to 1600×2400
full.resize((400, 600), Image.LANCZOS).save(HERE / "cag-10-notitle-source.png")   # series size (0.7 % stretch)
Image.fromarray(mask).save(HERE / "_mask-10.png")
print("wrote cag-10-notitle-source.png")
