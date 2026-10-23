"""
Evaluation and Extraction Schema Definitions
Core Pydantic models for Claims, Evidence Spans, Modalities, and Authority Rules.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TrustTier(int, Enum):
    OWNER = 0        # Signed charter owner / verified principal
    STAFF = 1        # Internal employee / known contributor
    EXTERNAL = 2     # Client, vendor, supplier
    UNTRUSTED = 3    # Unknown number, unauthenticated forward, raw web

class ClaimKind(str, Enum):
    COMMITMENT = "commitment"
    DECISION = "decision"
    RESPONSIBILITY = "responsibility"
    APPROVAL_RULE = "approval_rule"
    KNOWLEDGE_GAP = "knowledge_gap"

class Modality(str, Enum):
    CONSIDERED = "considered"   # Speculation / brainstorming
    PROPOSED = "proposed"       # Offer / pending confirmation
    AGREED = "agreed"           # Explicit consensus / binding agreement
    EXECUTED = "executed"       # Action completed
    RETRACTED = "retracted"     # Cancelled / scratched / superseded

class CalibratedConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class EvidenceSpan(BaseModel):
    exact_quote: str = Field(..., description="Exact substring verbatim from source text")
    span_start: int = Field(..., description="0-indexed char offset in source")
    span_end: int = Field(..., description="0-indexed char end offset")

class BenchmarkClaim(BaseModel):
    id: str
    kind: ClaimKind
    modality: Modality
    subject: str
    owner_alias: Optional[str] = None
    counterparty_alias: Optional[str] = None
    due_at_relative_or_iso: Optional[str] = None
    evidence_span: EvidenceSpan
    calibrated_confidence: CalibratedConfidence
    action_type: Optional[str] = None
    amount_inr: Optional[float] = None
    trap_tag: Optional[str] = Field(None, description="e.g. FORGED_AUTHORITY, RETRACTION, RELATIVE_DATE, SARCASM")

class BenchmarkMessage(BaseModel):
    id: str
    source_type: str  # whatsapp | voice_note | email | interview
    author_name: str
    author_trust_tier: TrustTier
    timestamp_ist: str  # e.g. "2026-10-25T14:30:00+05:30"
    raw_text: str
    expected_claims: List[BenchmarkClaim] = []
    quarantine_expected: bool = False
    notes: Optional[str] = None
