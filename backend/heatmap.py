"""
Heatmap overlay generator.

Draws semi-transparent bounding boxes with labels over suspicious regions.
Used after verdict to produce the demo wow-factor image.

Gotcha: OpenCV reads/writes BGR, not RGB. Colors are defined as BGR tuples.
"""

from pathlib import Path

import cv2
import numpy as np


# Overlay colour (BGR): vivid red that pops on grayscale medical images
_HIGHLIGHT_COLOR = (0, 0, 220)
_ALPHA = 0.30  # opacity of the filled rectangle (0=transparent, 1=opaque)
_FONT = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE = 0.55
_FONT_THICKNESS = 2
_BORDER_THICKNESS = 2


def overlay_heatmap(
    image_path: str,
    regions: list[dict],
    output_path: str,
) -> str:
    """
    Draw suspicious-region boxes on an image and save the result.

    Args:
      image_path:  path to source image (PNG / JPEG)
      regions:     list of dicts, each with:
                     bbox  — [x1, y1, x2, y2] as fractions 0-1
                     label — short string (e.g. "clinical_anomaly")
                     score — float 0-1
      output_path: where to save the annotated image (PNG)

    Returns:
      output_path (for chaining / URL construction)
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    h, w = img.shape[:2]
    overlay = img.copy()

    for region in regions:
        bbox = region.get("bbox", [])
        if len(bbox) != 4:
            continue

        x1_f, y1_f, x2_f, y2_f = bbox
        x1 = int(x1_f * w)
        y1 = int(y1_f * h)
        x2 = int(x2_f * w)
        y2 = int(y2_f * h)

        # Filled translucent rect on overlay
        cv2.rectangle(overlay, (x1, y1), (x2, y2), _HIGHLIGHT_COLOR, -1)

        # Solid border on main image
        cv2.rectangle(img, (x1, y1), (x2, y2), _HIGHLIGHT_COLOR, _BORDER_THICKNESS)

        # Label text
        score = region.get("score", 0.0)
        label_text = f"{region.get('label', 'anomaly')} ({score:.2f})"
        text_y = max(y1 - 8, 14)
        cv2.putText(
            img,
            label_text,
            (x1, text_y),
            _FONT,
            _FONT_SCALE,
            _HIGHLIGHT_COLOR,
            _FONT_THICKNESS,
        )

    # Blend filled overlay with bordered image
    result = cv2.addWeighted(overlay, _ALPHA, img, 1.0 - _ALPHA, 0)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, result)
    return output_path


def regions_from_agent_outputs(forensics: dict, clinical: dict) -> list[dict]:
    """
    Merge suspicious_regions from both agents into one list for overlay_heatmap().
    Deduplicates by exact bbox match.
    """
    seen: set[tuple] = set()
    merged: list[dict] = []

    for source in (forensics, clinical):
        for r in source.get("suspicious_regions", []):
            key = tuple(r.get("bbox", []))
            if key not in seen and key:
                seen.add(key)
                merged.append(r)

    return merged
