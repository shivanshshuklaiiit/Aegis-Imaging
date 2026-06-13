from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class Modality(str, Enum):
    xray = "xray"
    mri = "mri"
    ct = "ct"
    ultrasound = "ultrasound"
    other = "other"


class Verdict(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


class Evidence(BaseModel):
    type: str
    region: Optional[list[float]] = None
    score: float
    source_agent: str


class HashChain(BaseModel):
    prev: str
    self: str


class VerifyResponse(BaseModel):
    audit_id: str
    verdict: Verdict
    confidence: float
    rationale: str
    evidence: list[Evidence]
    heatmap_url: Optional[str]
    agent_outputs: dict[str, Any]
    total_latency_ms: int
    total_cost_usd: float
    hash_chain: dict[str, str]


class AuditResponse(VerifyResponse):
    created_at: str
    image_sha256: str
    modality: str


class DashboardTotals(BaseModel):
    verifications_today: int
    approve: int
    reject: int
    escalate: int


class DashboardLatency(BaseModel):
    p50_ms: int
    p95_ms: int


class DashboardCost(BaseModel):
    total_usd: float
    by_model: dict[str, float]
    saved_vs_top_tier_usd: float
    saved_percent: float


class DashboardResponse(BaseModel):
    totals: DashboardTotals
    latency: DashboardLatency
    cost: DashboardCost
    recent_audits: list[dict[str, Any]]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
