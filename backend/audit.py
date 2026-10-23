"""
Tamper-Evident Hash-Chained Audit Logger
Ensures all state transitions, approvals, and absence triggers are cryptographically linked.
"""
import hashlib
import json
import datetime
from sqlalchemy.orm import Session
from backend.models import AuditLog

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def append_audit_event(db: Session, tenant_id: str, actor: str, event: str, payload: dict) -> AuditLog:
    """
    Computes sha256(prev_hash + actor + event + payload_json + timestamp)
    and stores an immutable log entry.
    """
    last_log = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).order_by(AuditLog.seq.desc()).first()
    prev_hash = last_log.hash if last_log else GENESIS_HASH
    now = datetime.datetime.utcnow()
    payload_str = json.dumps(payload, sort_keys=True, default=str)

    content_to_hash = f"{prev_hash}:{actor}:{event}:{payload_str}:{now.isoformat()}"
    curr_hash = hashlib.sha256(content_to_hash.encode("utf-8")).hexdigest()

    entry = AuditLog(
        tenant_id=tenant_id,
        actor=actor,
        event=event,
        payload=payload,
        prev_hash=prev_hash,
        hash=curr_hash,
        timestamp=now
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
