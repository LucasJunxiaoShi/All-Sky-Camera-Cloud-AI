# Cloud Classifier Project (Phase 1)

## New project goal

This project now focuses on **classifying all-sky camera images into cloudiness levels** (not predicting exact cloud percentage).

Classes:

1. `clear`
2. `low_cloud`
3. `medium_cloud`
4. `high_cloud`
5. `overcast`

Phase 1 is only dataset organization and checks.  
No model training yet.

## Folder structure

- `data/raw/clear/` — images with mostly clear sky.
- `data/raw/low_cloud/` — light cloud presence.
- `data/raw/medium_cloud/` — moderate cloud coverage.
- `data/raw/high_cloud/` — high cloud coverage.
- `data/raw/overcast/` — fully/near-fully overcast sky.
- `data/processed/` — reserved for resized/cleaned images later.
- `data/splits/` — reserved for train/val/test split files later.
- `notebooks/` — optional analysis notebooks.
- `src/` — helper scripts (like dataset checks).
- `outputs/` — reports/logs/plots generated later.

## Where to put images

Put each image directly into the right class folder under `data/raw/`.

Example:

- `data/raw/clear/sky_000001.jpg`
- `data/raw/high_cloud/sky_000245.jpg`

Do not place images directly inside `data/raw/`.

## metadata.csv

Path: `data/metadata.csv`

Required columns (header row must match exactly):

`filename,class_label,rain(true/false),daytime,notes`

Guidelines:

- `filename` — image filename only (no full path), e.g. `sky_000001.jpg`
- `class_label` — one of: `clear`, `low_cloud`, `medium_cloud`, `high_cloud`, `overcast`
- `rain(true/false)` — either `true` or `false` (lowercase recommended; checker accepts any case)
- `daytime` — `day` or `night` (case-insensitive)
- `notes` — optional free text (anything you want to remember about the image)

Each image should have exactly one row in `metadata.csv`.

After you fill `class_label`, run:

```bash
python src/apply_metadata_classification.py
```

This will copy images from `data/raw_not_classified/` into the right class
folder under `data/raw/`. Source images stay in `raw_not_classified`.

## Why balanced classes matter

If one class has many more images than others, the classifier may over-predict that class and perform poorly on minority classes.  
Try to keep class counts reasonably balanced over time.

## Dataset check script

Run from `cloud_classifier_project/`:

```bash
python src/check_dataset.py
```

It checks:

1. Every image is inside one of the five class folders.
2. Every class has at least one image.
3. Image count per class.
4. Warns if classes are very imbalanced.
5. Filenames are unique across all class folders.
6. Every image has a row in `metadata.csv`.
7. Each row has valid `rain(true/false)` (`true` or `false` only).
8. Each row has valid `daytime` (`day` or `night` only).
9. Prints a clear summary report.

## What happens later

After this dataset structure is stable, we can move to training experiments in a later phase (for example with **Teachable Machine** or **TensorFlow**).

## Automation flow

Drive source is configured in **`.env.local_drive`** (`LOCAL_DRIVE_SOURCE`).  
**Only** this folder is used: **… → All Sky Camera → Documentation** (not the library root, not other subfolders, not the old training shortcut).

The auto-sync job does all of this:

1. Pull new **top-level** image files from that Drive folder into `data/raw_not_classified/` (existing `sky_*.jpg` files are kept; `SYNC_MODE=copy`)
2. Remove duplicate byte-identical files
3. Rename to `sky_000001.jpg` style
4. Read `data/metadata.csv` and copy labeled images into `data/raw/<class_label>/`
