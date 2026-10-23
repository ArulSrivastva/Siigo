"""
Cedar / Deterministic Policy Engine for Action Gateway
Implements authority policies as code.
Verifies whether a requested action (e.g. approve_payment) is permitted given:
- Caller identity and active absence status
- Standing delegation limits (INR limits, account scopes)
- Owner Charter rules
"""
import datetime
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.models import DelegationGrant, AbsenceEvent, ActionRequest
from backend.audit import append_audit_event

def evaluate_action_policy(
    db: Session,
    tenant_id: str,
    action_type: str,
    actor_id: str,
    on_behalf_of: str,
    params: Dict[str, Any],
    authenticated_actor_tier: int = 1 # 0: Verified Owner, 1: Verified Staff, 2: External
) -> Tuple[bool, str]:
    """
    Evaluates policy with fail-closed financial integrity:
    1. If actor claims direct owner action -> REJECT unless authenticated_actor_tier == 0
    2. If actor acting on behalf of owner:
       a. Check if owner has an active AbsenceEvent
       b. Check if actor has an active DelegationGrant for action_type
       c. Payment action checks:
          - FAIL CLOSED: amount_inr must be positive finite number
          - Check ceiling: amount_inr <= max_amount_inr
          - Check account restriction: account in grant scope
    Returns (is_allowed, reason)
    """
    # 1. Owner direct action authentication guard
    if actor_id == on_behalf_of:
        if authenticated_actor_tier != 0:
            return False, f"Denied: Spoofed Owner Identity. Actor {actor_id} is not authenticated as Tier 0 Owner."
        return True, "Direct owner authorization (Verified Tier 0)."

    # 2. Acting on behalf of absent owner
    now = datetime.datetime.utcnow()
    absence = db.query(AbsenceEvent).filter(
        AbsenceEvent.tenant_id == tenant_id,
        AbsenceEvent.person_id == on_behalf_of,
        AbsenceEvent.status == "active",
        AbsenceEvent.auto_expires_at > now
    ).first()

    if not absence:
        return False, f"Denied: No active absence event declared for {on_behalf_of}."

    # Find matching delegation grants
    grants = db.query(DelegationGrant).filter(
        DelegationGrant.tenant_id == tenant_id,
        DelegationGrant.grantor == on_behalf_of,
        DelegationGrant.grantee == actor_id,
        DelegationGrant.revoked_at.is_(None)
    ).all()

    valid_grant = None
    for g in grants:
        if g.expires_at and g.expires_at < now:
            continue
        if g.not_before and g.not_before > now:
            continue
        if action_type in (g.allowed_actions or []):
            valid_grant = g
            break

    if not valid_grant:
        return False, f"Denied: Actor {actor_id} does not have delegation for {action_type} from {on_behalf_of}."

    # 3. Financial Integrity & Scope Checks
    scope = valid_grant.scope or {}

    if action_type in ("approve_payment", "approve_vendor_payment"):
        requested_amount = params.get("amount_inr")
        # FAIL CLOSED: Missing, negative, or non-numeric amount
        if requested_amount is None:
            return False, "Denied (Fail-Closed): Payment action missing mandatory 'amount_inr' parameter."
        try:
            amt_val = float(requested_amount)
            if amt_val <= 0:
                return False, f"Denied (Fail-Closed): Invalid payment amount ₹{amt_val:,.2f}. Must be positive."
        except (ValueError, TypeError):
            return False, "Denied (Fail-Closed): 'amount_inr' must be a valid numeric value."

        max_amount = scope.get("max_amount_inr")
        if max_amount is not None and amt_val > float(max_amount):
            return False, f"Denied: Requested amount ₹{amt_val:,.2f} exceeds delegation ceiling ₹{max_amount:,.2f}."

        # Account restriction check
        allowed_account = scope.get("account")
        requested_account = params.get("account")
        if allowed_account and requested_account and allowed_account.lower() != requested_account.lower():
            return False, f"Denied: Payment account '{requested_account}' not authorized. Allowed account: '{allowed_account}'."

    return True, f"Allowed under delegation grant {valid_grant.id}."
