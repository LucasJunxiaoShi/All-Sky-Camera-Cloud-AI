"""
Phase 1 checks for cloud-level classification dataset.
Run from project root: python src/check_dataset.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
METADATA_PATH = PROJECT_ROOT / "data" / "metadata.csv"

CLASSES = ["clear", "low_cloud", "medium_cloud", "high_cloud", "overcast"]
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

# Must match the header row in metadata.csv exactly
METADATA_COLUMNS = [
    "filename",
    "class_label",
    "rain(true/false)",
    "daytime",
    "notes",
]


def parse_rain(value: str) -> tuple[bool, str | None]:
    """Returns (ok, error_message). ok True if value is true/false (case-insensitive)."""
    text = (value or "").strip().lower()
    if not text:
        return False, "rain(true/false) is empty (use true or false)"
    if text in ("true", "false"):
        return True, None
    return False, f"rain(true/false) must be true or false, got {value!r}"


def parse_daytime(value: str) -> tuple[bool, str | None]:
    """Returns (ok, error_message). Allowed: day, night (case-insensitive)."""
    text = (value or "").strip().lower()
    if not text:
        return False, "daytime is empty (use day or night)"
    if text in ("day", "night"):
        return True, None
    return False, f"daytime must be day or night, got {value!r}"


def list_image_records() -> tuple[list[tuple[str, str]], list[str]]:
    """
    Returns:
      records: [(filename, class_label), ...]
      errors: structure-related errors
    """
    records: list[tuple[str, str]] = []
    errors: list[str] = []

    if not RAW_DIR.is_dir():
        errors.append(f"Missing folder: {RAW_DIR}")
        return records, errors

    # Check unexpected folders/files directly under data/raw
    for child in sorted(RAW_DIR.iterdir()):
        if child.name.startswith("."):
            continue
        if child.is_dir() and child.name not in CLASSES:
            errors.append(f"Unexpected class folder in data/raw: {child.name!r}")
        if child.is_file():
            errors.append(f"Image/file must be inside a class folder, found: {child.name!r}")

    # Collect image files in each class folder
    for class_name in CLASSES:
        class_dir = RAW_DIR / class_name
        if not class_dir.is_dir():
            errors.append(f"Missing class folder: {class_dir}")
            continue

        for p in sorted(class_dir.iterdir()):
            if p.name.startswith("."):
                continue
            if p.is_dir():
                errors.append(f"Nested folder not allowed in {class_name!r}: {p.name!r}")
                continue
            if p.suffix.lower() in ALLOWED_EXTENSIONS:
                records.append((p.name, class_name))

    return records, errors


def load_metadata() -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, str]] = []

    if not METADATA_PATH.is_file():
        errors.append(f"Missing metadata file: {METADATA_PATH}")
        return rows, errors

    # utf-8-sig strips a leading BOM if Excel added one
    with METADATA_PATH.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != METADATA_COLUMNS:
            errors.append(
                "metadata.csv header must be exactly: " + ",".join(METADATA_COLUMNS)
            )
            return rows, errors

        for row in reader:
            if not any((v or "").strip() for v in row.values()):
                continue
            rows.append(row)

    return rows, errors


def main() -> None:
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Raw data folder: {RAW_DIR}")
    print(f"Metadata file: {METADATA_PATH}")
    print()

    image_records, errors = list_image_records()
    metadata_rows, metadata_errors = load_metadata()
    errors.extend(metadata_errors)

    class_counts = {c: 0 for c in CLASSES}
    for _filename, class_name in image_records:
        class_counts[class_name] += 1

    # 1) every class has at least one image
    for class_name, count in class_counts.items():
        if count == 0:
            errors.append(f"Class has no images: {class_name!r}")

    # 2) filename uniqueness across all class folders
    seen_files: dict[str, int] = {}
    for filename, _class_name in image_records:
        seen_files[filename] = seen_files.get(filename, 0) + 1
    for filename, count in seen_files.items():
        if count > 1:
            errors.append(
                f"Filename appears in multiple class folders: {filename!r} ({count} times)"
            )

    # 3) metadata checks
    metadata_by_file: dict[str, dict[str, str]] = {}
    for row in metadata_rows:
        filename = (row.get("filename") or "").strip()
        label = (row.get("class_label") or "").strip()

        if not filename:
            errors.append("metadata.csv row has empty filename")
            continue

        if filename in metadata_by_file:
            errors.append(f"Duplicate filename in metadata.csv: {filename!r}")
        metadata_by_file[filename] = row

        if label not in CLASSES:
            errors.append(
                f"metadata.csv has invalid class_label for {filename!r}: {label!r}"
            )

        rain_val = row.get("rain(true/false)", "")
        ok_rain, rain_msg = parse_rain(rain_val)
        if not ok_rain:
            errors.append(f"{filename!r}: {rain_msg}")

        ok_day, day_msg = parse_daytime(row.get("daytime", ""))
        if not ok_day:
            errors.append(f"{filename!r}: {day_msg}")

    # each image has a metadata row
    image_to_class = {filename: class_name for filename, class_name in image_records}
    for filename in sorted(image_to_class.keys()):
        if filename not in metadata_by_file:
            errors.append(f"Missing metadata row for image: {filename!r}")

    # metadata row points to real image + class_label matches folder
    for filename, row in metadata_by_file.items():
        if filename not in image_to_class:
            errors.append(f"metadata.csv points to missing image file: {filename!r}")
            continue
        folder_class = image_to_class[filename]
        row_class = (row.get("class_label") or "").strip()
        if row_class and row_class != folder_class:
            errors.append(
                f"Class mismatch for {filename!r}: folder={folder_class!r}, metadata={row_class!r}"
            )

    # 4) imbalance warning
    non_zero_counts = [count for count in class_counts.values() if count > 0]
    warnings: list[str] = []
    if non_zero_counts:
        min_count = min(non_zero_counts)
        max_count = max(non_zero_counts)
        if min_count > 0 and max_count >= 3 * min_count:
            warnings.append(
                "Class distribution looks very imbalanced (largest class is >= 3x smallest non-empty class)."
            )

    # Summary report
    total_images = len(image_records)
    print("Class counts:")
    for class_name in CLASSES:
        print(f"  - {class_name}: {class_counts[class_name]}")
    print(f"Total images: {total_images}")
    print(f"Metadata rows: {len(metadata_rows)}")
    print()

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print("Problems found:")
        for e in errors:
            print(f"  - {e}")
        print()
        print("Fix the issues above and run again.")
        sys.exit(1)

    print("All dataset checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
