"""
Cedar / Deterministic Policy Engine for Action Gateway
Implements authority policies as code.
Verifies whether a requested action (e.g. approve_payment) is permitted given:
- Verified caller identity, active absence status, and authenticated trust tier
- Standing delegation limits (INR ceilings, mandatory account scopes)
- Fail-closed financial integrity (rejects non-finite, NaN, missing, or negative amounts)
- Owner Charter rules
"""
import datetime
import math
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
       - REJECT if caller is unauthenticated/external (authenticated_actor_tier > 1)
       - Check if owner has an active AbsenceEvent in this tenant
       - Check if actor has an active DelegationGrant for action_type
       - Payment action checks:
          - FAIL CLOSED: amount_inr must be positive finite number (no NaN, Inf, negative, zero)
          - Check ceiling: amount_inr <= max_amount_inr
          - Check account restriction: if grant restricts account, request MUST provide matching account
    Returns (is_allowed, reason)
    """
    # 1. Owner direct action authentication guard
    if actor_id == on_behalf_of:
        if authenticated_actor_tier != 0:
            return False, f"Denied: Spoofed Owner Identity. Actor '{actor_id}' is not authenticated as Tier 0 Owner."
        return True, "Direct owner authorization (Verified Tier 0)."

    # 2. Acting on behalf of absent owner requires at least verified staff tier (Tier 1)
    if authenticated_actor_tier > 1:
        return False, f"Denied (Fail-Closed): Unauthenticated or External caller (Tier {authenticated_actor_tier}) cannot execute delegated actions on behalf of '{on_behalf_of}'."

    # 3. Check for active absence event
    now = datetime.datetime.utcnow()
    absence = db.query(AbsenceEvent).filter(
        AbsenceEvent.tenant_id == tenant_id,
        AbsenceEvent.person_id == on_behalf_of,
        AbsenceEvent.status == "active",
        AbsenceEvent.auto_expires_at > now
    ).first()

    if not absence:
        return False, f"Denied: No active absence event declared for '{on_behalf_of}'."

    # 4. Find matching delegation grants
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
        return False, f"Denied: Actor '{actor_id}' does not possess an active delegation grant for '{action_type}' from '{on_behalf_of}'."

    # 5. Financial Integrity & Scope Checks
    scope = valid_grant.scope or {}

    if action_type in ("approve_payment", "approve_vendor_payment"):
        requested_amount = params.get("amount_inr")
        
        # FAIL CLOSED: Missing amount
        if requested_amount is None:
            return False, "Denied (Fail-Closed): Payment action missing mandatory 'amount_inr' parameter."
        
        # Validate numeric type and finite range
        try:
            amt_val = float(requested_amount)
        except (ValueError, TypeError):
            return False, "Denied (Fail-Closed): 'amount_inr' must be a valid numeric value."

        if math.isnan(amt_val) or math.isinf(amt_val):
            return False, "Denied (Fail-Closed): 'amount_inr' must be a finite, non-NaN number."

        if amt_val <= 0:
            return False, f"Denied (Fail-Closed): Invalid payment amount INR {amt_val:,.2f}. Must be greater than zero."

        # Ceiling check
        max_amount = scope.get("max_amount_inr")
        if max_amount is not None and amt_val > float(max_amount):
            return False, f"Denied: Requested amount INR {amt_val:,.2f} exceeds delegation ceiling INR {float(max_amount):,.2f}."

        # Account restriction check (Fail closed if account is restricted but request omitted it)
        allowed_account = scope.get("account")
        requested_account = params.get("account")
        if allowed_account:
            if not requested_account or not str(requested_account).strip():
                return False, f"Denied (Fail-Closed): Grant is restricted to account '{allowed_account}', but request provided no account."
            if allowed_account.strip().lower() != str(requested_account).strip().lower():
                return False, f"Denied: Payment account '{requested_account}' not authorized. Allowed account: '{allowed_account}'."

    return True, f"Allowed under delegation grant {valid_grant.id}."
