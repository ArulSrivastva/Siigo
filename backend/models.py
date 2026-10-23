"""
Core Database Configuration & Models
SQLAlchemy ORM models defining the exact Phase 1 schema:
- Evidence: append-only, content-hashed, visibility-scoped, trust-tiered
- Claims: stateful ledger with calibrated confidence and modality
- ClaimEvidence: span-level citations linking claim to exact quote
- Edges: directed dependency and approval relationships
- Charter: absence trigger policy & designated trustees
- DelegationGrants: pre-authorized standing authority limits
- AbsenceEvents: active absence declarations with auto-expiry
- ActionRequests: typed intent requests guarded by policy and idempotency
- AuditLog: tamper-evident hash-chained event log
"""
import uuid
import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean,
    DateTime, ForeignKey, Text, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from tests.gold_dataset.schema import TrustTier, ClaimKind, Modality, CalibratedConfidence

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, nullable=False, default="default_tenant")
    source_type = Column(String, nullable=False) # whatsapp | email | voice_note | interview | manual
    author_person_id = Column(String, nullable=True)
    author_external_id = Column(String, nullable=True)
    author_name = Column(String, nullable=False)
    trust_tier = Column(Integer, nullable=False, default=TrustTier.EXTERNAL.value)
    occurred_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    ingested_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    content_sha256 = Column(String(64), nullable=False)
    storage_uri = Column(String, nullable=True)
    raw_content = Column(Text, nullable=False)
    visibility = Column(String, nullable=False, default="private") # private | team | org
    consent_id = Column(String, nullable=True)

    citations = relationship("ClaimEvidence", back_populates="evidence")

class Claim(Base):
    __tablename__ = "claims"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, nullable=False, default="default_tenant")
    kind = Column(String, nullable=False) # commitment | decision | responsibility | approval_rule | knowledge_gap
    subject = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)
    modality = Column(String, nullable=False, default=Modality.PROPOSED.value)
    state = Column(String, nullable=False, default="proposed") # proposed | confirmed | fulfilled | superseded | rejected | stale
    owner_person_id = Column(String, nullable=True)
    counterparty_id = Column(String, nullable=True)
    due_at = Column(DateTime, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    superseded_by = Column(String, ForeignKey("claims.id"), nullable=True)
    calibrated_conf = Column(String, nullable=False, default=CalibratedConfidence.MEDIUM.value)
    origin = Column(String, nullable=False, default="model") # human | model | rule
    extractor_version = Column(String, nullable=False, default="bedrock-claude-v1")
    last_confirmed_by = Column(String, nullable=True)
    last_confirmed_at = Column(DateTime, nullable=True)
    stale_after = Column(DateTime, nullable=True)

    evidence_citations = relationship("ClaimEvidence", back_populates="claim")

class ClaimEvidence(Base):
    __tablename__ = "claim_evidence"

    id = Column(String, primary_key=True, default=generate_uuid)
    claim_id = Column(String, ForeignKey("claims.id"), nullable=False)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=False)
    span_start = Column(Integer, nullable=False)
    span_end = Column(Integer, nullable=False)
    exact_quote = Column(Text, nullable=False)
    quote_sha256 = Column(String(64), nullable=False)
    role = Column(String, nullable=False, default="supports") # supports | contradicts | supersedes | fulfills

    claim = relationship("Claim", back_populates="evidence_citations")
    evidence = relationship("Evidence", back_populates="citations")

class Edge(Base):
    __tablename__ = "edges"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, nullable=False, default="default_tenant")
    from_claim_id = Column(String, ForeignKey("claims.id"), nullable=False)
    to_claim_id = Column(String, ForeignKey("claims.id"), nullable=False)
    kind = Column(String, nullable=False) # blocks | requires_approval_from | same_as
    status = Column(String, nullable=False, default="declared") # declared | inferred | confirmed | rejected
    confirmed_by = Column(String, nullable=True)

class Charter(Base):
    __tablename__ = "charter"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, nullable=False, default="default_tenant")
    person_id = Column(String, nullable=False) # e.g. Maya (Owner)
    trigger_policy = Column(JSON, nullable=False) # {"type": "quorum", "trustees": ["Velu", "Rajesh"], "min": 2, "delay_hours": 4}
    signed_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

class DelegationGrant(Base):
    __tablename__ = "delegation_grants"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, nullable=False, default="default_tenant")
    grantor = Column(String, nullable=False) # owner person ID
    grantee = Column(String, nullable=False) # delegate person ID (e.g. Rajesh)
    scope = Column(JSON, nullable=True) # {"account": "HDFC current", "max_amount_inr": 25000.0}
    allowed_actions = Column(JSON, nullable=False) # ["approve_vendor_payment", "dispatch_shipment"]
    activation = Column(String, nullable=False, default="on_handoff") # always | on_handoff
    not_before = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    granted_via = Column(String, nullable=False, default="normal") # normal | break_glass
    revoked_at = Column(DateTime, nullable=True)

class AbsenceEvent(Base):
    __tablename__ = "absence_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, nullable=False, default="default_tenant")
    person_id = Column(String, nullable=False)
    declared_by = Column(JSON, nullable=False) # list of user IDs who initiated trigger
    method = Column(String, nullable=False) # owner_declared | trustee_quorum | missed_checkin
    status = Column(String, nullable=False, default="active") # pending_delay | active | expired | cancelled
    started_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    auto_expires_at = Column(DateTime, nullable=False)
    cancelled_by_owner = Column(Boolean, nullable=False, default=False)

class ActionRequest(Base):
    __tablename__ = "action_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, nullable=False, default="default_tenant")
    action_type = Column(String, nullable=False) # e.g. approve_payment
    params = Column(JSON, nullable=False)
    requested_by = Column(String, nullable=False)
    on_behalf_of = Column(String, nullable=True)
    policy_decision = Column(String, nullable=False) # ALLOW | DENY
    approver_id = Column(String, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False, default="pending") # pending | executed | blocked | rejected
    executed_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_log"

    seq = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String, nullable=False, default="default_tenant")
    actor = Column(String, nullable=False)
    event = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    prev_hash = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
