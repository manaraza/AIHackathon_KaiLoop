"""
Builds a grade manifest from the raw Kaggle fresh/rotten dataset(s) —
does NOT copy image files.

Two performance notes baked into this script, both learned the hard way
on this repo's mounted drive:
  1. Copying tens of thousands of small files onto a mounted drive is
     extremely slow, so we build a CSV manifest of (filepath, grade)
     instead. A tf.data / ImageDataGenerator pipeline should read
     straight from data/raw using this manifest — no duplication needed.
  2. Per-file stat() calls from Python (e.g. Path.is_file() in a rglob
     loop) are also extremely slow on this mount — 27k files can hang
     indefinitely. The `find` CLI does the same enumeration in under a
     second, so this script shells out to `find` for listing and does
     all classification via pure string parsing, no per-file stat calls.

Usage:
    python model/prepare_dataset.py [--include-veg]

By default only the classic apple/banana/orange set is indexed (fast,
balanced, ~13.6k images — matches the original training plan). Pass
--include-veg to also index the larger fruit/veg dataset for extra
variety later.

Output: data/graded/manifest.csv with columns: filepath,grade,source_class
    grade: A_good (fresh) | C_reject (rotten)
    Grade B (blemished-but-edible) has no source in this data — it'll be
    filled in later from the supermarket photo shoot.
"""

import argparse
import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
MANIFEST_PATH = ROOT / "data" / "graded" / "manifest.csv"

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}

CLASSIC_SET_DIRNAME = "Fresh_Rotten_Apple_Banana_Orange"
VEG_SET_DIRNAME = "Fresh_Rotten_Fruits_Vegetables"

GRADE_MAP = {
    "fresh": "A_good",
    "rotten": "C_reject",
}


def classify(folder_name: str) -> str | None:
    name = folder_name.lower()
    for prefix, grade in GRADE_MAP.items():
        if name.startswith(prefix):
            return grade
    return None


def list_files(root: Path) -> list[str]:
    """Fast file listing via `find` — avoids slow per-file Python stat()
    calls on mounted drives."""
    result = subprocess.run(
        ["find", str(root), "-type", "f"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.splitlines()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-veg", action="store_true",
                         help="Also index the larger fruit/veg dataset")
    args = parser.parse_args()

    if not RAW_DIR.exists():
        print(f"No data found in {RAW_DIR}. Unzip the Kaggle dataset there first.")
        return

    roots = [RAW_DIR / CLASSIC_SET_DIRNAME]
    if args.include_veg:
        roots.append(RAW_DIR / VEG_SET_DIRNAME)

    counts: dict[str, int] = {"A_good": 0, "C_reject": 0}
    skipped = 0
    rows = []

    for root in roots:
        if not root.exists():
            print(f"  (skipping {root}, not found)")
            continue
        for filepath in list_files(root):
            p = Path(filepath)
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            grade = classify(p.parent.name)
            if grade is None:
                skipped += 1
                continue
            rows.append((filepath, grade, p.parent.name))
            counts[grade] += 1

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filepath", "grade", "source_class"])
        writer.writerows(rows)

    print(f"Manifest written to {MANIFEST_PATH}")
    print(f"  A_good (fresh):    {counts['A_good']}")
    print(f"  C_reject (rotten): {counts['C_reject']}")
    print(f"  skipped (unmatched folder names): {skipped}")
    print(f"  total indexed: {len(rows)}")


if __name__ == "__main__":
    main()
