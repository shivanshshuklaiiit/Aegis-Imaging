"""
DICOM parser — extracts key metadata tags and pixel data for the pipeline.

Intentionally narrow: extracts 6 meaningful tags and pixel array only.
DICOM has 100+ tag variations; don't try to be comprehensive.

Gotcha: some DICOM files have no PixelData or use compressed transfer syntax
that pydicom can't decompress without extra codecs. Always wrap in try/except.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

try:
    import pydicom
    from pydicom.errors import InvalidDicomError
    _PYDICOM_AVAILABLE = True
except ImportError:
    _PYDICOM_AVAILABLE = False


# Tags we care about (name → DICOM keyword)
_TAGS = {
    "modality":      "Modality",
    "manufacturer":  "Manufacturer",
    "study_date":    "StudyDate",
    "patient_id":    "PatientID",
    "rows":          "Rows",
    "columns":       "Columns",
}


def parse_dicom(file_path: str) -> dict:
    """
    Parse a .dcm file and return metadata + a PNG-encoded pixel array.

    Returns:
      {
        "modality":     str | None,
        "manufacturer": str | None,
        "study_date":   str | None,
        "patient_id":   str | None,      # anonymised label only — no real PHI in demo
        "rows":         int | None,
        "columns":      int | None,
        "pixel_bytes":  bytes | None,    # PNG-encoded grayscale pixel array
        "error":        str | None,
      }
    """
    result: dict = {k: None for k in _TAGS}
    result["pixel_bytes"] = None
    result["error"] = None

    if not _PYDICOM_AVAILABLE:
        result["error"] = "pydicom not installed"
        return result

    try:
        ds = pydicom.dcmread(file_path, force=True)
    except (InvalidDicomError, FileNotFoundError, Exception) as e:
        result["error"] = f"read_failed: {e}"
        return result

    # Extract text tags
    for key, tag_name in _TAGS.items():
        try:
            val = getattr(ds, tag_name, None)
            result[key] = str(val) if val is not None else None
        except Exception:
            result[key] = None

    # Extract pixel data → PNG bytes
    result["pixel_bytes"] = _extract_pixel_bytes(ds)

    return result


def _extract_pixel_bytes(ds) -> Optional[bytes]:
    """Convert DICOM pixel array to PNG bytes (grayscale, window-levelled)."""
    try:
        pixel_array = ds.pixel_array
    except Exception:
        return None

    try:
        import cv2

        # Normalise to 8-bit
        arr = pixel_array.astype(np.float32)
        lo, hi = arr.min(), arr.max()
        if hi > lo:
            arr = ((arr - lo) / (hi - lo) * 255).astype(np.uint8)
        else:
            arr = np.zeros_like(arr, dtype=np.uint8)

        # Handle multi-frame: use first frame
        if arr.ndim == 3:
            arr = arr[0]

        success, buf = cv2.imencode(".png", arr)
        if success:
            return buf.tobytes()
    except Exception:
        pass
    return None


def is_dicom(file_path: str) -> bool:
    """Quick check for DICOM magic bytes (no full parse)."""
    try:
        with open(file_path, "rb") as f:
            f.seek(128)
            return f.read(4) == b"DICM"
    except Exception:
        return Path(file_path).suffix.lower() == ".dcm"
