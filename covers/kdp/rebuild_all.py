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
    "asrin-1": (None, "1", None, A5, 251, "asrin", "ការងឿងឆ្ងល់នៃយុគសម័យ", "asrin-khmer-1-kdp-a5-251p",
                "asrin-getirdigi-tereddutler-1", "ការងឿងឆ្ងល់នៃយុគសម័យ ភាគទី១"),
    "asrin-2": (None, "2", None, B5, 292, "asrin", "ការងឿងឆ្ងល់នៃយុគសម័យ", "asrin-khmer-2-kdp-b5-292p",
                "asrin-getirdigi-tereddutler-2", "ការងឿងឆ្ងល់នៃយុគសម័យ ភាគទី២"),
    "asrin-3": (None, "3", None, A5, 307, "asrin", "ការងឿងឆ្ងល់នៃយុគសម័យ", "asrin-khmer-3-kdp-a5-307p",
                "asrin-getirdigi-tereddutler-3", "ការងឿងឆ្ងល់នៃយុគសម័យ ភាគទី៣"),
    "asrin-4": (None, "4", None, A5, 354, "asrin", "ការងឿងឆ្ងល់នៃយុគសម័យ", "asrin-khmer-4-kdp-a5-354p",
                "asrin-getirdigi-tereddutler-4", "ការងឿងឆ្ងល់នៃយុគសម័យ ភាគទី៤"),
    "cag-2": ("buhranlar", "2", "buhranlar-notitle-source-4x-noauthor.png", A5, 155, "cag", "មនុស្សក្នុងទឹកគួចនៃវិបត្តិ",
              "cag-khmer-2-kdp-a5-155p", "cag-2", "មនុស្សក្នុងទឹកគួចនៃវិបត្តិ (សម័យកាល និងជំនាន់ ២)"),
    **{f"cag-{v}": ("cagnesil", str(v), f"cag-{v}-notitle-source-4x.png", B5, n, "cag", t,
                    f"cag-khmer-{v}-kdp-b5-{n}p", f"cag-{v}", f"{t} (សម័យកាល និងជំនាន់ {d})")
       for v, n, t, d in [(6, 260, "គំនិតដែលដុះបៃតង", "៦"), (7, 368, "ជើងមេឃដែលពន្លឺលេចមក", "៧"),
                          (8, 232, "ចលនាមួយដែលគំរូមកពីខ្លួនឯង", "៨"), (9, 234, "សំឡេងស្រែកនៃភាពស្ងៀម", "៩")]},
    "cag-3": ("yitirilmis", "3", "yitirilmis-notitle-source-4x-noauthor.png", A5, 168, "cag", "ឆ្ពោះទៅរកឋានសួគ៌ដ៏បាត់បង់",
              "cag-khmer-3-kdp-a5-168p", "cag-3", "ឆ្ពោះទៅរកឋានសួគ៌ដ៏បាត់បង់ (សម័យកាល និងជំនាន់ ៣)"),
    **{f"cag-{v}": ("cagnesil", str(v), f"cag-{v}-notitle-source-4x.png", A5, n, th, t,
                    f"cag-khmer-{v}-kdp-a5-{n}p", f"cag-{v}", f"{t} (សម័យកាល និងជំនាន់ {d})")
       for v, n, th, t, d in [(4, 272, "cag", "ចំណែកមាសនៃពេលវេលា", "៤"),
                              (5, 174, "cag", "ពេលដែលថ្ងៃទាំងឡាយរសាត់ទៅរករដូវផ្ការីក", "៥"),
                              (10, 194, "cag10", "ផ្លូវនៃអ្នកដែលបានឧទ្ទិសខ្លួនចំពោះអល់ឡោះ", "១០")]},
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
    "kirik-17": ("kirik17", "17", "kirik-notitle-source-4x.png", A5, 305, "kirik17", "បន្ទាត់នៃភាពត្រឹមត្រូវ",
                 "kirik-khmer-17-kdp-a5-305p", "kirik-17", "បន្ទាត់នៃភាពត្រឹមត្រូវ (ក្អមបែក ១៧)"),
    "kirik-9": ("kirik9", "9", "kirik-notitle-source-4x.png", A5, 419, "kirik", "ទ្រនិចនៃបេះដូង",
                "kirik-khmer-9-kdp-a5-419p", "kirik-9", "ទ្រនិចនៃបេះដូង (ក្អមបែក ៩)"),
    "fasil-1": ("fasil", "1", "fasil-notitle-source-4x.png", A5, 234, "fasil", "ពីវគ្គមួយ ទៅវគ្គមួយ",
                "fasil-khmer-1-kdp-a5-234p", "fasil-1", "ពីវគ្គមួយ ទៅវគ្គមួយ ១"),
    "heykel-1": ("heykel", "1", "heykel-notitle-source-4x.png", A5, 208, "heykel", "ពេលកសាងរូបសំណាកនៃព្រលឹងយើង",
                 "heykel-khmer-1-kdp-a5-208p", "ruhumuzun-heykeli-1", "ពេលកសាងរូបសំណាកនៃព្រលឹងយើង ១"),
    "heykel-2": ("heykel2", "2", "heykel2-notitle-source-4x.png", A5, 377, "heykel2", "ឆ្ពោះទៅកាន់ពិភពផ្ទាល់ខ្លួនរបស់យើង",
                 "heykel-khmer-2-kdp-a5-377p", "ruhumuzun-heykeli-2",
                 "ពេលកសាងរូបសំណាកនៃព្រលឹងយើង ២ — ឆ្ពោះទៅកាន់ពិភពផ្ទាល់ខ្លួនរបស់យើង"),
    "asa": ("asa", "", "asa-back-4x.png", A5, 438, "asa", "ដំបងរបស់ព្យាការីមូសា",
            "asa-khmer-kdp-a5-438p", "asa-musa", "ដំបងរបស់ព្យាការីមូសា"),
    "namaz": ("namaz", "", "namaz-notitle-source-4x.png", A5, 413, "namaz", "សឡាត",
              "namaz-khmer-kdp-a5-413p", "namaz", "សឡាត — ការគោរពប្រណិប័តន៍ដ៏ជ្រាលជ្រៅដូចមៀរ៉ាជ"),
    "gonul": ("gonul", "", "gonul-notitle-source-4x.png", A5, 401, "gonul", "បទភ្លេងនៃដួងចិត្ត",
              "gonul-khmer-kdp-a5-401p", "gonul", "បទភ្លេងនៃដួងចិត្ត — ខុតហ្ពះ"),
    "beyan-1": ("beyan", "1", "beyan-notitle-source-4x.png", A5, 263, "beyan", "វោហារ",
                "beyan-khmer-1-kdp-a5-263p", "beyan-1", "វោហារ ១"),
    "fasil-2": ("fasil2", "2", "fasil2-notitle-source-4x.png", A5, 250, "fasil2", "ពីវគ្គមួយ ទៅវគ្គមួយ",
                "fasil-khmer-2-kdp-a5-250p", "fasil-2", "ពីវគ្គមួយ ទៅវគ្គមួយ ២"),
    "fasil-3": ("fasil3", "3", "fasil3-notitle-source-4x.png", A5, 306, "fasil3", "ពីវគ្គមួយ ទៅវគ្គមួយ",
                "fasil-khmer-3-kdp-a5-306p", "fasil-3", "ពីវគ្គមួយ ទៅវគ្គមួយ ៣"),
    "fasil-4": ("fasil4", "4", "fasil4-notitle-source-4x.png", A5, 257, "fasil4", "ពីវគ្គមួយ ទៅវគ្គមួយ",
                "fasil-khmer-4-kdp-a5-257p", "fasil-4", "ពីវគ្គមួយ ទៅវគ្គមួយ ៤"),
    "fasil-5": ("fasil5", "5", "fasil5-notitle-source-4x.png", A5, 222, "fasil5", "ពីវគ្គមួយ ទៅវគ្គមួយ",
                "fasil-khmer-5-kdp-a5-222p", "fasil-5", "ពីវគ្គមួយ ទៅវគ្គមួយ ៥"),
    "dunyamiz": ("dunyamiz", "", "dunyamiz-notitle-source-4x.png", A5, 684, "dunyamiz", "ពិភពរបស់យើង ក្នុងភាពធំទូលាយរបស់វា",
                 "dunyamiz-khmer-kdp-a5-684p", "dunyamiz", "ពិភពរបស់យើង ក្នុងភាពធំទូលាយរបស់វា"),
    **{f"tarihce-{v}": ("tarihce", str(v), "../asa/asa-back-4x.png", A5, n, "asa", "ប្រវត្តិជីវិត",
                        f"tarihce-khmer-{v}-kdp-a5-{n}p", f"tarihce-{v}", f"ប្រវត្តិជីវិត ភាគទី{d}")
       for v, n, d in [(1, 706, "១"), (2, 608, "២")]},
    **{f"lemalar-{v}": ("lemalar", str(v), "../asa/asa-back-4x.png", A5, n, "asa", "ពន្លឺទាំងឡាយ",
                        f"lemalar-khmer-{v}-kdp-a5-{n}p", f"lemalar-{v}", f"ពន្លឺទាំងឡាយ ភាគទី{d}")
       for v, n, d in [(1, 580, "១"), (2, 592, "២")]},
    **{f"sozler-{v}": ("sozler", str(v), "../asa/asa-back-4x.png", A5, n, "asa", "ពាក្យទាំងឡាយ",
                       f"sozler-khmer-{v}-kdp-a5-{n}p", f"sozler-{v}", f"ពាក្យទាំងឡាយ ភាគទី{d}")
       for v, n, d in [(1, 649, "១"), (2, 746, "២")]},
    "olcu": ("olcu", "", "olcu-notitle-source-4x.png", B5, 176, "olcu", "រង្វាស់ជីវិត ឬ ពន្លឺនៅលើដងផ្លូវ",
             "olcu-khmer-kdp-b5-176p", "olcu", "រង្វាស់ជីវិត ឬ ពន្លឺនៅលើដងផ្លូវ ភាគ១"),
    "icaz": ("icaz", "", "icaz-notitle-source-4x.png", B5, 571, "icaz", "ការសូត្រអាននូវអច្ឆរិយភាពមួយ",
             "icaz-khmer-kdp-b5-571p", "icaz", "ការសូត្រអាននូវអច្ឆរិយភាពមួយ"),
    "irsad": ("irsad", "", "irsad-notitle-source-4x.png", A5, 327, "irsad", "មាគ៌ានៃការផ្ដល់មគ្គុទេសក៍",
              "irsad-khmer-kdp-a5-327p", "irsad", "មាគ៌ានៃការផ្ដល់មគ្គុទេសក៍ (ការទាក់វះ)"),
    "mizrap": ("mizrap", "", "mizrap-notitle-source-4x.png", B5, 332, "mizrap", "ក្រចកដេញដែលបាក់",
               "mizrap-khmer-kdp-b5-332p", "mizrap", "ក្រចកដេញដែលបាក់ (កំណាព្យ)"),
    "kader": ("kader", "", "kader-notitle-source-4x.png", B5, 203, "kader", "កទ្រ៍ តាមទស្សនៈនៃគម្ពីរ និងស៊ុនណះ",
              "kader-khmer-kdp-b5-203p", "kader", "កទ្រ៍ តាមទស្សនៈនៃគម្ពីរ និងស៊ុនណះ"),
    "altin": ("altin", "", "altin-notitle-source-4x.png", B5, 745, "altin", "ក្នុងបរិយាកាសមាសនៃគម្ពីរគួរអាន",
              "altin-khmer-kdp-b5-745p", "altin", "ក្នុងបរិយាកាសមាសនៃគម្ពីរគួរអាន"),
    "fatiha": ("fatiha", "", "fatiha-notitle-source-4x.png", A5, 327, "fatiha", "ការពិចារណាលើស៊ូរ៉ោះអាល់ហ្វាទីហះ",
               "fatiha-khmer-kdp-a5-327p", "fatiha", "ការពិចារណាលើស៊ូរ៉ោះអាល់ហ្វាទីហះ"),
    "hitap": ("hitap", "", "hitap-notitle-source-4x.png", A5, 260, "hitap", "ផ្កានៃការអំពាវនាវ",
              "hitap-khmer-kdp-a5-260p", "hitap", "ផ្កានៃការអំពាវនាវ"),
    "hac": ("hac", "", "hac-notitle-source-4x.png", A5, 252, "hac", "ហាជ្ជ",
            "hac-khmer-kdp-a5-252p", "hac", "ការឆ្លើយតបនឹងការអំពាវនាវរបស់អល់ឡោះ៖ ហាជ្ជ"),
    "oruc": ("oruc", "", "oruc-notitle-source-4x.png", A5, 247, "oruc", "ការតមអាហារ",
             "oruc-khmer-kdp-a5-247p", "oruc", "ការតមអាហារ"),
    "zekat": ("zekat", "", "zekat-notitle-source-4x.png", A5, 388, "zekat", "ហ្សាកាត់",
              "zekat-khmer-kdp-a5-388p", "zekat", "ហ្សាកាត់"),
    "cevsen": ("cevsen", "", "cevsen-notitle-source-4x.png", A5, 237, "cevsen", "ចាវ់ស្ហាន់អាល់ខាប៊ៀរ",
               "cevsen-khmer-kdp-a5-237p", "cevsen", "ចាវ់ស្ហាន់អាល់ខាប៊ៀរ — ការបួងសួងមួយរយវគ្គ"),
    "kuran": ("kuran", "", "kuran-notitle-source-4x.png", A5, 519, "kuran", "ការឆ្លុះបញ្ចាំងពីគម្ពីរគួរអាន",
              "kuran-khmer-kdp-a5-519p", "kuran", "ការឆ្លុះបញ្ចាំងពីគម្ពីរគួរអាន ទៅកាន់ការយល់ដឹង"),
    "sohbet": ("sohbet", "", "sohbet-notitle-source-4x.png", A5, 319, "sohbet", "បរិយាកាសនៃការសន្ទនា",
               "sohbet-khmer-kdp-a5-319p", "sohbet", "បរិយាកាសនៃការសន្ទនា"),
    "varlik": ("varlik", "", "varlik-notitle-source-4x.png", A5, 474, "varlik", "វិមាត្រអរូបីនៃអត្ថិភាព",
               "varlik-khmer-kdp-a5-474p", "varlik", "វិមាត្រអរូបីនៃអត្ថិភាព"),
    "yaratilis": ("yaratilis", "", "yaratilis-notitle-source-4x.png", A5, 155, "yaratilis",
                  "ការពិតនៃការបង្កើត និងទ្រឹស្ដីវិវត្តន៍", "yaratilis-khmer-kdp-a5-155p", "yaratilis",
                  "ការពិតនៃការបង្កើត និងទ្រឹស្ដីវិវត្តន៍"),
    "vefadar": ("vefadar", "", "vefadar-notitle-source-4x.png", A5, 120, "vefadar", "សម្លាញ់ដ៏ស្មោះស្ម័គ្រ",
                "vefadar-khmer-kdp-a5-120p", "vefadar", "សម្លាញ់ដ៏ស្មោះស្ម័គ្រ — កំណាព្យ"),
    "omur": ("omur", "", "omur-notitle-source-4x.png", A5, 608, "omur", "ជីវប្រវត្តិ",
             "omur-khmer-kdp-a5-608p", "omur", "ជីវប្រវត្តិ Fethullah Gülen"),
    "kisa": ("kisa", "", "kisa-notitle-source-4x.png", A5, 370, "kisa", "តាហ្វសៀរស៊ូរ៉ោះខ្លីៗ",
             "kisa-khmer-kdp-a5-370p", "kisa-a5", "តាហ្វសៀរស៊ូរ៉ោះខ្លីៗ"),
    "baris": ("baris", "", "baris-front-600dpi.png", A5, 245, "baris", "ការរួមរស់ដោយសន្តិភាព និងការសន្ទនារវាងមនុស្សជាតិ",
              "baris-khmer-kdp-a5-245p", "baris", "ការរួមរស់ដោយសន្តិភាព និងការសន្ទនារវាងមនុស្សជាតិ"),
    "bahar": ("bahar", "", "bahar-notitle-source-4x.png", A5, 320, "bahar", "ចម្រៀងនៃនិទាឃរដូវ",
              "bahar-khmer-kdp-a5-320p", "bahar", "ចម្រៀងនៃនិទាឃរដូវ"),
    **{f"sonsuz-{v}": (f"sonsuz{v}", str(v), f"sonsuz{v}-notitle-source-4x.png", A5, n, "sonsuz", "ពន្លឺនិរន្ត",
                       f"sonsuz-khmer-{v}-kdp-a5-{n}p", f"sonsuz-{v}", f"ពន្លឺនិរន្ត ភាគ {d}")
       for v, n, d in [(1, 269, "១"), (2, 239, "២")]},
    "derin": ("derin", "", "derin-notitle-source-4x.png", B5, 523, "derin", "សីលធម៌ជ្រៅជ្រះនៃឥស្លាម",
              "derin-khmer-kdp-b5-523p", "derin", "សីលធម៌ជ្រៅជ្រះនៃឥស្លាម"),
    "cekirdek": ("cekirdek", "", "cekirdek-notitle-source-4x.png", A5, 238, "cekirdek", "ពីគ្រាប់ធញ្ញជាតិទៅដើមឈើ",
                 "cekirdek-khmer-kdp-a5-238p", "cekirdek", "ពីគ្រាប់ធញ្ញជាតិទៅដើមឈើ"),
    "olum": ("olum", "", "olum-notitle-source-4x.png", A5, 123, "olum", "សេចក្ដីស្លាប់ និងជីវិតបរលោក",
             "olum-khmer-kdp-a5-123p", "olum", "សេចក្ដីស្លាប់ និងជីវិតបរលោក"),
    "yusuf": ("yusuf", "", "yusuf-notitle-source-4x.png", A5, 371, "yusuf", "ស៊ូរ៉ោះយូសុហ្វ",
              "yusuf-khmer-kdp-a5-371p", "yusuf", "ជើងមេឃដ៏មន្តស្នេហ៍នៃគម្ពីរគួរអាន — ស៊ូរ៉ោះយូសុហ្វ"),
    **{f"soluk-{v}": ("soluk", str(v), "soluk-notitle-source-4x.png", A5, n, "soluk", "ដង្ហើមនៃដួងចិត្ត",
                      f"soluk-khmer-{v}-kdp-a5-{n}p", f"soluk-{v}", f"ដង្ហើមនៃដួងចិត្ត ភាគទី{d}")
       for v, n, d in [(1, 424, "១"), (2, 418, "២")]},
    **{f"inanc-{v}": ("inanc", str(v), "inanc-notitle-source-4x.png", A5, n, "inanc", "នៅក្រោមម្លប់នៃជំនឿ",
                      f"inanc-khmer-{v}-kdp-a5-{n}p", f"inanc-{v}", f"នៅក្រោមម្លប់នៃជំនឿ ភាគទី{d}")
       for v, n, d in [(1, 384, "១"), (2, 328, "២")]},
}

# books whose interior went through fix_gutter.py (…-interior-kdp.pdf); the others use …-interior.pdf
KDP_INTERIOR = ("cag-1", "kalbin-1", "kalbin-2", "kalbin-3", "kalbin-4", "ustadla", "kirik-2", "kirik-3", "kirik-4",
                "kirik-5", "fasil-1", "heykel-1", "heykel-2", "asa", "prizma-1", "namaz", "gonul", "asrin-1", "asrin-3", "asrin-4", "beyan-1", "fasil-2", "fasil-3", "fasil-4", "fasil-5", "dunyamiz", "lemalar-1", "lemalar-2", "fatiha", "hitap", "hac", "inanc-1", "inanc-2", "oruc", "zekat", "soluk-1", "soluk-2", "kuran", "cevsen", "yusuf", "olum", "sohbet", "varlik", "yaratilis", "vefadar", "omur", "kisa", "baris", "tarihce-1", "tarihce-2", "kirik-9", "kirik-17", "cag-2", "cag-6", "cag-7", "cag-8", "cag-9", "sozler-1", "sozler-2", "olcu", "icaz", "irsad", "mizrap", "kader", "altin", "bahar", "sonsuz-1", "sonsuz-2", "derin", "cekirdek")


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
    front = mk.build(True, round_corners=False) if folder in ("ustadla", "asa", "namaz", "gonul", "beyan", "fasil2", "fasil3", "fasil4", "fasil5", "dunyamiz", "fatiha", "hitap", "hac", "oruc", "zekat", "kuran", "cevsen", "yusuf", "olum", "sohbet", "varlik", "yaratilis", "vefadar", "omur", "kisa", "baris", "kirik17", "olcu", "icaz") else mk.build(volume, hd=True, round_corners=False)
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
    if key in KDP_INTERIOR:
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
