# P2 — ML / Detection Engineer PRD

**Role:** Forensics Lead
**Owner:** P2
**Reports to:** P1 for contracts, self for ML decisions

---

## 1. Mission

Own the detection brain of Aegis Imaging. Build the two agents that actually look at the image (Forensics + Clinical), curate the demo test set, and produce the heatmap overlays that will dominate the judges' attention. Your work is the difference between "neat demo" and "we believe this works."

---

## 2. Deliverables

| # | Deliverable | Definition of Done |
|---|---|---|
| D1 | 20-image test set | 10 real + 10 AI-generated, labeled, hash-listed in `data/synthetic_hash_db.json` |
| D2 | 3 hero demo images | Curated for live demo: one obvious real, one obvious fake, one subtle |
| D3 | Forensics Agent | Implements `BaseAgent`; calls HF detectors + FFT + LLM; returns trust score |
| D4 | Clinical Agent | Implements `BaseAgent`; calls vision LLM via IronLabs; returns plausibility score |
| D5 | `hf_detectors.py` | Wrappers for SDXL detector + general AI detector; runs both in parallel |
| D6 | `heatmap.py` | OpenCV overlay function; draws semi-transparent bboxes with labels |
| D7 | DICOM parser | Handles `.dcm` files via pydicom; extracts modality, manufacturer, study date |
| D8 | Accuracy report | Script that runs all 20 test images through pipeline and outputs confusion matrix |
| D9 | Backup verdicts | Pre-computed JSON verdicts for hero images (loaded if `DEMO_MODE=true`) |

---

## 3. Hour-by-Hour Plan

### Sprint 1: Test Set (H0–H4) — DO THIS FIRST

This is your highest priority. Without it, nothing else matters.

- Download 10 real medical images:
  - NIH ChestX-ray14 (5 images, various views) — https://nihcc.app.box.com/v/ChestXray-NIHCC
  - RSNA Pneumonia (2 images)
  - Kaggle Brain MRI (3 images)
- Generate 10 AI medical images:
  - SDXL via HuggingFace Spaces or Replicate ($1 budget)
  - Prompts: "chest X-ray, pneumonia, grayscale, medical imaging", "brain MRI axial slice, T2 weighted", etc.
  - Make 3 of them *subtly* wrong (extra rib, asymmetric lungs, impossible contrast) — these are your "subtle hero" images
- Save all 20 to `demo/test_images/` with naming: `real_NN_<modality>.png`, `fake_NN_<modality>.png`
- Build `data/synthetic_hash_db.json` with perceptual hashes of all 10 fakes (Intake Agent uses this)

### Sprint 2: HF Detectors (H4–H10)

- Get HF token, test inference API access for:
  - `Organika/sdxl-detector`
  - `umm-maybe/AI-image-detector`
  - `dima806/ai_vs_real_image_detection` (fallback)
- Build `hf_detectors.py` with one function: `async def detect_ai(image_bytes) -> dict`
- Run all 3 detectors in parallel via `asyncio.gather`; ensemble = average
- Add FFT analysis using OpenCV: compute frequency spectrum, look for grid patterns characteristic of GANs/diffusion
- Cache results by image SHA-256 to avoid repeated HF calls during testing

### Sprint 3: Forensics Agent (H10–H14)

```python
class ForensicsAgent(BaseAgent):
    name = "forensics"

    async def run(self, context: dict) -> dict:
        image_bytes = open(context["image_path"], "rb").read()

        # Parallel: HF detectors + FFT + LLM
        hf_task = detect_ai(image_bytes)
        fft_task = analyze_fft(image_bytes)
        llm_task = self._llm_forensics(context["image_b64"])
        hf_r, fft_r, llm_r = await asyncio.gather(hf_task, fft_task, llm_task)

        ai_prob = 0.5 * hf_r["ensemble_score"] + 0.2 * fft_r["score"] + 0.3 * llm_r["ai_prob"]
        trust_score = 1.0 - ai_prob

        return {
            "score": trust_score,
            "ai_probability": ai_prob,
            "evidence": [
                *hf_r["evidence"],
                *fft_r["evidence"],
                *llm_r["evidence"],
            ],
            "suspicious_regions": llm_r.get("regions", []),
        }
```

### Sprint 4: Clinical Agent (H14–H18)

Use IronLabs vision LLM to describe the image and assess plausibility. Prompt:

```
You are a board-certified radiologist reviewing an image submitted for verification.

Step 1: Describe what you see (anatomical region, modality, view, key features).
Step 2: Rate clinical plausibility 0.0 to 1.0:
  - Does the anatomy obey normal physiology?
  - Are there impossible features (extra organs, mirrored asymmetry, unnatural densities)?
  - Are labels/markers/text consistent with real imaging equipment?
Step 3: List any impossibilities with approximate bounding boxes [x1, y1, x2, y2] as image-coordinate fractions (0-1).

Output strict JSON:
{
  "description": "...",
  "plausibility": 0.85,
  "impossibilities": [
    {"description": "Fourth rib bifurcates unnaturally", "bbox": [0.4, 0.3, 0.55, 0.45]}
  ]
}
```

### Sprint 5: Heatmap (H18–H22) — THE WOW FACTOR

```python
import cv2
import numpy as np

def overlay_heatmap(image_path: str, regions: list, output_path: str):
    """
    regions: list of {"bbox": [x1,y1,x2,y2] (fractions 0-1),
                       "label": str, "score": float}
    """
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    overlay = img.copy()

    for r in regions:
        x1, y1, x2, y2 = r["bbox"]
        x1, y1, x2, y2 = int(x1*w), int(y1*h), int(x2*w), int(y2*h)
        color = (0, 0, 255)  # BGR red

        # Filled translucent rect
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)

        # Border
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        # Label background + text
        label = f"{r['label']} ({r['score']:.2f})"
        cv2.putText(img, label, (x1, max(y1-8, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Blend
    out = cv2.addWeighted(overlay, 0.3, img, 0.7, 0)
    cv2.imwrite(output_path, out)
```

Test heatmap on all 10 fake images; tweak colors/opacity until it looks crisp at presentation resolution.

### Sprint 6: Accuracy & Tuning (H22–H28)

- Write `tests/test_pipeline.py` that runs all 20 images through `/verify`
- Output confusion matrix, accuracy, precision, recall
- Iterate with P1 on Verdict weights and thresholds until ≥85% accuracy
- If accuracy <85%, add more weight to whichever signal is most discriminative on your test set

### Sprint 7: Demo Insurance (H28–H34)

- Pre-record verdicts for the 3 hero images (JSON files in `demo/cached_verdicts/`)
- Set up `DEMO_MODE=true` path in P1's code to serve these as fallback
- Be present at all dry-runs

### Sprint 8: On Standby (H34–H36)

- During demo: watch backend logs, ready to flip to demo mode if HF API hangs

---

## 4. Code Skeletons

### 4.1 `hf_detectors.py`

```python
import os, httpx, asyncio, hashlib, json
from pathlib import Path

HF_TOKEN = os.getenv("HF_TOKEN")
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
CACHE_DIR = Path("data/hf_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DETECTORS = [
    "Organika/sdxl-detector",
    "umm-maybe/AI-image-detector",
]

async def _call_one(client, model, image_bytes):
    url = f"https://api-inference.huggingface.co/models/{model}"
    try:
        r = await client.post(url, headers=HF_HEADERS, content=image_bytes, timeout=15)
        r.raise_for_status()
        return {"model": model, "result": r.json()}
    except Exception as e:
        return {"model": model, "error": str(e)}

async def detect_ai(image_bytes: bytes) -> dict:
    sha = hashlib.sha256(image_bytes).hexdigest()
    cache_path = CACHE_DIR / f"{sha}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[_call_one(client, m, image_bytes) for m in DETECTORS])

    scores = []
    evidence = []
    for r in results:
        if "error" in r:
            evidence.append({"detector": r["model"], "error": r["error"]})
            continue
        # HF detectors typically return [{"label": "fake", "score": 0.92}, ...]
        for item in r["result"]:
            if "fake" in item["label"].lower() or "ai" in item["label"].lower():
                scores.append(item["score"])
                evidence.append({
                    "detector": r["model"],
                    "label": item["label"],
                    "score": item["score"],
                })

    ensemble_score = sum(scores) / len(scores) if scores else 0.5
    out = {"ensemble_score": ensemble_score, "evidence": evidence}
    cache_path.write_text(json.dumps(out))
    return out
```

### 4.2 `fft_analysis.py`

```python
import cv2, numpy as np

def analyze_fft(image_bytes: bytes) -> dict:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {"score": 0.5, "evidence": [{"fft": "decode_failed"}]}

    f = np.fft.fft2(img)
    fshift = np.fft.fftshift(f)
    mag = 20 * np.log(np.abs(fshift) + 1)

    # Detect periodic high-frequency artifacts (proxy for AI generation)
    high_freq_energy = mag[mag.shape[0]//4 : 3*mag.shape[0]//4,
                            mag.shape[1]//4 : 3*mag.shape[1]//4]
    mean_energy = float(np.mean(high_freq_energy))
    # Empirical threshold; tune on test set
    score = min(1.0, max(0.0, (mean_energy - 80) / 40))

    return {
        "score": score,
        "evidence": [{"fft_mean_energy": mean_energy, "ai_likelihood": score}],
    }
```

---

## 5. Test Set Curation Checklist

Use this checklist when assembling the 20-image set:

- [ ] All 10 real images come from publicly licensed datasets
- [ ] All 10 fake images generated by you (document the prompts in `demo/test_images/generation_log.md`)
- [ ] Images range across 3 modalities (X-ray, MRI, CT)
- [ ] At least 3 fakes are "subtle" (no obvious tells)
- [ ] At least 2 reals have unusual features (old scans, annotations) to test for false positives
- [ ] All images resized to ~1024×1024 max
- [ ] All saved as PNG (lossless)
- [ ] No PHI in filenames or metadata
- [ ] License/attribution noted in `data/ATTRIBUTION.md`

---

## 6. Success Criteria

By H28 you must have:
- ✅ 20-image test set complete with labels
- ✅ Pipeline accuracy ≥85% on test set
- ✅ Heatmap renders cleanly on all 10 fakes
- ✅ Forensics + Clinical agents return in <2s combined (with HF cache warm)
- ✅ 3 hero demo images pre-tested and locked

---

## 7. Things That Will Bite You

1. **HuggingFace inference cold starts are 20–30s.** Pre-warm at startup or rely on cache.
2. **HF returns different schemas per model.** Print and inspect the first response; don't trust docs.
3. **DICOM has 100+ tag variations.** Don't try to be comprehensive; extract 5–6 key tags and call it done.
4. **Vision LLM bbox coordinates drift.** Always ask for fractions (0-1), not pixels — survives image resizing.
5. **SDXL generation costs money.** Use HuggingFace Spaces (free tier) for the 10 fakes.
6. **OpenCV reads BGR, not RGB.** When debugging colors look wrong, this is why.

---

## 8. Daily Checkpoints

- **H4:** Test set locked → commit and tag `test-set-v1`
- **H10:** HF detectors return real scores
- **H18:** Both agents integrated with P1's orchestrator
- **H22:** Heatmaps look demo-ready
- **H28:** Accuracy report committed; thresholds tuned
- **H34:** Hero images verified to demo correctly
