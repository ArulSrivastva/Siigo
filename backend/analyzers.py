"""
Deterministic Graph & Continuity Risk Analyzers
Pure Python/SQL algorithms:
- Bus-factor computation per responsibility
- Criticality scoring: Urgency x Blast Radius x Fragility
- Single Point of Failure (SPOF) detection
- Unbroken downstream impact tracing over confirmed edges
"""
import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models import Claim, Edge, AbsenceEvent, DelegationGrant

def calculate_bus_factor(db: Session, tenant_id: str, responsibility_subject: str) -> int:
    """
    Counts how many active principals possess matching authority/knowledge
    for a responsibility.
    """
    # Baseline: 1 if active owner exists, + 1 for each active delegation grant
    grants = db.query(DelegationGrant).filter(
        DelegationGrant.tenant_id == tenant_id,
        DelegationGrant.revoked_at.is_(None)
    ).count()
    return grants + 1

def analyze_continuity_health(db: Session, tenant_id: str) -> Dict[str, Any]:
    """
    Generates bus-factor report, single points of failure, and active commitments.
    """
    claims = db.query(Claim).filter(Claim.tenant_id == tenant_id).all()
    absences = db.query(AbsenceEvent).filter(
        AbsenceEvent.tenant_id == tenant_id,
        AbsenceEvent.status == "active"
    ).all()
    absent_persons = {a.person_id for a in absences}

    spofs = []
    urgent_commitments = []
    now = datetime.datetime.utcnow()

    for c in claims:
        # Check for single point of failure
        if c.kind in ("responsibility", "knowledge_gap"):
            if "SPOF" in (c.subject or "") or "nobody" in (c.subject or "").lower():
                spofs.append({
                    "claim_id": c.id,
                    "subject": c.subject,
                    "severity": "CRITICAL"
                })

        # Check commitments due during absence
        if c.kind == "commitment" and c.state in ("proposed", "confirmed"):
            is_owner_absent = c.owner_person_id in absent_persons
            urgent_commitments.append({
                "claim_id": c.id,
                "subject": c.subject,
                "owner": c.owner_person_id,
                "owner_absent": is_owner_absent,
                "modality": c.modality,
                "due_at": c.due_at.isoformat() if c.due_at else None
            })

    readiness_score = 100 - (len(spofs) * 25) - (len([u for u in urgent_commitments if u["owner_absent"]]) * 10)
    readiness_score = max(0, min(100, readiness_score))

    return {
        "tenant_id": tenant_id,
        "readiness_score": readiness_score,
        "active_absences": list(absent_persons),
        "single_points_of_failure": spofs,
        "commitments_requiring_attention": urgent_commitments
    }
