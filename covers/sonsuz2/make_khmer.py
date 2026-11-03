"""Khmer cover for `sonsuz2/` — see ../singles/common.py (BOOKS["sonsuz2"]).  python3 make_khmer.py [--hd]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "singles"))
import common  # noqa: E402

KEY = "sonsuz2"
COVER = common.cover_box(KEY) if common.src(KEY).exists() else (0, 0, 1, 1)


def build(volume=None, hd=False, round_corners=True):
    return common.build(KEY, hd, round_corners)


if __name__ == "__main__":
    hd = "--hd" in sys.argv[1:]
    out = Path(__file__).parent / f"khmer{'-hd' if hd else ''}.png"
    build(hd=hd).save(out)
    print("wrote", out.name)
