"""
Span Verifier & Security Boundary Validator
Deterministic Python rules enforcing the core architectural principle:
'The LLM proposes; deterministic code disposes.'
"""
import hashlib
from typing import Tuple, Optional
try:
    from tests.gold_dataset.schema import EvidenceSpan, TrustTier, BenchmarkClaim, ClaimKind
except ImportError:
    from schema import EvidenceSpan, TrustTier, BenchmarkClaim, ClaimKind

class VerificationError(Exception):
    pass

class ForgedAuthorityError(Exception):
    pass

def verify_span(source_text: str, span: EvidenceSpan) -> str:
    """
    Verifies that span.exact_quote exists verbatim in source_text at [span_start:span_end].
    If exact boundaries drifted slightly due to tokenizer artifacts, recovers the true offset
    if the quote exists unambiguously.
    Rejects completely hallucinated quotes.
    Returns sha256 checksum of verified quote for tamper-evident provenance.
    """
    # 1. Exact boundary match
    sub = source_text[span.span_start:span.span_end]
    if sub == span.exact_quote:
        return hashlib.sha256(span.exact_quote.encode("utf-8")).hexdigest()

    # 2. Resilient fallback search
    found_idx = source_text.find(span.exact_quote)
    if found_idx != -1:
        # Check if unique occurrence
        next_idx = source_text.find(span.exact_quote, found_idx + 1)
        if next_idx == -1:
            # Safely re-anchor offsets
            span.span_start = found_idx
            span.span_end = found_idx + len(span.exact_quote)
            return hashlib.sha256(span.exact_quote.encode("utf-8")).hexdigest()

    raise VerificationError(
        f"Span verification failed! Hallucinated or drifted quote: '{span.exact_quote}' "
        f"not found in source."
    )

def validate_authority_claim(claim: BenchmarkClaim, author_trust_tier: TrustTier) -> None:
    """
    Quarantine rule:
    Only TrustTier.OWNER (Tier 0) can establish new authority rules, standing delegations,
    or approve payments out of channel.
    Staff (Tier 1) cannot establish new approval rules or authorize emergency delegations without owner charter.
    Tier 2 (External) and Tier 3 (Untrusted) messages attempting to define decisions,
    approval rules, or claim pre-approved status MUST be quarantined.
    """
    # 1. Staff proxy or hearsay cannot establish approvals or break-glass delegations
    if author_trust_tier == TrustTier.STAFF:
        if claim.kind in (ClaimKind.APPROVAL_RULE, ClaimKind.DECISION):
            raise ForgedAuthorityError(
                f"Quarantine Triggered: Staff member (Tier 1) cannot establish new {claim.kind.value} without Owner signed Charter."
            )
        if getattr(claim, 'action_type', None) in ("approve_payment", "authorize_delegation"):
            raise ForgedAuthorityError(
                f"Quarantine Triggered: Staff member (Tier 1) cannot self-authorize '{claim.action_type}'."
            )

    # 2. External / Untrusted tiers
    if author_trust_tier in (TrustTier.EXTERNAL, TrustTier.UNTRUSTED):
        if claim.kind in (ClaimKind.APPROVAL_RULE, ClaimKind.DECISION):
            raise ForgedAuthorityError(
                f"Quarantine Triggered: Untrusted/External source (Tier {author_trust_tier.value}) "
                f"cannot establish {claim.kind.value} (Subject: '{claim.subject}')."
            )
        if getattr(claim, 'action_type', None) in ("approve_payment", "authorize_delegation"):
            raise ForgedAuthorityError(
                f"Quarantine Triggered: Unauthorized action '{claim.action_type}' from Tier {author_trust_tier.value}."
            )
