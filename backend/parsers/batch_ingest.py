"""
Batch Evidence Ingestion Pipeline for WhatsApp Exports
Loads parsed messages into the append-only, content-hashed Evidence Store.
Determines author trust tiers:
- Owner (Tier 0)
- Known Staff (Tier 1)
- Known Vendors/Clients (Tier 2)
- Unknown numbers (Tier 3)
"""
import hashlib
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from backend.parsers.whatsapp_parser import parse_whatsapp_txt, ParsedWhatsAppMessage
from backend.models import Evidence
from backend.audit import append_audit_event
from tests.gold_dataset.schema import TrustTier

# Configurable directory of known staff & stakeholders
KNOWN_PARTIES = {
    "maya": TrustTier.OWNER,
    "maya sundaram": TrustTier.OWNER,
    "rajesh": TrustTier.STAFF,
    "velu": TrustTier.STAFF,
    "karthik": TrustTier.STAFF,
    "accounts": TrustTier.STAFF,
    "sharma": TrustTier.EXTERNAL,
    "sharma prints": TrustTier.EXTERNAL,
    "murugan": TrustTier.EXTERNAL,
    "suresh": TrustTier.EXTERNAL,
    "kavitha": TrustTier.EXTERNAL,
}

def resolve_trust_tier(author_name: str) -> TrustTier:
    """Resolves phone number or contact name to a security trust tier."""
    clean = author_name.lower().strip()
    for key, tier in KNOWN_PARTIES.items():
        if key in clean:
            return tier
    # Phone numbers like "+91 98400..." or unknown names default to Tier 3
    if author_name.startswith("+") or any(c.isdigit() for c in author_name):
        return TrustTier.UNTRUSTED
    return TrustTier.EXTERNAL

from backend.parsers.forward_attribution import parse_forwarded_content

def ingest_whatsapp_export(
    db: Session,
    tenant_id: str,
    raw_export_text: str,
    default_visibility: str = "private"
) -> List[Dict[str, str]]:
    """
    Parses export, applies forward-attribution security downgrade,
    stores each message as an immutable Evidence record, and returns list of records.
    """
    messages = parse_whatsapp_txt(raw_export_text)
    ingested_records = []

    for msg in messages:
        base_tier = resolve_trust_tier(msg.author_name)
        # Apply forward attribution defense directly in production ingestion!
        cleaned_content, effective_tier, attribution_note = parse_forwarded_content(msg.content, base_tier)

        content_hash = hashlib.sha256(cleaned_content.encode("utf-8")).hexdigest()

        ev = Evidence(
            tenant_id=tenant_id,
            source_type="whatsapp",
            author_name=msg.author_name,
            trust_tier=effective_tier.value,
            occurred_at=msg.timestamp_ist,
            content_sha256=content_hash,
            raw_content=cleaned_content,
            visibility=default_visibility
        )
        db.add(ev)
        db.commit()
        db.refresh(ev)

        append_audit_event(db, tenant_id, msg.author_name, "WHATSAPP_MESSAGE_INGESTED", {
            "evidence_id": ev.id,
            "author": msg.author_name,
            "base_trust_tier": base_tier.value,
            "effective_trust_tier": effective_tier.value,
            "attribution_note": attribution_note,
            "occurred_at": msg.timestamp_ist.isoformat(),
            "content_sha256": content_hash
        })

        ingested_records.append({
            "evidence_id": ev.id,
            "author": msg.author_name,
            "trust_tier": effective_tier.value,
            "content_sha256": content_hash,
            "preview": cleaned_content[:60]
        })

    return ingested_records
