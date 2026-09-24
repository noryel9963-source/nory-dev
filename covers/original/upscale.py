"""4x AI upscale of the source cover with Real-ESRGAN (x4plus), CPU-friendly tiling.

    python3 upscale.py path/to/RealESRGAN_x4plus.pth
Needs: torch, torchvision, spandrel, numpy, Pillow.
Weights: https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
"""
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from spandrel import ModelLoader

HERE = Path(__file__).parent
SRC = HERE / "asrin-getirdigi-tereddutler-1-source.webp"
DST = HERE / "asrin-getirdigi-tereddutler-1-source-4x.png"
TILE, PAD = 256, 16


def upscale(model, img):
    x = torch.from_numpy(np.asarray(img, dtype=np.float32) / 255).permute(2, 0, 1)[None]
    _, _, h, w = x.shape
    out = torch.zeros(1, 3, h * 4, w * 4)
    with torch.inference_mode():
        for y0 in range(0, h, TILE):
            for x0 in range(0, w, TILE):
                y1, x1 = min(y0 + TILE, h), min(x0 + TILE, w)
                py0, px0 = max(y0 - PAD, 0), max(x0 - PAD, 0)
                py1, px1 = min(y1 + PAD, h), min(x1 + PAD, w)
                o = model(x[:, :, py0:py1, px0:px1])
                out[:, :, y0 * 4:y1 * 4, x0 * 4:x1 * 4] = o[:, :, (y0 - py0) * 4:(y1 - py0) * 4, (x0 - px0) * 4:(x1 - px0) * 4]
    arr = (out[0].clamp(0, 1).permute(1, 2, 0).numpy() * 255).round().astype(np.uint8)
    return Image.fromarray(arr)


if __name__ == "__main__":
    torch.set_num_threads(torch.get_num_threads())
    model = ModelLoader().load_from_file(sys.argv[1]).model.eval()
    upscale(model, Image.open(SRC).convert("RGB")).save(DST)
    print("wrote", DST.name)
