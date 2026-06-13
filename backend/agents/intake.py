import json
import asyncio
import logging
from pathlib import Path

from agents.base import BaseAgent

logger = logging.getLogger(__name__)

SYNTHETIC_HASH_DB_PATH = Path("data/synthetic_hash_db.json")

DICOM_TAGS = [
    "Modality", "Manufacturer", "StudyDate", "PatientAge",
    "PixelSpacing", "SliceThickness", "KVP", "ExposureTime",
    "ImageType", "SOPClassUID",
]


class IntakeAgent(BaseAgent):
    name = "intake"

    def __init__(self):
        self._hash_db: dict = {}
        self._hash_db_loaded = False

    def _load_hash_db(self) -> None:
        if self._hash_db_loaded:
            return
        try:
            if SYNTHETIC_HASH_DB_PATH.exists():
                raw = json.loads(SYNTHETIC_HASH_DB_PATH.read_text())
                # Strip comment keys
                self._hash_db = {k: v for k, v in raw.items() if not k.startswith("_")}
        except Exception as e:
            logger.warning(f"Could not load synthetic hash DB: {e}")
        self._hash_db_loaded = True

    async def run(self, context: dict) -> dict:
        image_path = context["image_path"]
        file_bytes = Path(image_path).read_bytes()
        suffix = Path(image_path).suffix.lower()

        loop = asyncio.get_event_loop()

        if suffix == ".dcm":
            metadata = await loop.run_in_executor(None, self._extract_dicom, file_bytes)
        else:
            metadata = await loop.run_in_executor(None, self._extract_exif, file_bytes)

        phash = await loop.run_in_executor(None, self._compute_phash, file_bytes)

        self._load_hash_db()
        in_synthetic_db = phash in self._hash_db

        score = self._compute_score(metadata, in_synthetic_db)

        anomalies = []
        if in_synthetic_db:
            anomalies.append({
                "type": "synthetic_hash_match",
                "detail": "pHash found in known AI-generated image database",
            })
        if not metadata.get("metadata_complete"):
            anomalies.append({
                "type": "incomplete_metadata",
                "detail": f"Only {len(metadata.get('tags', {}))} DICOM/EXIF tags found",
            })

        evidence = [
            {"type": "metadata_integrity", "score": score, "source_agent": "intake"},
            *[{"type": a["type"], "score": 0.0, "source_agent": "intake"} for a in anomalies],
        ]

        return {
            "score": score,
            "metadata": metadata,
            "phash": phash,
            "in_synthetic_db": in_synthetic_db,
            "metadata_complete": metadata.get("metadata_complete", False),
            "anomalies": anomalies,
            "evidence": evidence,
        }

    def _extract_dicom(self, file_bytes: bytes) -> dict:
        try:
            import pydicom
            import io
            ds = pydicom.dcmread(io.BytesIO(file_bytes))
            tags = {}
            for tag_name in DICOM_TAGS:
                try:
                    val = getattr(ds, tag_name, None)
                    if val is not None:
                        tags[tag_name] = str(val)[:200]
                except Exception:
                    pass
            return {
                "source": "dicom",
                "tags": tags,
                "metadata_complete": len(tags) >= 4,
            }
        except Exception as e:
            return {"source": "dicom", "tags": {}, "metadata_complete": False, "error": "metadata_missing"}

    def _extract_exif(self, file_bytes: bytes) -> dict:
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            import io
            img = Image.open(io.BytesIO(file_bytes))
            exif_data = {}
            raw_exif = img._getexif()
            if raw_exif:
                for tag_id, value in raw_exif.items():
                    tag = TAGS.get(tag_id, str(tag_id))
                    try:
                        exif_data[str(tag)] = str(value)[:200]
                    except Exception:
                        pass
            return {
                "source": "exif",
                "format": img.format,
                "size": list(img.size),
                "mode": img.mode,
                "tags": exif_data,
                "metadata_complete": True,
            }
        except Exception as e:
            return {"source": "unknown", "tags": {}, "metadata_complete": False, "error": str(e)}

    def _compute_phash(self, file_bytes: bytes) -> str:
        try:
            import imagehash
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(file_bytes))
            return str(imagehash.phash(img))
        except Exception:
            import hashlib
            return hashlib.sha256(file_bytes[:2048]).hexdigest()[:16]

    def _compute_score(self, metadata: dict, in_synthetic_db: bool) -> float:
        score = 1.0

        if in_synthetic_db:
            score -= 0.7

        if not metadata.get("metadata_complete"):
            score -= 0.15

        if metadata.get("source") == "dicom" and len(metadata.get("tags", {})) >= 6:
            score += 0.05

        return round(max(0.0, min(1.0, score)), 4)
