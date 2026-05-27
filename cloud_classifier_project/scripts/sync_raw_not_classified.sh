#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f ".env.local_drive" ]]; then
  # shellcheck disable=SC1091
  source ".env.local_drive"
fi

SOURCE="${LOCAL_DRIVE_SOURCE:-}"
DEST="${LOCAL_RAW_NOT_CLASSIFIED_DIR:-data/raw_not_classified}"
MODE="${SYNC_MODE:-copy}" # copy | mirror

if [[ -z "${SOURCE}" ]]; then
  echo "Error: LOCAL_DRIVE_SOURCE is empty in .env.local_drive"
  exit 1
fi
if [[ ! -d "${SOURCE}" ]]; then
  echo "Error: source folder not found: ${SOURCE}"
  exit 1
fi

PYTHON3=""
for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [[ -x "${candidate}" ]]; then
    PYTHON3="${candidate}"
    break
  fi
done
if [[ -z "${PYTHON3}" ]]; then
  echo "Error: python3 not found."
  exit 1
fi

mkdir -p "${ROOT}/data"
LOCKDIR="${ROOT}/data/.raw_sync_lock"
if ! mkdir "${LOCKDIR}" 2>/dev/null; then
  echo "Skip: another sync is running."
  exit 0
fi
cleanup_lock() { rmdir "${LOCKDIR}" 2>/dev/null || true; }
trap cleanup_lock EXIT INT TERM HUP

mkdir -p "${DEST}"
echo "==> Syncing from ${SOURCE} to ${DEST} (mode=${MODE})"
# Only image files directly inside SOURCE (not nested subfolders).
# Uses find (macOS rsync is too old for --max-depth).
FIND_EXPR=(
  find "${SOURCE}" -maxdepth 1 -type f \(
  -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.bmp'
  -o -iname '*.tif' -o -iname '*.tiff' -o -iname '*.webp'
  \)
)
if [[ "${MODE}" == "mirror" ]]; then
  keep_list="$(mktemp)"
  while IFS= read -r -d '' f; do
    base="$(basename "$f")"
    echo "$base" >> "${keep_list}"
    cp -p "$f" "${DEST}/${base}"
  done < <("${FIND_EXPR[@]}" -print0)
  for f in "${DEST}"/*; do
    [[ -f "$f" ]] || continue
    base="$(basename "$f")"
    if ! grep -Fxq "$base" "${keep_list}"; then
      rm -f "$f"
      echo "Removed (mirror): ${base}"
    fi
  done
  rm -f "${keep_list}"
elif [[ "${MODE}" == "copy" ]]; then
  copied=0
  while IFS= read -r -d '' f; do
    cp -p "$f" "${DEST}/$(basename "$f")"
    copied=$((copied + 1))
  done < <("${FIND_EXPR[@]}" -print0)
  echo "Copied ${copied} top-level image(s) from Drive folder."
else
  echo "Error: SYNC_MODE must be copy or mirror"
  exit 1
fi

echo "==> Dedupe"
"${PYTHON3}" "${ROOT}/src/dedupe_raw_images.py" "${DEST}"
echo "==> Rename to sky_######"
"${PYTHON3}" "${ROOT}/src/rename_raw_to_sky.py" "${DEST}"
echo "==> Apply metadata classification (copy to class folders)"
"${PYTHON3}" "${ROOT}/src/apply_metadata_classification.py"
echo "==> Done"
