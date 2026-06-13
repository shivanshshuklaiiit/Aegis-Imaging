"""
ML accuracy report — runs all 20 test images through ForensicsAgent + ClinicalAgent
and outputs a confusion matrix with accuracy / precision / recall.

Target: >= 85% accuracy on the 20-image set (PRD §6).

Usage (from repo root):
  cd backend
  python -m dotenv run -- python tests/test_pipeline.py
  # or set env vars manually then:
  python tests/test_pipeline.py

Verdict threshold: combined trust score >= 0.5 → REAL, < 0.5 → FAKE.
Tune TRUST_THRESHOLD and agent weights in fft_analysis.py (ENERGY_MIN, ENERGY_RANGE)
until you hit >= 85% accuracy.
"""

import asyncio
import os
import sys
from pathlib import Path

# Allow imports from backend/ when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from agents.forensics import ForensicsAgent
from agents.clinical import ClinicalAgent

TEST_IMAGES_DIR = Path(__file__).parent.parent.parent / "demo" / "test_images"

# Threshold: combined trust score >= this → predict REAL
TRUST_THRESHOLD = 0.50

# Weights matching ForensicsAgent + ClinicalAgent outputs
# (Verdict agent will use 0.5*forensics + 0.3*clinical in full pipeline)
FORENSICS_WEIGHT = 0.625   # 0.5 / (0.5 + 0.3)
CLINICAL_WEIGHT  = 0.375   # 0.3 / (0.5 + 0.3)


async def run_image(path: Path, forensics: ForensicsAgent, clinical: ClinicalAgent) -> dict:
    context: dict = {"image_path": str(path), "sha256": "", "modality": "unknown"}
    forensics_r, clinical_r = await asyncio.gather(
        forensics.execute(context),
        clinical.execute(context),
    )
    combined_trust = (
        FORENSICS_WEIGHT * forensics_r.get("score", 0.5)
        + CLINICAL_WEIGHT * clinical_r.get("score", 0.5)
    )
    return {
        "path": path.name,
        "forensics_score": forensics_r.get("score"),
        "clinical_score": clinical_r.get("score"),
        "combined_trust": round(combined_trust, 4),
        "predict": "REAL" if combined_trust >= TRUST_THRESHOLD else "FAKE",
        "forensics_error": forensics_r.get("error"),
        "clinical_error": clinical_r.get("error"),
    }


def label_from_filename(filename: str) -> str:
    """Infer ground-truth label from filename convention: real_* → REAL, fake_* → FAKE."""
    if filename.startswith("real_"):
        return "REAL"
    if filename.startswith("fake_"):
        return "FAKE"
    raise ValueError(f"Cannot infer label from filename: {filename}. "
                     "Must start with 'real_' or 'fake_'.")


def print_confusion_matrix(results: list[dict]) -> None:
    tp = fp = tn = fn = 0
    print(f"\n{'Filename':<30} {'Truth':<6} {'Predict':<7} {'Trust':>6}  {'Match'}")
    print("-" * 65)
    for r in results:
        truth = r["truth"]
        pred = r["predict"]
        match = "OK" if truth == pred else "MISS"
        print(f"{r['path']:<30} {truth:<6} {pred:<7} {r['combined_trust']:>6.3f}  {match}")

        if truth == "REAL" and pred == "REAL":
            tp += 1
        elif truth == "FAKE" and pred == "FAKE":
            tn += 1
        elif truth == "FAKE" and pred == "REAL":
            fp += 1
        else:
            fn += 1

    total = tp + fp + tn + fn
    accuracy  = (tp + tn) / total if total else 0
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall    = tp / (tp + fn) if (tp + fn) else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0

    print("\nConfusion Matrix:")
    print(f"  TP (real→real): {tp:3d}   FP (fake→real): {fp:3d}")
    print(f"  FN (real→fake): {fn:3d}   TN (fake→fake): {tn:3d}")
    print(f"\nAccuracy:  {accuracy:.1%}  {'PASS ✓' if accuracy >= 0.85 else 'FAIL — tune weights/thresholds'}")
    print(f"Precision: {precision:.1%}")
    print(f"Recall:    {recall:.1%}")
    print(f"F1:        {f1:.3f}")

    if accuracy < 0.85:
        print("\nTuning tips:")
        print("  - Adjust ENERGY_MIN / ENERGY_RANGE in fft_analysis.py")
        print("  - Adjust FORENSICS_WEIGHT / CLINICAL_WEIGHT above")
        print("  - Adjust TRUST_THRESHOLD above")


async def main() -> None:
    images = sorted(TEST_IMAGES_DIR.glob("*.png"))
    if not images:
        print(f"No images found in {TEST_IMAGES_DIR}")
        print("Run: python scripts/download_test_set.py")
        sys.exit(1)

    print(f"Found {len(images)} images. Running agents...")

    forensics = ForensicsAgent()
    clinical = ClinicalAgent()

    tasks = [run_image(p, forensics, clinical) for p in images]
    raw_results = await asyncio.gather(*tasks)

    results = []
    errors = []
    for r in raw_results:
        try:
            truth = label_from_filename(r["path"])
            r["truth"] = truth
            results.append(r)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        print("Skipped (unlabeled):", errors)

    if results:
        print_confusion_matrix(results)
    else:
        print("No labeled images found.")


if __name__ == "__main__":
    asyncio.run(main())
