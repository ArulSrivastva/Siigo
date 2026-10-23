"""
Cryptographic Authentication & Tenant Context Middleware
Enforces strict HMAC-SHA256 session token verification:
- Validates token signature, expiration (exp), issued-at (iat), and issuer (iss)
- Strictly rejects public headers (such as X-Actor-Role or X-Demo-Role) from escalating privileges
- Extracts authenticated actor identity, tenant_id, and trust_tier exclusively from verified tokens
- Defaults unauthenticated requests to unprivileged EXTERNAL tier (Tier 2), NEVER Owner
- Scopes all downstream operations cleanly to the authenticated tenant
"""
import hmac
import hashlib
import json
import base64
import time
import os
from typing import Optional, Dict
from fastapi import Header, HTTPException, Depends
from pydantic import BaseModel
from tests.gold_dataset.schema import TrustTier

# Enforce secure signing secret
AUTH_SECRET = os.getenv("SIIGO_AUTH_SECRET", "siigo_hackathon_demo_hmac_secret_2026_key")
TOKEN_ISSUER = "siigo-authority-core"
DEFAULT_TTL_SECONDS = 365 * 86400 # 365 days for verified test fixtures and demo sessions

class AuthenticatedActor(BaseModel):
    actor_id: str
    tenant_id: str
    trust_tier: TrustTier
    display_name: str

def mint_session_token(
    actor_id: str, 
    tenant_id: str, 
    trust_tier: TrustTier, 
    display_name: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> str:
    """Mints an HMAC-SHA256 signed session token with exp, iat, iss, actor_id, tenant_id, and trust_tier claims."""
    now = int(time.time())
    payload = {
        "iss": TOKEN_ISSUER,
        "iat": now,
        "exp": now + ttl_seconds,
        "actor_id": actor_id,
        "tenant_id": tenant_id,
        "trust_tier": trust_tier.value,
        "display_name": display_name
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    sig = hmac.new(AUTH_SECRET.encode("utf-8"), b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"

REQUIRED_CLAIMS = ("exp", "iat", "iss", "actor_id", "tenant_id", "trust_tier")

def verify_session_token(token: str) -> Optional[AuthenticatedActor]:
    """
    Cryptographically verifies HMAC-SHA256 signature and validates all required claims:
    - Signature integrity via hmac.compare_digest
    - Mandatory presence of exp, iat, iss, actor_id, tenant_id, trust_tier
    - Expiration time (exp >= now)
    - Issuance time (iat <= now + 60s skew tolerance, and not stale > 365 days)
    - Issuer match (iss == TOKEN_ISSUER)
    - Trust tier validity (0, 1, or 2)
    Returns AuthenticatedActor on success, or None if invalid, forged, or expired.
    """
    if not token or "." not in token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    b64, sig = parts
    expected_sig = hmac.new(AUTH_SECRET.encode("utf-8"), b64.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None

    try:
        padded = b64 + "=" * (-len(b64) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))

        # Verify all mandatory claims are present
        for rc in REQUIRED_CLAIMS:
            if rc not in payload or payload[rc] is None:
                return None

        # Verify issuer
        if payload.get("iss") != TOKEN_ISSUER:
            return None

        now = int(time.time())
        iat = int(payload["iat"])
        exp = int(payload["exp"])

        # Validate issuance time: allow 60s future clock skew, reject stale > 365 days
        if iat > now + 60:
            return None
        if iat < now - (365 * 86400):
            return None

        # Validate expiration
        if exp < now or exp <= iat:
            return None

        tier_val = payload["trust_tier"]
        if tier_val not in (0, 1, 2):
            return None

        return AuthenticatedActor(
            actor_id=str(payload["actor_id"]),
            tenant_id=str(payload["tenant_id"]),
            trust_tier=TrustTier(tier_val),
            display_name=str(payload.get("display_name", payload["actor_id"]))
        )
    except Exception:
        return None

# Pre-minted cryptographic tokens for verified test fixtures and demo harness
DEMO_TOKENS: Dict[str, str] = {
    "owner": mint_session_token("maya_owner", "default_tenant", TrustTier.OWNER, "Maya Sundaram (Owner)"),
    "staff": mint_session_token("rajesh_staff", "default_tenant", TrustTier.STAFF, "Rajesh (Staff)"),
    "external": mint_session_token("external_guest", "default_tenant", TrustTier.EXTERNAL, "External Guest")
}

def get_current_actor(
    authorization: Optional[str] = Header(default=None),
    x_siigo_session: Optional[str] = Header(default=None)
) -> AuthenticatedActor:
    """
    Derives actor identity strictly from verified HMAC session tokens.
    
    Security Boundary:
    - Extracts token from 'Authorization: Bearer <token>' or 'X-Siigo-Session: <token>'.
    - Validates HMAC-SHA256 signature, issuer, claims, and expiration.
    - If token is missing, invalid, expired, or forged:
      DEFAULTS TO UNPRIVILEGED EXTERNAL TIER (TrustTier.EXTERNAL) with tenant_id="unauthenticated".
    - Unauthenticated callers can NEVER select arbitrary tenant_ids.
    """
    token_str: Optional[str] = None

    if authorization and authorization.lower().startswith("bearer "):
        token_str = authorization[7:].strip()
    elif x_siigo_session:
        token_str = x_siigo_session.strip()

    if token_str:
        actor = verify_session_token(token_str)
        if actor:
            return actor

    # Unauthenticated fallback: strictly unprivileged EXTERNAL tier with unauthenticated tenant
    return AuthenticatedActor(
        actor_id="anonymous_guest",
        tenant_id="unauthenticated",
        trust_tier=TrustTier.EXTERNAL,
        display_name="External Guest (Unauthenticated)"
    )

def require_authenticated_actor(
    actor: AuthenticatedActor = Depends(get_current_actor)
) -> AuthenticatedActor:
    """Enforces that caller has presented a valid, cryptographically verified session token."""
    if actor.actor_id == "anonymous_guest" or actor.tenant_id == "unauthenticated":
        raise HTTPException(
            status_code=401, 
            detail="Authentication required. Provide a valid cryptographic session token via Authorization Bearer header."
        )
    return actor

def require_staff_or_owner(
    actor: AuthenticatedActor = Depends(require_authenticated_actor)
) -> AuthenticatedActor:
    """Enforces that authenticated caller belongs to Tier 0 (Owner) or Tier 1 (Staff)."""
    if actor.trust_tier not in (TrustTier.OWNER, TrustTier.STAFF):
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Insufficient privileges. Staff or Owner tier required. Caller is Tier {actor.trust_tier.value}."
        )
    return actor

def require_owner(
    actor: AuthenticatedActor = Depends(require_authenticated_actor)
) -> AuthenticatedActor:
    """Enforces that authenticated caller is strictly Tier 0 (Owner)."""
    if actor.trust_tier != TrustTier.OWNER:
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Owner tier (Tier 0) required. Caller is Tier {actor.trust_tier.value}."
        )
    return actor
