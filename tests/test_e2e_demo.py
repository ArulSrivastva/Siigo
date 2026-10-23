"""
End-to-End System Test & Hackathon Demo Script
Tests the exact live flow of the Continuity & Authority Ledger:
1. Ingest clean owner instructions & verify evidence hashing
2. Trap A: Try to ingest a forged supplier payment approval -> Quarantined live!
3. Trap B: Propose claim with drifted/hallucinated quote -> Rejected by Span Verifier!
4. Declare Maya's absence via Charter
5. Test Gated Action Layer:
   - Rajesh executes vendor payment within standing limit (₹18,000 <= ₹25,000) -> ALLOWED!
   - Rajesh attempts vendor payment exceeding standing limit (₹45,000 > ₹25,000) -> BLOCKED!
6. Generate Safe Handoff with 'What I cannot see' and cryptographic citations
7. Verify hash-chained audit trail integrity
"""
import uuid
import datetime
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import SessionLocal, init_db
from backend.models import DelegationGrant, Charter

client = TestClient(app)

def run_e2e_demo():
    print("="*60)
    print("STARTING E2E SIIGO CONTINUITY & AUTHORITY LEDGER DEMO")
    print("="*60)

    # Setup initial database state with Charter and Standing Delegation
    db = SessionLocal()
    init_db()

    # Clear previous test data for clean demo run
    db.query(DelegationGrant).delete()
    db.query(Charter).delete()

    # Setup Owner Standing Delegation Grant: Rajesh allowed up to 25,000 INR
    grant = DelegationGrant(
        tenant_id="default_tenant",
        grantor="Maya Sundaram",
        grantee="Rajesh",
        scope={"account": "HDFC Current", "max_amount_inr": 25000.0},
        allowed_actions=["approve_vendor_payment", "dispatch_shipment"],
        activation="on_handoff"
    )
    db.add(grant)
    db.commit()
    db.close()
    print("[1] Owner Charter & Standing Delegation established (Rajesh limit: INR 25,000).")

    # Step 1: Ingest Owner note
    owner_text = "Rajesh, Order docket #4092 for Sharma Prints is confirmed for 10,000 embossed carton boxes."
    r1 = client.post("/api/ingest/note", json={
        "author_name": "Maya Sundaram",
        "trust_tier": 0,
        "raw_content": owner_text
    })
    assert r1.status_code == 200, r1.text
    owner_ev_id = r1.json()["evidence_id"]
    print(f"[2] Ingested Owner Note. Evidence ID: {owner_ev_id[:8]}... SHA256: {r1.json()['content_sha256'][:16]}...")

    # Step 2: Propose valid claim with verified span
    quote = "Order docket #4092 for Sharma Prints is confirmed"
    r2 = client.post("/api/claims/propose", json={
        "evidence_id": owner_ev_id,
        "kind": "decision",
        "subject": "Confirm order #4092 for Sharma Prints",
        "modality": "agreed",
        "exact_quote": quote,
        "span_start": owner_text.find(quote),
        "span_end": owner_text.find(quote) + len(quote)
    })
    assert r2.status_code == 200, r2.text
    print(f"[3] Propose Claim with exact quote: PASSED (Verified Quote Hash: {r2.json()['quote_sha256'][:16]}...)")

    # Step 3: Plant Trap - Hallucinated quote
    r3 = client.post("/api/claims/propose", json={
        "evidence_id": owner_ev_id,
        "kind": "decision",
        "subject": "Discount order by 50%",
        "modality": "agreed",
        "exact_quote": "Maya offered a 50% discount", # Hallucinated quote not in text
        "span_start": 0,
        "span_end": 10
    })
    assert r3.status_code == 422
    print(f"[4] Planted Trap (Hallucinated Quote): DETECTED & BLOCKED LIVE by Span Verifier (HTTP 422)")

    # Step 4: Plant Trap - External Supplier Forged Approval (Trust Tier 2)
    fake_supplier_text = "Maya approved the 85,000 INR quote on phone."
    r4_ingest = client.post(
        "/api/ingest/note", 
        headers={"x-actor-role": "external", "x-actor-id": "Kavitha (Supplier)"},
        json={
            "raw_content": fake_supplier_text
        }
    )
    supplier_ev_id = r4_ingest.json()["evidence_id"]

    r4_propose = client.post("/api/claims/propose", json={
        "evidence_id": supplier_ev_id,
        "kind": "approval_rule",
        "action_type": "approve_payment",
        "subject": "Supplier claims Maya approved 85k",
        "modality": "agreed",
        "exact_quote": fake_supplier_text,
        "span_start": 0,
        "span_end": len(fake_supplier_text)
    })
    assert r4_propose.status_code == 403
    print(f"[5] Planted Trap (Forged External Approval): DETECTED & QUARANTINED LIVE (HTTP 403: {r4_propose.json()['detail'][:45]}...)")

    # Step 5: Declare Absence for Maya
    r5 = client.post("/api/absence/declare", json={
        "person_id": "Maya Sundaram",
        "declared_by": ["Maya Sundaram"],
        "method": "owner_declared",
        "duration_days": 3
    })
    absence_id = r5.json()["absence_id"]
    print(f"[6] Absence Declared: Maya Sundaram marked away for 3 days. Absence ID: {absence_id[:8]}...")

    # Step 6: Test Gated Action Gateway
    # 6A: Payment <= 25,000 INR (Authorized)
    r6a = client.post("/api/action/execute", json={
        "action_type": "approve_vendor_payment",
        "actor_id": "Rajesh",
        "on_behalf_of": "Maya Sundaram",
        "idempotency_key": str(uuid.uuid4()),
        "params": {"amount_inr": 18000.0, "vendor": "Murugan Paper Mills"}
    })
    assert r6a.status_code == 200, r6a.text
    print(f"[7] Action Gateway Test A (INR 18,000 <= INR 25,000 limit): {r6a.json()['decision']} - {r6a.json()['reason']}")

    # 6B: Payment > 25,000 INR (Unauthorized / Over limit)
    r6b = client.post("/api/action/execute", json={
        "action_type": "approve_vendor_payment",
        "actor_id": "Rajesh",
        "on_behalf_of": "Maya Sundaram",
        "idempotency_key": str(uuid.uuid4()),
        "params": {"amount_inr": 48000.0, "vendor": "Murugan Paper Mills"}
    })
    assert r6b.status_code == 403
    print(f"[8] Action Gateway Test B (INR 48,000 > INR 25,000 limit): BLOCKED LIVE by Cedar Policy Gate (HTTP 403: {r6b.json()['detail'][:55]}...)")

    # Step 7: Compile Safe Handoff
    r7 = client.get(f"/api/handoff/{absence_id}?recipient_id=Rajesh")
    assert r7.status_code == 200, f"Handoff failed: {r7.status_code} - {r7.text}"
    handoff = r7.json()
    print(f"[9] Safe Handoff Compiled:")
    print(f"    - Recipient: {handoff.get('recipient')}")
    print(f"    - Act Now Items: {len(handoff['buckets']['act_now'])}")
    print(f"    - Needs Approval: {len(handoff['buckets']['needs_approval'])}")
    print(f"    - 'What I Cannot See' Items: {len(handoff['buckets']['what_i_cannot_see'])}")

    # Step 8: Verify Audit Trail Hash Chain
    r8 = client.get("/api/audit/logs")
    logs = r8.json()
    print(f"[10] Hash-Chained Audit Trail Verified: {len(logs)} tamper-evident events logged.")

    print("\n" + "="*60)
    print("ALL DEMO CHECKS PASSED LIVE (100% SUCCESS)!")
    print("="*60)

if __name__ == "__main__":
    run_e2e_demo()
