"""
Copy images from data/raw_not_classified into class folders using metadata.csv.

Rules:
- Read each row in data/metadata.csv
- For rows with a valid class_label, copy filename into data/raw/<class_label>/
- Keep source image in data/raw_not_classified (copy, not move)
- If the same filename exists in other class folders, remove those copies
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"
SOURCE_DIR = PROJECT_ROOT / "data" / "raw_not_classified"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLASSES = ["clear", "low_cloud", "medium_cloud", "high_cloud", "overcast"]


def main() -> None:
    if not METADATA_PATH.is_file():
        print(f"Skip classify: metadata file not found: {METADATA_PATH}")
        return

    if not SOURCE_DIR.is_dir():
        print(f"Skip classify: source folder not found: {SOURCE_DIR}")
        return

    for class_name in CLASSES:
        (RAW_DIR / class_name).mkdir(parents=True, exist_ok=True)

    copied = 0
    removed_wrong_class = 0
    skipped_missing_source = 0
    skipped_invalid_label = 0

    with METADATA_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = (row.get("filename") or "").strip()
            class_label = (row.get("class_label") or "").strip()

            if not filename:
                continue
            if class_label not in CLASSES:
                skipped_invalid_label += 1
                continue

            src = SOURCE_DIR / filename
            if not src.is_file():
                skipped_missing_source += 1
                continue

            # Keep only one class destination for this filename.
            for other_class in CLASSES:
                if other_class == class_label:
                    continue
                wrong_path = RAW_DIR / other_class / filename
                if wrong_path.exists():
                    wrong_path.unlink()
                    removed_wrong_class += 1

            dst = RAW_DIR / class_label / filename
            shutil.copy2(src, dst)
            copied += 1

    print(f"Classify done: copied={copied}")
    print(f"Removed from wrong class folders: {removed_wrong_class}")
    print(f"Skipped (missing in raw_not_classified): {skipped_missing_source}")
    print(f"Skipped (invalid/empty class_label): {skipped_invalid_label}")


if __name__ == "__main__":
    main()
