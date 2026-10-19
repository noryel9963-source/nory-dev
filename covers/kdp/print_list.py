"""Write ../print/PRINT-LIST.txt: every book in rebuild_all.BOOKS with title, size, pages, spine widths and whether
its print package is ready (HOLD = the interior has a known defect; see the reason).

    python3 print_list.py
"""
from rebuild_all import BOOKS, COVERS

from print_package import SIZE_NAME, SPINE_IN, mm

# books whose interior PDF has a defect only the translator can fix
HOLD = {
    "asrin-2": "30 missing letters (print as □) on pp 4, 5, 21, 29, 59, 63, 64, 114",
    "prizma-5": "9 missing letters (Arabic words set in a Khmer font print as □)",
    "prizma-6": "905 missing letters (Arabic words set in a Khmer font print as □)",
    "prizma-7": "1,728 missing letters (Arabic words set in a Khmer font print as □)",
    "prizma-8": "1,349 missing letters (Arabic words set in a Khmer font print as □)",
    "prizma-9": "937 missing letters (Arabic words set in a Khmer font print as □)",
}


def main():
    rows = []
    for key, b in BOOKS.items():
        trim, pages, title = b[3], b[4], b[9]
        rows.append((key, title, SIZE_NAME.get(trim, trim), pages, mm(pages * SPINE_IN["cream"]),
                     mm(pages * SPINE_IN["white"]), HOLD.get(key)))
    ready = [r for r in rows if not r[6]]
    held = [r for r in rows if r[6]]
    out = [f"BOOKS READY TO PRINT / សៀវភៅរួចរាល់សម្រាប់បោះពុម្ព — {len(ready)} of {len(rows)}", "=" * 100,
           f"{'package':12} {'size':4} {'pages':>5}  {'spine cream':>11} {'spine white':>11}  title", "-" * 100]
    out += [f"{k + '-print.zip':12} {s:4} {p:5}  {c:9.1f}mm {w:9.1f}mm  {t}" for k, t, s, p, c, w, _ in ready]
    out += ["", f"ON HOLD — waiting for a corrected PDF from the translator / រង់ចាំឯកសារកែតម្រូវ — {len(held)}",
            "-" * 100]
    out += [f"{k:12} {s:4} {p:5}  {t}\n{'':14}-> {why}" for k, t, s, p, c, w, why in held]
    out += ["", "Spine widths are for Amazon KDP paper; ask a local printer for theirs. / ទំហំខ្នងគិតតាមក្រដាស Amazon KDP។"]
    (COVERS / "print" / "PRINT-LIST.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
