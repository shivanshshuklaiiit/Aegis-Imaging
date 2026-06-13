"""
Heatmap overlay utility. Draws semi-transparent bounding boxes on suspicious regions.
Used by ForensicsAgent / ClinicalAgent after P2 wires in real detection.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def overlay_heatmap(image_path: str, regions: list, output_path: str) -> bool:
    """
    Args:
        image_path: source image file path
        regions: list of {"bbox": [x1,y1,x2,y2] as 0-1 fractions,
                          "label": str, "score": float}
        output_path: where to write the annotated PNG
    Returns:
        True on success, False on failure
    """
    if not regions:
        return False

    try:
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"cv2 could not read {image_path}")
            return False

        h, w = img.shape[:2]
        overlay = img.copy()

        for r in regions:
            bbox = r.get("bbox", [])
            if len(bbox) != 4:
                continue
            x1, y1, x2, y2 = bbox
            x1, y1, x2, y2 = int(x1 * w), int(y1 * h), int(x2 * w), int(y2 * h)
            color = (0, 0, 255)  # BGR red

            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

            label = f"{r.get('label', 'anomaly')} ({r.get('score', 0):.2f})"
            cv2.putText(
                img, label, (x1, max(y1 - 8, 12)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2,
            )

        out = cv2.addWeighted(overlay, 0.3, img, 0.7, 0)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(output_path, out)
        return True

    except Exception as e:
        logger.error(f"Heatmap generation failed: {e}")
        return False
