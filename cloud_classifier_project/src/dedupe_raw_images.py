"""
Delete byte-identical duplicate images in one folder.
Prefer keeping the lowest-numbered sky_###### file if present.
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SKY_PATTERN = re.compile(r"^sky_(\d{6})\.", re.IGNORECASE)


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def list_images(folder: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(folder.iterdir()):
        if p.name.startswith("."):
            continue
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            out.append(p)
    return out


def pick_keeper(group: list[Path]) -> Path:
    sky_candidates: list[tuple[int, Path]] = []
    for p in group:
        m = SKY_PATTERN.match(p.name)
        if m:
            sky_candidates.append((int(m.group(1)), p))
    if sky_candidates:
        return min(sky_candidates, key=lambda x: x[0])[1]
    return min(group, key=lambda p: p.name.lower())


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 src/dedupe_raw_images.py <target_folder>")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    if not target.is_dir():
        print(f"Error: folder not found: {target}")
        sys.exit(1)

    groups: dict[str, list[Path]] = defaultdict(list)
    for p in list_images(target):
        groups[md5(p)].append(p)

    removed = 0
    for digest, files in groups.items():
        if len(files) < 2:
            continue
        keeper = pick_keeper(files)
        for p in files:
            if p == keeper:
                continue
            p.unlink()
            removed += 1
            print(f"Removed duplicate ({digest[:8]}...): {p.name} (kept {keeper.name})")

    if removed == 0:
        print("Dedupe: no duplicates found.")
    else:
        print(f"Dedupe: removed {removed} file(s).")


if __name__ == "__main__":
    main()
