"""
Test-set assembly guide for Aegis Imaging (P2 — ML Engineer).

This script does NOT auto-download anything.
Each dataset requires manual license acceptance before use.

Run this script to:
  1. Verify the expected folder structure exists
  2. Print the exact URLs + steps for each dataset
  3. Generate phashes for any images already placed in demo/test_images/
     and update data/synthetic_hash_db.json

Usage:
  cd <repo-root>
  python scripts/download_test_set.py [--hash-only]

Flags:
  --hash-only   Skip instructions, only compute/update phashes for existing images.
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
TEST_IMAGES_DIR = REPO_ROOT / "demo" / "test_images"
HASH_DB_PATH = REPO_ROOT / "data" / "synthetic_hash_db.json"
ATTRIBUTION_PATH = REPO_ROOT / "data" / "ATTRIBUTION.md"

REAL_TARGETS = [
    ("real_01_xray.png", "NIH ChestX-ray14"),
    ("real_02_xray.png", "NIH ChestX-ray14"),
    ("real_03_xray.png", "NIH ChestX-ray14"),
    ("real_04_xray.png", "NIH ChestX-ray14"),
    ("real_05_xray.png", "NIH ChestX-ray14"),
    ("real_06_xray.png", "RSNA Pneumonia Challenge"),
    ("real_07_xray.png", "RSNA Pneumonia Challenge"),
    ("real_08_mri.png",  "Kaggle Brain MRI Segmentation"),
    ("real_09_mri.png",  "Kaggle Brain MRI Segmentation"),
    ("real_10_mri.png",  "Kaggle Brain MRI Segmentation"),
]

FAKE_TARGETS = [
    "fake_01_xray.png", "fake_02_xray.png", "fake_03_xray.png",
    "fake_04_xray.png", "fake_05_xray.png", "fake_06_mri.png",
    "fake_07_mri.png",  "fake_08_mri.png",  "fake_09_ct.png",
    "fake_10_ct.png",
]

DATASET_INSTRUCTIONS = """
=============================================================================
DATASET DOWNLOAD INSTRUCTIONS
You must accept each dataset's license before downloading.
=============================================================================

1. NIH ChestX-ray14 (5 real X-rays)
   URL:     https://nihcc.app.box.com/v/ChestXray-NIHCC
   Steps:
     a. Go to the URL above and accept the data use agreement.
     b. Download images_001.tar.gz (or any tar file).
     c. Extract and pick 5 diverse images (different views/pathologies).
     d. Rename to real_01_xray.png … real_05_xray.png
     e. Place in: demo/test_images/
   License: NIH Clinical Center data use agreement (research/education only)

2. RSNA Pneumonia Detection Challenge (2 real X-rays)
   URL:     https://www.kaggle.com/c/rsna-pneumonia-detection-challenge/data
   Steps:
     a. Accept competition rules on Kaggle.
     b. Download stage_2_train_images.zip
     c. Pick 2 images: one with pneumonia, one normal.
     d. Convert .dcm → .png with: python -c "
          import pydicom, cv2, numpy as np
          ds = pydicom.dcmread('image.dcm')
          arr = ds.pixel_array.astype(float)
          arr = ((arr - arr.min())/(arr.max()-arr.min())*255).astype('uint8')
          cv2.imwrite('real_06_xray.png', arr)"
     e. Place in: demo/test_images/
   License: Kaggle competition rules

3. Kaggle Brain MRI Segmentation (3 real MRIs)
   URL:     https://www.kaggle.com/datasets/mateuszbuda/lgg-mri-segmentation
   Steps:
     a. Accept dataset license (CC BY-NC-SA 4.0).
     b. Download archive.zip
     c. Pick 3 axial slices from different patients.
     d. Rename to real_08_mri.png … real_10_mri.png
     e. Place in: demo/test_images/
   License: CC BY-NC-SA 4.0

=============================================================================
FAKE IMAGE GENERATION (10 AI-generated images, $0 cost)
=============================================================================

Use HuggingFace Spaces SDXL (free tier):
  URL: https://huggingface.co/spaces/stabilityai/stable-diffusion

Prompts to use (copy-paste each):
  fake_01_xray.png : "chest X-ray, pneumonia, grayscale, medical imaging, AP view, radiograph"
  fake_02_xray.png : "chest X-ray, bilateral infiltrates, ICU patient, portable AP radiograph"
  fake_03_mri.png  : "brain MRI axial slice, T2 weighted, glioblastoma, high resolution"
  fake_04_mri.png  : "brain MRI coronal T1 with contrast, meningioma, 3 Tesla"
  fake_05_ct.png   : "CT chest axial slice, pulmonary embolism, lung window, HRCT"
  fake_06_ct.png   : "abdominal CT axial, liver mass, contrast enhanced, portal venous phase"
  fake_07_xray.png : "chest X-ray with subtle extra rib, slight anatomy variation, AP view"
  fake_08_mri.png  : "brain MRI with subtle bilateral symmetry, axial T2"
  fake_09_ct.png   : "chest CT with subtle density gradient error, axial slice"
  fake_10_xray.png : "chest X-ray asymmetric lung fields, cardiomegaly, AP view"

Notes:
  - fake_07, fake_08, fake_09 are your "subtle" hero images — pick the ones
    where the defect is not immediately obvious to a non-radiologist.
  - Save all as PNG, resize to max 1024x1024.
  - Document exact prompts in demo/test_images/generation_log.md

=============================================================================
IMAGE CHECKLIST (verify before locking test-set-v1)
=============================================================================
  [ ] 10 real images in demo/test_images/ named real_NN_<modality>.png
  [ ] 10 fake images in demo/test_images/ named fake_NN_<modality>.png
  [ ] All images <= 1024x1024, saved as PNG
  [ ] No PHI in filenames or file metadata (strip EXIF/DICOM patient tags)
  [ ] At least 3 modalities represented (xray, mri, ct)
  [ ] At least 3 fakes are "subtle" (fake_07, fake_08, fake_09)
  [ ] At least 2 reals have unusual features (old scans, annotations)
  [ ] License/attribution noted in data/ATTRIBUTION.md
  [ ] Run this script with --hash-only to populate synthetic_hash_db.json
  [ ] git commit -m "chore: lock test-set-v1" && git tag test-set-v1
=============================================================================
"""


def compute_phashes() -> dict[str, str]:
    """Compute perceptual hashes for all fake images that exist."""
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        print("ERROR: pip install imagehash Pillow first")
        return {}

    hashes: dict[str, str] = {}
    for fname in FAKE_TARGETS:
        path = TEST_IMAGES_DIR / fname
        if path.exists():
            h = str(imagehash.phash(Image.open(path)))
            hashes[fname] = h
            print(f"  {fname}: {h}")
        else:
            print(f"  {fname}: NOT FOUND (skip)")
    return hashes


def update_hash_db(hashes: dict[str, str]) -> None:
    if not hashes:
        return
    db = json.loads(HASH_DB_PATH.read_text())
    for entry in db["hashes"]:
        fname = entry["filename"]
        if fname in hashes:
            entry["phash"] = hashes[fname]
    HASH_DB_PATH.write_text(json.dumps(db, indent=2))
    print(f"\nUpdated {HASH_DB_PATH}")


def check_structure() -> None:
    TEST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    (REPO_ROOT / "data").mkdir(parents=True, exist_ok=True)
    (REPO_ROOT / "demo" / "cached_verdicts").mkdir(parents=True, exist_ok=True)

    found_real = [f for f in REAL_TARGETS if (TEST_IMAGES_DIR / f[0]).exists()]
    found_fake = [f for f in FAKE_TARGETS if (TEST_IMAGES_DIR / f).exists()]
    print(f"Real images found:  {len(found_real)}/10")
    print(f"Fake images found:  {len(found_fake)}/10")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hash-only", action="store_true")
    args = parser.parse_args()

    check_structure()

    if not args.hash_only:
        print(DATASET_INSTRUCTIONS)

    print("\nComputing perceptual hashes for existing fake images...")
    hashes = compute_phashes()
    update_hash_db(hashes)

    missing_real = [f for f, _ in REAL_TARGETS if not (TEST_IMAGES_DIR / f).exists()]
    missing_fake = [f for f in FAKE_TARGETS if not (TEST_IMAGES_DIR / f).exists()]
    if missing_real or missing_fake:
        print(f"\nStill needed: {len(missing_real)} real, {len(missing_fake)} fake images.")
        sys.exit(1)
    else:
        print("\nAll 20 images present. Run the accuracy test: python backend/tests/test_pipeline.py")


if __name__ == "__main__":
    main()
