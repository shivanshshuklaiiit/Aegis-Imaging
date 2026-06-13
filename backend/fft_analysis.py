"""
FFT-based AI-generation artifact detector.

This is intentionally synchronous (CPU-bound NumPy/OpenCV work).
Call it via asyncio.to_thread() from async contexts:

    result = await asyncio.to_thread(analyze_fft, image_bytes)

Tuning guide:
  - Run on your 20-image test set and print mean_energy for real vs fake.
  - Adjust ENERGY_MIN and ENERGY_RANGE so score separates the two groups.
  - Typical values: real ~70-85, SDXL fake ~90-110.
"""

import cv2
import numpy as np


# Empirical thresholds calibrated on the 20-image test set.
# Real images scored 159–174, fakes scored 172–197.
# Boundary set to minimise misclassification: 2 fakes (171.7, 175.0) fall in
# the real zone; all 10 reals correctly score below 0.5.
ENERGY_MIN = 155.0   # below this → score = 0.0 (looks real)
ENERGY_RANGE = 40.0  # ENERGY_MIN + ENERGY_RANGE (195) → score = 1.0 (looks AI)


def analyze_fft(image_bytes: bytes) -> dict:
    """
    Compute FFT frequency spectrum and score how AI-like it looks.

    Returns:
      {
        "score": float,      # 0.0 = real, 1.0 = AI-generated
        "evidence": list[dict],
      }
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)

    if img is None:
        return {
            "score": 0.5,
            "evidence": [{"fft": "decode_failed", "note": "non-JPEG/PNG bytes?"}],
        }

    # Compute 2D FFT and shift DC to centre
    f = np.fft.fft2(img.astype(np.float32))
    fshift = np.fft.fftshift(f)
    magnitude = 20 * np.log(np.abs(fshift) + 1)

    # Sample the mid-frequency band (excl. DC peak and very high freq noise)
    h, w = magnitude.shape
    mid = magnitude[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
    mean_energy = float(np.mean(mid))

    # Normalise to [0, 1]
    score = float(np.clip((mean_energy - ENERGY_MIN) / ENERGY_RANGE, 0.0, 1.0))

    return {
        "score": score,
        "evidence": [
            {
                "detector": "fft",
                "fft_mean_energy": round(mean_energy, 2),
                "ai_likelihood": round(score, 3),
            }
        ],
    }
