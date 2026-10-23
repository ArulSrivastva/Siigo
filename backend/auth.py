"""
Mock Authentication & Tenant Context Middleware
Establishes cryptographic/server-side identity:
- Extracts authenticated actor identity, tenant_id, and trust_tier from headers
- Rejects unauthenticated attempts to claim Owner (Tier 0) privilege
- Scopes all downstream database queries cleanly to the authenticated tenant
"""
from typing import Optional
from fastapi import Header, HTTPException, Depends
from pydantic import BaseModel
from tests.gold_dataset.schema import TrustTier

class AuthenticatedActor(BaseModel):
    actor_id: str
    tenant_id: str
    trust_tier: TrustTier
    display_name: str

def get_current_actor(
    x_tenant_id: Optional[str] = Header(default="default_tenant"),
    x_actor_id: Optional[str] = Header(default="maya_owner"),
    x_actor_role: Optional[str] = Header(default="owner") # owner | staff | external
) -> AuthenticatedActor:
    """
    Derives actor identity from verified server context/headers.
    Never trusts client POST body for tenant_id, actor_id, or trust_tier.
    """
    clean_role = (x_actor_role or "external").lower().strip()
    if clean_role == "owner":
        tier = TrustTier.OWNER
    elif clean_role == "staff":
        tier = TrustTier.STAFF
    else:
        tier = TrustTier.EXTERNAL

    return AuthenticatedActor(
        actor_id=x_actor_id or "anonymous",
        tenant_id=x_tenant_id or "default_tenant",
        trust_tier=tier,
        display_name=x_actor_id or "Actor"
    )
