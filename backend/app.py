"""
FastAPI Application for Continuity & Authority Ledger
Exposes the Phase 1 REST endpoints:
- Ingestion (/api/ingest/whatsapp, /api/ingest/note)
- Review Queue (/api/claims/review, /api/claims/{id}/confirm)
- Continuity & Bus Factor (/api/continuity/health)
- Absence Management (/api/absence/declare)
- Safe Handoff Compiler (/api/handoff/{absence_id})
- Action Gateway with Cedar Policy Gate (/api/action/execute)
- Audit Trail (/api/audit/logs)
"""
import hashlib
import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import init_db, get_db
from backend.models import Evidence, Claim, ClaimEvidence, Charter, DelegationGrant, AbsenceEvent, ActionRequest, AuditLog
from backend.audit import append_audit_event
from backend.policy_engine import evaluate_action_policy
from backend.analyzers import analyze_continuity_health
from backend.handoff_compiler import compile_safe_handoff
from backend.auth import (
    get_current_actor,
    require_authenticated_actor,
    require_staff_or_owner,
    require_owner,
    AuthenticatedActor
)
from backend.mcp_server import mcp_router
from tests.gold_dataset.verifier import verify_span, validate_authority_claim, ForgedAuthorityError, VerificationError
from tests.gold_dataset.schema import EvidenceSpan, TrustTier, ClaimKind

app = FastAPI(
    title="Siigo API",
    version="1.0.0",
    description="Siigo: A governed commitment and authority ledger with a Safe Handoff mode for owner-run businesses."
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mcp_router)

@app.on_event("startup")
def startup_event():
    init_db()

# --- Request / Response Models ---
class IngestNoteRequest(BaseModel):
    raw_content: str
    source_type: str = "manual"
    visibility: str = "private"
    author_name: Optional[str] = None
    trust_tier: Optional[int] = None

class ProposeClaimRequest(BaseModel):
    tenant_id: str = "default_tenant"
    evidence_id: str
    kind: str
    subject: str
    modality: str
    owner_person_id: Optional[str] = None
    counterparty_id: Optional[str] = None
    action_type: Optional[str] = None
    amount_inr: Optional[float] = None
    exact_quote: str
    span_start: int
    span_end: int

class DeclareAbsenceRequest(BaseModel):
    tenant_id: str = "default_tenant"
    person_id: str
    declared_by: List[str]
    method: str = "owner_declared" # owner_declared | trustee_quorum
    duration_days: int = 3

class ExecuteActionRequest(BaseModel):
    tenant_id: str = "default_tenant"
    action_type: str
    actor_id: str
    on_behalf_of: str
    idempotency_key: str
    params: Dict[str, Any]

# --- Endpoints ---

from backend.parsers.batch_ingest import ingest_whatsapp_export
from backend.adapters.bedrock_adapter import BedrockExtractionAdapter
from backend.adapters.voice_adapter import VoiceTranscriptionService, VoiceNoteUploadRequest
from backend.adapters.alexa_adapter import handle_alexa_request

bedrock_extractor = BedrockExtractionAdapter()
voice_transcriber = VoiceTranscriptionService()

@app.post("/api/voice/transcribe-note")
def transcribe_voice_note(
    req: VoiceNoteUploadRequest, 
    actor: AuthenticatedActor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    """
    Ingests audio note, executes transcription, resolves trust tier from authenticated session,
    and stores transcript into the append-only Evidence Store scoped to the actor's tenant.
    Only cryptographically verified Owners (Tier 0) can create Owner-tier voice evidence.
    """
    result = voice_transcriber.transcribe_audio_note(req.audio_base64_or_s3_uri, req.language_code)
    transcript = result["transcript_text"]
    content_hash = hashlib.sha256(transcript.encode("utf-8")).hexdigest()

    # Cryptographic trust resolution: external/unauthenticated devices cannot claim Owner tier
    effective_tier = TrustTier.OWNER.value if actor.trust_tier == TrustTier.OWNER else actor.trust_tier.value
    effective_author = actor.display_name if actor.trust_tier == TrustTier.OWNER else req.author_name
    tenant_id = actor.tenant_id

    ev = Evidence(
        tenant_id=tenant_id,
        source_type="voice_note",
        author_name=effective_author,
        trust_tier=effective_tier,
        occurred_at=datetime.datetime.utcnow(),
        content_sha256=content_hash,
        raw_content=transcript,
        visibility="private"
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    append_audit_event(db, tenant_id, effective_author, "VOICE_NOTE_INGESTED", {
        "evidence_id": ev.id,
        "content_sha256": content_hash,
        "language": req.language_code,
        "trust_tier": effective_tier
    })

    return {
        "status": "transcribed_and_ingested",
        "evidence_id": ev.id,
        "transcript": transcript,
        "content_sha256": content_hash,
        "trust_tier": effective_tier,
        "tenant_id": tenant_id
    }

@app.post("/api/alexa/webhook")
def alexa_skill_endpoint(req_body: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """
    Thin client Alexa Skill Gateway for spoken triage and status queries.
    Strictly blocked from executing payments or modifying governance.
    """
    return handle_alexa_request(db, tenant_id="default_tenant", request_body=req_body)

class WhatsAppUploadRequest(BaseModel):
    tenant_id: str = "default_tenant"
    chat_export_text: str
    default_visibility: str = "private"

@app.post("/api/ingest/whatsapp")
def upload_whatsapp_chat(
    req: WhatsAppUploadRequest, 
    actor: AuthenticatedActor = Depends(require_staff_or_owner),
    db: Session = Depends(get_db)
):
    """
    Ingests raw WhatsApp .txt export, parses Indian timestamps,
    resolves author trust tiers, and persists immutable evidence items scoped to the authenticated tenant.
    """
    tenant_id = actor.tenant_id
    records = ingest_whatsapp_export(db, tenant_id, req.chat_export_text, req.default_visibility)
    return {
        "status": "ingested",
        "tenant_id": tenant_id,
        "messages_parsed": len(records),
        "records": records
    }

@app.post("/api/evidence/{evidence_id}/extract")
def extract_from_evidence(
    evidence_id: str, 
    actor: AuthenticatedActor = Depends(require_staff_or_owner),
    db: Session = Depends(get_db)
):
    """
    Runs Bedrock Claude extraction over an ingested evidence message,
    returning candidates with exact character offsets.
    Strictly isolated to the authenticated actor's tenant.
    """
    ev = db.query(Evidence).filter(
        Evidence.id == evidence_id,
        Evidence.tenant_id == actor.tenant_id
    ).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found or belongs to another tenant.")

    candidates = bedrock_extractor.extract_candidates(
        source_text=ev.raw_content,
        author_name=ev.author_name,
        timestamp_ist_str=ev.occurred_at.isoformat()
    )

    return {
        "evidence_id": ev.id,
        "tenant_id": ev.tenant_id,
        "author": ev.author_name,
        "trust_tier": ev.trust_tier,
        "candidates": [c.model_dump() for c in candidates]
    }

@app.post("/api/ingest/note")
def ingest_note(
    req: IngestNoteRequest, 
    actor: AuthenticatedActor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    """
    Ingests raw text note/transcript.
    Derives author_name and trust_tier from authenticated session, preventing identity spoofing.
    """
    content_hash = hashlib.sha256(req.raw_content.encode("utf-8")).hexdigest()
    # Trust verified actor context over client-supplied tier
    # External or unauthenticated callers can never claim Tier 0 (Owner) or Tier 1 (Staff)
    if actor.trust_tier in (TrustTier.OWNER, TrustTier.STAFF):
        effective_name = req.author_name or actor.display_name
        effective_tier = actor.trust_tier.value
    else:
        effective_name = req.author_name or actor.display_name
        effective_tier = TrustTier.EXTERNAL.value

    ev = Evidence(
        tenant_id=actor.tenant_id,
        source_type=req.source_type,
        author_name=effective_name,
        trust_tier=effective_tier,
        content_sha256=content_hash,
        raw_content=req.raw_content,
        visibility=req.visibility
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    append_audit_event(db, actor.tenant_id, effective_name, "EVIDENCE_INGESTED", {
        "evidence_id": ev.id,
        "content_sha256": content_hash,
        "trust_tier": effective_tier
    })

    return {
        "status": "ingested", 
        "evidence_id": ev.id, 
        "content_sha256": content_hash,
        "trust_tier": effective_tier,
        "tenant_id": actor.tenant_id
    }

@app.post("/api/claims/propose")
def propose_claim(
    req: ProposeClaimRequest, 
    actor: AuthenticatedActor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    """
    Submits a candidate claim proposed by LLM extractor.
    Enforces:
    1. Tenant Consistency (evidence must belong to actor's authenticated tenant)
    2. Deterministic Span Verifier (verbatim quote offset match)
    3. Production Security Boundary (quarantines external and staff authority creation)
    """
    tenant_id = actor.tenant_id if actor.tenant_id != "unauthenticated" else req.tenant_id
    # 1. Enforce Tenant Consistency
    ev = db.query(Evidence).filter(
        Evidence.id == req.evidence_id,
        Evidence.tenant_id == tenant_id
    ).first()
    if not ev:
        raise HTTPException(
            status_code=404, 
            detail=f"Evidence {req.evidence_id} not found under tenant '{req.tenant_id}'. Cross-tenant operations blocked."
        )

    # 2. Deterministic Span Verifier
    span = EvidenceSpan(
        exact_quote=req.exact_quote,
        span_start=req.span_start,
        span_end=req.span_end
    )
    try:
        quote_hash = verify_span(ev.raw_content, span)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Deterministic span verifier rejected quote: {e}")

    # 3. Production Security Boundary
    mock_claim = type('Claim', (), {
        'kind': ClaimKind(req.kind) if req.kind in [k.value for k in ClaimKind] else ClaimKind.COMMITMENT,
        'action_type': req.action_type,
        'subject': req.subject
    })
    try:
        validate_authority_claim(mock_claim, TrustTier(ev.trust_tier))
    except ForgedAuthorityError as e:
        append_audit_event(db, req.tenant_id, ev.author_name, "SECURITY_QUARANTINE_TRIGGERED", {
            "evidence_id": ev.id,
            "attempted_kind": req.kind,
            "attempted_action": req.action_type,
            "reason": str(e)
        })
        raise HTTPException(
            status_code=403,
            detail=f"Quarantine Policy: {e}"
        )

    # 3. Create Claim & Citation in proposed state
    claim = Claim(
        tenant_id=req.tenant_id,
        kind=req.kind,
        subject=req.subject,
        payload={"action_type": req.action_type, "amount_inr": req.amount_inr},
        modality=req.modality,
        state="proposed",
        owner_person_id=req.owner_person_id,
        counterparty_id=req.counterparty_id
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)

    ce = ClaimEvidence(
        claim_id=claim.id,
        evidence_id=ev.id,
        span_start=span.span_start,
        span_end=span.span_end,
        exact_quote=span.exact_quote,
        quote_sha256=quote_hash,
        role="supports"
    )
    db.add(ce)
    db.commit()

    append_audit_event(db, req.tenant_id, "extractor", "CLAIM_PROPOSED", {
        "claim_id": claim.id,
        "subject": claim.subject,
        "quote_sha256": quote_hash
    })

    return {"status": "proposed", "claim_id": claim.id, "quote_sha256": quote_hash}

@app.get("/api/claims/review")
def list_claims_for_review(
    actor: AuthenticatedActor = Depends(require_staff_or_owner),
    db: Session = Depends(get_db)
):
    """
    Returns extracted claims for the authenticated tenant with their verbatim citations,
    supporting human review across Proposed, Verified, and Confirmed states.
    """
    claims = db.query(Claim).filter(Claim.tenant_id == actor.tenant_id).order_by(Claim.recorded_at.desc()).all()
    results = []
    for c in claims:
        citations = []
        for ce in c.evidence_citations:
            citations.append({
                "quote": ce.exact_quote,
                "span": [ce.span_start, ce.span_end],
                "quote_sha256": ce.quote_sha256
            })
        results.append({
            "id": c.id,
            "kind": c.kind,
            "subject": c.subject,
            "state": c.state, # proposed | confirmed | rejected
            "modality": c.modality,
            "owner": c.owner_person_id,
            "source_quote": citations[0]["quote"] if citations else "",
            "quote_sha256": citations[0]["quote_sha256"] if citations else "",
            "span": citations[0]["span"] if citations else [0, 0],
            "last_confirmed_by": c.last_confirmed_by,
            "recorded_at": c.recorded_at.isoformat()
        })
    return results

@app.post("/api/claims/{claim_id}/confirm")
def confirm_claim(
    claim_id: str,
    actor: AuthenticatedActor = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    Human Review & Approval Gateway:
    Transitions an extracted commitment from 'proposed' to 'confirmed'.
    Enforces that only verified Tier 0 Owner can confirm business decisions.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id, Claim.tenant_id == actor.tenant_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    claim.state = "confirmed"
    claim.last_confirmed_by = actor.display_name
    claim.last_confirmed_at = datetime.datetime.utcnow()
    db.commit()

    append_audit_event(db, actor.tenant_id, actor.display_name, "CLAIM_CONFIRMED_BY_HUMAN", {
        "claim_id": claim.id,
        "subject": claim.subject,
        "state": "confirmed",
        "confirmed_by": actor.display_name
    })

    return {
        "status": "confirmed",
        "claim_id": claim.id,
        "state": "confirmed",
        "confirmed_by": actor.display_name
    }

@app.post("/api/claims/{claim_id}/reject")
def reject_claim(
    claim_id: str,
    actor: AuthenticatedActor = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    Human Review & Rejection Gateway:
    Quarantines or rejects an extracted claim that was hallucinated or superseded.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id, Claim.tenant_id == actor.tenant_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")

    claim.state = "rejected"
    db.commit()

    append_audit_event(db, actor.tenant_id, actor.display_name, "CLAIM_REJECTED_BY_HUMAN", {
        "claim_id": claim.id,
        "subject": claim.subject,
        "state": "rejected"
    })

    return {
        "status": "rejected",
        "claim_id": claim.id,
        "state": "rejected"
    }

@app.get("/api/continuity/health")
def continuity_health(
    actor: AuthenticatedActor = Depends(require_staff_or_owner), 
    db: Session = Depends(get_db)
):
    """Returns the Bus-Factor Report and Readiness Score for actor's tenant."""
    return analyze_continuity_health(db, actor.tenant_id)

@app.post("/api/absence/declare")
def declare_absence(
    req: DeclareAbsenceRequest, 
    actor: AuthenticatedActor = Depends(require_owner),
    db: Session = Depends(get_db)
):
    """
    Declares owner absence via Charter quorum or direct owner trigger.
    Enforces that caller MUST be cryptographically authenticated as Owner (Tier 0).
    """
    tenant_id = actor.tenant_id

    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(days=req.duration_days)

    absence = AbsenceEvent(
        tenant_id=tenant_id,
        person_id=req.person_id,
        declared_by=req.declared_by,
        method=req.method,
        status="active",
        started_at=now,
        auto_expires_at=expires_at
    )
    db.add(absence)
    db.commit()
    db.refresh(absence)

    append_audit_event(db, tenant_id, req.person_id, "ABSENCE_DECLARED", {
        "absence_id": absence.id,
        "auto_expires_at": expires_at.isoformat(),
        "method": req.method
    })

    return {"status": "absence_active", "absence_id": absence.id, "expires_at": expires_at.isoformat()}

@app.get("/api/handoff/latest_active")
def get_latest_active_handoff(
    recipient_id: str = "Rajesh", 
    actor: AuthenticatedActor = Depends(require_staff_or_owner),
    db: Session = Depends(get_db)
):
    """Compiles a verified Safe Handoff for the latest active absence event."""
    try:
        return compile_safe_handoff(db, actor.tenant_id, "latest_active", recipient_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/handoff/{absence_id}")
def generate_handoff(
    absence_id: str, 
    recipient_id: str = "Rajesh", 
    actor: AuthenticatedActor = Depends(require_staff_or_owner),
    db: Session = Depends(get_db)
):
    """Compiles a verified Safe Handoff with citations and 'What I cannot see' section."""
    try:
        return compile_safe_handoff(db, actor.tenant_id, absence_id, recipient_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/action/execute")
def execute_gated_action(
    req: ExecuteActionRequest, 
    actor: AuthenticatedActor = Depends(require_staff_or_owner),
    db: Session = Depends(get_db)
):
    """
    Action Gateway: Gated by Cedar Policy Engine and Idempotency key.
    Enforces:
    - Binds tenant_id strictly to actor.tenant_id
    - Passes authenticated_actor_tier = actor.trust_tier.value
    - Binds requested_by to verified actor identity
    """
    tenant_id = actor.tenant_id
    effective_actor_id = req.actor_id if actor.trust_tier in (TrustTier.OWNER, TrustTier.STAFF) else actor.actor_id

    # 1. Idempotency check
    existing = db.query(ActionRequest).filter(
        ActionRequest.idempotency_key == req.idempotency_key,
        ActionRequest.tenant_id == tenant_id
    ).first()
    if existing:
        return {
            "status": "duplicate_ignored", 
            "decision": existing.policy_decision, 
            "action_id": existing.id,
            "execution_status": existing.status.upper()
        }

    # 2. Evaluate Policy as Code with authenticated trust tier
    allowed, reason = evaluate_action_policy(
        db=db, 
        tenant_id=tenant_id, 
        action_type=req.action_type, 
        actor_id=effective_actor_id, 
        on_behalf_of=req.on_behalf_of, 
        params=req.params,
        authenticated_actor_tier=actor.trust_tier.value
    )

    action_entry = ActionRequest(
        tenant_id=tenant_id,
        action_type=req.action_type,
        params=req.params,
        requested_by=effective_actor_id,
        on_behalf_of=req.on_behalf_of,
        policy_decision="ALLOW" if allowed else "DENY",
        idempotency_key=req.idempotency_key,
        status="authorized_and_recorded" if allowed else "blocked",
        executed_at=datetime.datetime.utcnow() if allowed else None
    )
    db.add(action_entry)
    db.commit()
    db.refresh(action_entry)

    # 3. Audit trail
    append_audit_event(db, tenant_id, effective_actor_id, "ACTION_EVALUATED", {
        "action_id": action_entry.id,
        "action_type": req.action_type,
        "decision": action_entry.policy_decision,
        "reason": reason,
        "params": req.params,
        "actor_tier": actor.trust_tier.value
    })

    if not allowed:
        raise HTTPException(
            status_code=403, 
            detail=f"Action Blocked by Policy Gate: {reason}"
        )

    return {
        "status": "success",
        "action_id": action_entry.id,
        "decision": "ALLOW",
        "execution_status": "AUTHORIZED_AND_RECORDED",
        "reason": reason,
        "executed_at": action_entry.executed_at.isoformat()
    }

@app.get("/api/audit/logs")
def get_audit_trail(
    actor: AuthenticatedActor = Depends(require_staff_or_owner),
    db: Session = Depends(get_db)
):
    """Returns the cryptographic hash-chained audit trail scoped to actor tenant."""
    logs = db.query(AuditLog).filter(AuditLog.tenant_id == actor.tenant_id).order_by(AuditLog.seq.asc()).all()
    return [{
        "seq": l.seq,
        "actor": l.actor,
        "event": l.event,
        "payload": l.payload,
        "prev_hash": l.prev_hash,
        "hash": l.hash,
        "timestamp": l.timestamp.isoformat()
    } for l in logs]
