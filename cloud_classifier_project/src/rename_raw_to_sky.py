"""
Rename images to sky_000001.jpg, sky_000002.jpg, ...

- Existing sky_######.* names are kept.
- Non-sky images get the next available number.
- .jpeg is normalized to .jpg.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
SKY_PATTERN = re.compile(r"^sky_(\d{6})\.", re.IGNORECASE)


def list_images(folder: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(folder.iterdir()):
        if p.name.startswith("."):
            continue
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            out.append(p)
    return out


def next_number(paths: list[Path]) -> int:
    max_num = 0
    for p in paths:
        m = SKY_PATTERN.match(p.name)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return max_num + 1


def final_name(src: Path, number: int) -> str:
    ext = src.suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return f"sky_{number:06d}.jpg"
    return f"sky_{number:06d}{ext}"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 src/rename_raw_to_sky.py <target_folder>")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    if not target.is_dir():
        print(f"Error: folder not found: {target}")
        sys.exit(1)

    images = list_images(target)
    to_rename = [p for p in images if not SKY_PATTERN.match(p.name)]
    if not to_rename:
        print("Rename: nothing to do.")
        return

    num = next_number(images)
    tmp_map: list[tuple[str, Path, Path]] = []
    for i, p in enumerate(sorted(to_rename, key=lambda x: x.name.lower())):
        tmp = target / f".__rename_tmp_{i}"
        tmp_map.append((p.name, p.resolve(), tmp))

    for _old, src, tmp in tmp_map:
        src.rename(tmp)

    for old_name, src, tmp in tmp_map:
        new_path = target / final_name(src, num)
        while new_path.exists():
            num += 1
            new_path = target / final_name(src, num)
        tmp.rename(new_path)
        print(f"Renamed: {old_name} -> {new_path.name}")
        num += 1


if __name__ == "__main__":
    main()
