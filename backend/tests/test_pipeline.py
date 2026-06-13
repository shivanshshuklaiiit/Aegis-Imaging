"""
Basic pipeline smoke tests. P2 extends this with the 20-image accuracy suite.
Run from the backend/ directory: pytest tests/
"""
import io
import struct
import zlib
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DATABASE_URL", "data/test_aegis.db")
os.environ.setdefault("IRONLABS_API_KEY", "test-key")

from main import app


def _tiny_png() -> bytes:
    """1×1 white PNG — no external file needed."""
    def chunk(name: bytes, data: bytes) -> bytes:
        c = zlib.crc32(name + data).to_bytes(4, "big")
        return struct.pack(">I", len(data)) + name + data + c

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))
    iend = chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


@pytest.fixture
def png_bytes():
    return _tiny_png()


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_verify_returns_verdict(png_bytes):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/verify",
            files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")},
            data={"modality": "xray"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in ("APPROVE", "REJECT", "ESCALATE")
    assert "audit_id" in body
    assert "confidence" in body
    assert "hash_chain" in body


@pytest.mark.asyncio
async def test_verify_bad_extension():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/verify",
            files={"file": ("test.gif", io.BytesIO(b"GIF89a"), "image/gif")},
            data={"modality": "xray"},
        )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_verify_empty_file():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post(
            "/api/v1/verify",
            files={"file": ("test.png", io.BytesIO(b""), "image/png")},
            data={"modality": "xray"},
        )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_audit_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/audit/AEG-DOES-NOT-EXIST")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_dashboard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert "totals" in body
    assert "latency" in body
    assert "cost" in body


@pytest.mark.asyncio
async def test_audit_roundtrip(png_bytes):
    """Verify an image, then fetch its audit record."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        verify_r = await client.post(
            "/api/v1/verify",
            files={"file": ("roundtrip.png", io.BytesIO(png_bytes), "image/png")},
            data={"modality": "mri"},
        )
        assert verify_r.status_code == 200
        audit_id = verify_r.json()["audit_id"]

        audit_r = await client.get(f"/api/v1/audit/{audit_id}")
        assert audit_r.status_code == 200
        assert audit_r.json()["audit_id"] == audit_id
