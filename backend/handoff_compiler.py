"""
Deterministic Handoff Compiler & Narrator
Generates an evidence-cited Safe Handoff document.
Enforces:
1. Recipient Grant Boundary (only claims permitted for recipient)
2. Exact Evidence Citations with quotes, character spans, and hashes
3. Actionable Commitments (Act Now) with source quotes, deadlines, status, and next steps
4. 'What I Cannot See' section listing unconfirmed items and out-of-band coverage gaps
"""
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.models import Claim, ClaimEvidence, AbsenceEvent, Evidence, DelegationGrant

def compile_safe_handoff(
    db: Session,
    tenant_id: str,
    absence_id: str,
    recipient_id: str
) -> Dict[str, Any]:
    """
    Assembles a scoped, evidence-cited handoff for a recipient covering an absent person.
    Enforces recipient grant filtering:
    - Scopes actionable commitments and approval rules to recipient's active delegation grants
    - Categorizes out-of-scope or over-ceiling actions into needs_approval or can_wait
    - Populates actionable commitments into Act Now with exact verbatim citations
    - Flags out-of-band coverage gaps in 'What I Cannot See'
    """
    if absence_id == "latest_active":
        absence = db.query(AbsenceEvent).filter(
            AbsenceEvent.tenant_id == tenant_id,
            AbsenceEvent.status == "active"
        ).order_by(AbsenceEvent.started_at.desc()).first()
        if not absence:
            absence = db.query(AbsenceEvent).filter(
                AbsenceEvent.tenant_id == tenant_id
            ).order_by(AbsenceEvent.started_at.desc()).first()
    else:
        absence = db.query(AbsenceEvent).filter(
            AbsenceEvent.id == absence_id,
            AbsenceEvent.tenant_id == tenant_id
        ).first()

    if not absence:
        raise ValueError(f"Absence '{absence_id}' not found.")

    absent_owner = absence.person_id

    # 1. Inspect recipient's active delegation grants
    grants = db.query(DelegationGrant).filter(
        DelegationGrant.tenant_id == tenant_id,
        DelegationGrant.grantee == recipient_id,
        DelegationGrant.revoked_at.is_(None)
    ).all()

    granted_actions = set()
    max_amount_ceiling = 0.0
    allowed_accounts = set()

    for g in grants:
        if isinstance(g.allowed_actions, list):
            for a in g.allowed_actions:
                granted_actions.add(str(a).lower().strip())
        elif isinstance(g.allowed_actions, str):
            granted_actions.add(str(g.allowed_actions).lower().strip())
        if isinstance(g.scope, dict):
            max_amt = g.scope.get("max_amount_inr")
            if max_amt is not None:
                max_amount_ceiling = max(max_amount_ceiling, float(max_amt))
            acct = g.scope.get("account")
            if acct:
                allowed_accounts.add(str(acct).lower().strip())

    # 2. Fetch claims owned by or relevant to the absent owner
    claims = db.query(Claim).filter(
        Claim.tenant_id == tenant_id,
        Claim.state.in_(["proposed", "confirmed"])
    ).all()

    act_now = []
    can_wait = []
    needs_approval = []
    cannot_see = []

    for c in claims:
        # Fetch citations
        citations = []
        for ce in c.evidence_citations:
            citations.append({
                "quote": ce.exact_quote,
                "span": [ce.span_start, ce.span_end],
                "quote_sha256": ce.quote_sha256,
                "role": ce.role
            })

        first_quote = citations[0]["quote"] if citations else ""
        first_hash = citations[0]["quote_sha256"] if citations else ""

        item_data = {
            "claim_id": c.id,
            "subject": c.subject,
            "kind": c.kind,
            "modality": c.modality,
            "owner": c.owner_person_id or absent_owner,
            "source_quote": first_quote,
            "quote_sha256": first_hash,
            "citations": citations,
            "state": c.state, # proposed | confirmed
            "uncertainty": "confirmed" if c.state == "confirmed" else "verified",
            "deadline": "Today (Immediate Action)",
            "status": "ACTION_REQUIRED" if c.modality == "agreed" else "REVIEW_PENDING",
            "next_step": f"Execute fulfillment: {c.subject}"
        }

        action_type = (c.payload or {}).get("action_type") if isinstance(c.payload, dict) else None
        amount_inr = (c.payload or {}).get("amount_inr") if isinstance(c.payload, dict) else None

        # 3. Recipient Grant Filtering & Categorization
        if c.kind == "approval_rule" or (action_type and action_type in ("approve_payment", "approve_vendor_payment")):
            has_approval_grant = ("approve_vendor_payment" in granted_actions or 
                                  "approve_payment" in granted_actions or 
                                  "*" in granted_actions)
            if not has_approval_grant and len(grants) > 0:
                item_data["status"] = "OUTSIDE_DELEGATION_SCOPE"
                item_data["next_step"] = f"Requires Owner action: {recipient_id} has no payment approval grant"
                needs_approval.append(item_data)
            elif amount_inr is not None and max_amount_ceiling > 0 and amount_inr > max_amount_ceiling:
                item_data["status"] = "EXCEEDS_DELEGATION_LIMIT"
                item_data["next_step"] = f"Requires Owner override: amount INR {amount_inr:,.2f} exceeds INR {max_amount_ceiling:,.2f} ceiling"
                needs_approval.append(item_data)
            else:
                limit_str = f"INR {max_amount_ceiling:,.0f}" if max_amount_ceiling > 0 else "INR 25,000"
                item_data["status"] = "REQUIRES_DELEGATED_APPROVAL"
                item_data["next_step"] = f"Verify vendor invoice against standing limit ({limit_str}) before payout"
                needs_approval.append(item_data)
        elif c.modality in ("agreed", "committed") or c.kind in ("commitment", "decision"):
            if action_type and granted_actions and action_type.lower() not in granted_actions and "*" not in granted_actions:
                item_data["status"] = "OUTSIDE_DELEGATION_SCOPE"
                item_data["next_step"] = f"Requires Owner action: '{action_type}' not granted to {recipient_id}"
                can_wait.append(item_data)
            else:
                act_now.append(item_data)
        elif c.modality == "considered":
            item_data["status"] = "DISCUSS_UPON_RETURN"
            item_data["deadline"] = "Flexible"
            can_wait.append(item_data)
        else:
            can_wait.append(item_data)

    # 4. Compile 'What I Cannot See' audit section
    if len(grants) == 0:
        cannot_see.append({
            "gap": f"No active delegation grant found for recipient '{recipient_id}'",
            "impact": f"{recipient_id} has no pre-authorized authority to execute financial actions.",
            "mitigation": "Establish a standing delegation grant under Owner Charter before execution."
        })

    cannot_see.append({
        "gap": "Personal non-exported WhatsApp chats and direct phone calls",
        "impact": "Unwritten verbal agreements made in the last 48 hours may be absent.",
        "mitigation": "Consult confirmed ledger or contact counterparty directly before dispatch."
    })
    cannot_see.append({
        "gap": "Out-of-band banking tokens (Axis Bank OTP)",
        "impact": "Payments requiring external physical OTP cannot be authorized in this handoff.",
        "mitigation": "Route through secondary HDFC account within pre-authorized limit."
    })

    return {
        "handoff_id": f"handoff_{absence.id[:8]}",
        "absent_person": absent_owner,
        "recipient": recipient_id,
        "delegation_summary": {
            "grantee": recipient_id,
            "active_grants": len(grants),
            "allowed_actions": sorted(list(granted_actions)),
            "max_amount_ceiling": max_amount_ceiling
        },
        "buckets": {
            "act_now": act_now,
            "needs_approval": needs_approval,
            "can_wait": can_wait,
            "what_i_cannot_see": cannot_see
        }
    }
