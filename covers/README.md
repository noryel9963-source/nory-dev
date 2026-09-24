# Book Cover Studio

Recreates the "Asrın Getirdiği Tereddütler" cover style entirely in code (HTML canvas):
cosmic sky with nebula and planets, sunburst through clouds, glowing lava field,
Cinzel small-caps title, script author name and a volume box.

- Open `index.html` in a browser, edit title lines / author / volumes, click **Render covers**.
- **Download PNG** under each cover saves it at 836×1244.
- `index.html?solo=2` renders only volume 2 at full size (handy for screenshots).
- `preview-1.png`, `preview-2.png` are sample renders.

Fonts (SIL Open Font License) are bundled in `fonts/`: Cinzel, Pinyon Script.

## Original-art covers (`original/`)

`original/make_volumes.py` builds volume covers straight from the original cover image, so the
artwork, title and author name are identical to the source. Only the number box is repainted
(the old digit is erased by interpolating the box background) and the new number is drawn in
Cormorant Garamond with lining figures, sized to match the original "1". The old digit is
removed with OpenCV inpainting (only the digit pixels are touched).

    cd covers/original
    python3 make_volumes.py 1 2 3 4          # 815x1221   (needs Pillow, numpy, opencv-python-headless)
    python3 make_volumes.py --hd 1 2 3 4     # 3260x4884  HD versions (*-hd.png)

### HD (4x AI upscale)

`upscale.py` upscales the source 4x with Real-ESRGAN (`RealESRGAN_x4plus`) on CPU (~4 min) and
writes `asrin-getirdigi-tereddutler-1-source-4x.png`, which `--hd` uses. The upscale sharpens the
lettering a lot; painted areas (lava, clouds) get a slightly smoother, painterly look.

    pip install torch torchvision spandrel
    curl -LO https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
    python3 upscale.py RealESRGAN_x4plus.pth

Volume 1 output is the untouched original (just cropped out of the app frame).
For higher quality, replace `asrin-getirdigi-tereddutler-1-source.webp` with a larger scan and
update the measured coordinates at the top of the script.
