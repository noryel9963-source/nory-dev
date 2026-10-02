"""Rebuild every finished book's KDP covers (cream + white) and reading PDF from the current make_khmer.py builders.

    python3 rebuild_all.py              # all books
    python3 rebuild_all.py kirik-2 ...  # only these keys

Front = square-corner HD build of the book's make_khmer.py; back = the book's no-title HD art, mirrored
(Asrın uses kdp_cover's own defaults). Spine and reading-PDF title font: Battambang. Interiors come from
../interior/ (not in git — re-download from Drive when missing).
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

from PIL import Image

KDP = Path(__file__).resolve().parent
COVERS = KDP.parent
TMP = Path("/tmp/kdp-rebuild")
A5, B5 = "5.833x8.263", "6.929x9.842"
SPINE_FONT = "Battambang.ttf"

# key: (folder, volume, back art, trim, pages, theme, spine title, kdp out prefix, interior, reading title)
BOOKS = {
    "asrin-1": (None, "1", None, B5, 264, "asrin", "ការងឿងឆ្ងល់នៃយុគសម័យ", "khmer-1-kdp-176x250-264p",
                "asrin-getirdigi-tereddutler-1", "ការងឿងឆ្ងល់នៃយុគសម័យ ភាគទី១"),
    "cag-1": ("cag-ve-nesil", "1", "cag-ve-nesil-notitle-source-4x-noauthor.png", A5, 168, "cag", "សម័យកាល និងជំនាន់",
              "cag-khmer-1-kdp-a5-168p", "cag-ve-nesil-1", "សម័យកាល និងជំនាន់ ១"),
    **{f"kalbin-{v}": ("kalbin", str(v), "kalbin-notitle-source-4x-noauthor.png", A5, n, "kalbin", "ភ្នំមរកតនៃដួងចិត្ត",
                       f"kalbin-khmer-{v}-kdp-a5-{n}p", f"kalbin-{v}", f"ភ្នំមរកតនៃដួងចិត្ត {v}")
       for v, n in [(1, 368), (2, 443), (3, 387), (4, 337)]},
    "ustadla": ("ustadla", "", "ustadla-notitle-source-2x.png", A5, 283, "ustadla", "ការសន្ទនាជាមួយឧស្ដាស",
                "ustadla-khmer-kdp-a5-283p", "ustadla", "ការសន្ទនាជាមួយឧស្ដាស"),
    **{f"prizma-{v}": ("prizma", str(v), "prizma-notitle-source-4x-noauthor.png", B5, n, "prizma", "ព្រិស្មា",
                       f"prizma-khmer-{v}-kdp-b5-{n}p", f"prizma-{v}", f"ព្រិស្មា {v}")
       for v, n in [(2, 222), (3, 244), (4, 284)]},
    "prizma-1": ("prizma", "1", "prizma-notitle-source-4x-noauthor.png", A5, 255, "prizma", "ព្រិស្មា",
                 "prizma-khmer-1-kdp-a5-255p", "prizma-1", "ព្រិស្មា ១"),
    "prizma-5": ("kendi", "5", "kendi-notitle-source-4x-noauthor.png", B5, 219, "prizma", "បរិយាកាសផ្ទាល់ខ្លួនរបស់យើង",
                 "prizma-khmer-5-kdp-b5-219p", "prizma-5", "បរិយាកាសផ្ទាល់ខ្លួនរបស់យើង (ព្រិស្មា ៥)"),
    "prizma-6": ("yol", "6", "yol-notitle-source-4x-noauthor.png", B5, 188, "prizma6", "ការត្រិះរិះលើផ្លូវ",
                 "prizma-khmer-6-kdp-b5-188p", "prizma-6", "ការត្រិះរិះលើផ្លូវ (ព្រិស្មា ៦)"),
    "prizma-7": ("zihin", "7", "zihin-notitle-source-4x-noauthor.png", B5, 186, "prizma", "ការប្រមូលផលនៃគំនិត",
                 "prizma-khmer-7-kdp-b5-186p", "prizma-7", "ការប្រមូលផលនៃគំនិត (ព្រិស្មា ៧)"),
    "prizma-8": ("cizgimizi", "8", "cizgimizi-notitle-source-4x-noauthor.png", B5, 254, "prizma", "ខណៈប្រកបផ្លូវរបស់យើង",
                 "prizma-khmer-8-kdp-b5-254p", "prizma-8", "ខណៈប្រកបផ្លូវរបស់យើង (ព្រិស្មា ៨)"),
    "prizma-9": ("ruhumuzu", "9", "ruhumuzu-notitle-source-4x-noauthor.png", B5, 234, "prizma", "ស្វែងរកព្រលឹងរបស់ខ្លួនយើង",
                 "prizma-khmer-9-kdp-b5-234p", "prizma-9", "ស្វែងរកព្រលឹងរបស់ខ្លួនយើង (ព្រិស្មា ៩)"),
    "kirik-1": ("kirik", "1", "kirik-notitle-source-4x.png", B5, 284, "kirik", "ក្អមបែក",
                "kirik-khmer-1-kdp-b5-284p", "kirik-1", "ក្អមបែក ១"),
    "kirik-2": ("kirik2", "2", "kirik-notitle-source-4x.png", A5, 253, "kirik", "ការសន្ទនាជាមួយដួងព្រលឹងជាទីស្រឡាញ់",
                "kirik-khmer-2-kdp-a5-253p", "kirik-2", "ការសន្ទនាជាមួយដួងព្រលឹងជាទីស្រឡាញ់ (ក្អមបែក ២)"),
    "kirik-3": ("kirik3", "3", "kirik-notitle-source-4x.png", A5, 337, "kirik", "ជើងមេឃនៃការនិរទេស",
                "kirik-khmer-3-kdp-a5-337p", "kirik-3", "ជើងមេឃនៃការនិរទេស (ក្អមបែក ៣)"),
    "kirik-4": ("kirik4", "4", "kirik-notitle-source-4x.png", A5, 560, "kirik", "ប៉មនៃក្ដីសង្ឃឹម",
                "kirik-khmer-4-kdp-a5-560p", "kirik-4", "ប៉មនៃក្ដីសង្ឃឹម (ក្អមបែក ៤)"),
    "kirik-5": ("kirik5", "5", "kirik-notitle-source-4x.png", A5, 682, "kirik", "ភ្លៀងពេលអាសើរ",
                "kirik-khmer-5-kdp-a5-682p", "kirik-5", "ភ្លៀងពេលអាសើរ (ក្អមបែក ៥)"),
    "fasil-1": ("fasil", "1", "fasil-notitle-source-4x.png", A5, 234, "fasil", "ពីជំពូកមួយ ទៅជំពូកមួយ",
                "fasil-khmer-1-kdp-a5-234p", "fasil-1", "ពីជំពូកមួយ ទៅជំពូកមួយ ១"),
    "heykel-1": ("heykel", "1", "heykel-notitle-source-4x.png", A5, 177, "heykel", "នៅពេលតាំងរូបសំណាកនៃព្រលឹងរបស់យើង",
                 "heykel-khmer-1-kdp-a5-177p", "ruhumuzun-heykeli-1", "នៅពេលតាំងរូបសំណាកនៃព្រលឹងរបស់យើង ១"),
    "asa": ("asa", "", "asa-back-4x.png", A5, 438, "asa", "ដំបងរបស់ព្យាការីមូសា",
            "asa-khmer-kdp-a5-438p", "asa-musa", "ដំបងរបស់ព្យាការីមូសា"),
    "namaz": ("namaz", "", "namaz-notitle-source-4x.png", A5, 413, "namaz", "សឡាត",
              "namaz-khmer-kdp-a5-413p", "namaz", "សឡាត — ការគោរពប្រណិប័តន៍ដ៏ជ្រាលជ្រៅដូចមៀរ៉ាជ"),
}


def load(folder):
    sys.path.insert(0, str(COVERS / folder))
    spec = importlib.util.spec_from_file_location(f"mk_{folder}", COVERS / folder / "make_khmer.py")
    mk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mk)
    return mk


def art(key):
    """Write the square-corner HD front and the mirrored back for one book; return their paths."""
    folder, volume, back_art = BOOKS[key][:3]
    TMP.mkdir(exist_ok=True)
    mk = load(folder)
    front = mk.build(True, round_corners=False) if folder in ("ustadla", "asa", "namaz") else mk.build(volume, hd=True, round_corners=False)
    k = round(front.width / (mk.COVER[2] - mk.COVER[0]))           # 4x upscale (Üstad'la: 2x)
    box = tuple(v * k for v in mk.COVER)
    back = Image.open(COVERS / folder / back_art).convert("RGB").crop(box).transpose(Image.FLIP_LEFT_RIGHT)
    f, b = TMP / f"{key}-front.png", TMP / f"{key}-back.png"
    front.convert("RGB").save(f)
    back.save(b)
    return f, b


def rebuild(key):
    folder, volume, _, trim, pages, theme, spine, out, interior, title = BOOKS[key]
    extra = ["--volume", volume, "--spine-title", spine, "--spine-font", SPINE_FONT, "--theme", theme]
    if folder:
        f, b = art(key)
        extra += ["--front", str(f), "--back", str(b)]
    for paper in ("cream", "white"):
        subprocess.run([sys.executable, str(KDP / "kdp_cover.py"), "build", "--trim", trim, "--pages", str(pages),
                        "--paper", paper, *extra, "-o", str(KDP / f"{out}-{paper}")],
                       check=True, cwd=KDP, stdout=subprocess.DEVNULL)
    src = COVERS / "interior" / f"{interior}-interior.pdf"
    if key in ("heykel-1", "asa", "prizma-1", "namaz"):
        src = COVERS / "interior" / f"{interior}-interior-kdp.pdf"
    if src.exists():
        subprocess.run([sys.executable, str(KDP / "combine.py"), str(src),
                        str(COVERS / "interior" / f"{interior}-with-cover.pdf"), "--title", title, *extra],
                       check=True, cwd=KDP, stdout=subprocess.DEVNULL)
    else:
        print("  (no interior, reading PDF skipped)", src.name)
    print("rebuilt", key, flush=True)


if __name__ == "__main__":
    keys = sys.argv[1:] or list(BOOKS)
    if len(keys) == 1:
        rebuild(keys[0])
    else:
        for k in keys:   # one process per book: every folder has its own make_khmer module
            subprocess.run([sys.executable, __file__, k], check=True)
