"""4x enlargement for a small, heavily JPEG-compressed source.

Real-ESRGAN turns this image's 8x8 compression blocks into sharp squares, so the art is enlarged
smoothly instead (Lanczos + light blur that hides block edges) with a fine print grain added.

    python3 upscale_soft.py
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "ustadla-notitle-source.png"
DST = HERE / "ustadla-notitle-source-4x.png"

if __name__ == "__main__":
    im = Image.open(SRC).convert("RGB")
    big = np.asarray(im.resize((im.width * 4, im.height * 4), Image.LANCZOS)).astype(np.float32)
    big = cv2.GaussianBlur(big, (0, 0), 2.2)
    grain = np.random.default_rng(3).normal(0, 2.2, big.shape[:2])[..., None]
    Image.fromarray(np.clip(big + grain, 0, 255).astype(np.uint8)).save(DST)
    print("wrote", DST.name)
