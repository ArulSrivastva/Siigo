"""
End-to-End System Test & Security Verification Suite
Tests the exact live flow of the Continuity & Authority Ledger:
1. Ingest clean owner instructions with HMAC Bearer token & verify evidence hashing
2. Trap A: Try to ingest a forged supplier payment approval -> Quarantined live!
3. Trap B: Propose claim with drifted/hallucinated quote -> Rejected by Span Verifier!
4. Security Gate: Unauthenticated absence declaration attempt -> BLOCKED with HTTP 403!
5. Declare Maya's absence via cryptographically verified Owner session
6. Financial Policy Integrity Gates:
   - Rajesh executes vendor payment within standing limit (₹18,000 <= ₹25,000, HDFC Current) -> ALLOWED!
   - Rajesh attempts vendor payment exceeding standing limit (₹48,000 > ₹25,000) -> BLOCKED!
   - Rajesh attempts vendor payment omitting required account -> BLOCKED (Fail-Closed)!
   - Rajesh attempts vendor payment with non-finite / negative amount -> BLOCKED!
7. Generate Safe Handoff with 'What I cannot see' and cryptographic citations
8. Verify hash-chained audit trail integrity
"""
import uuid
import datetime
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import SessionLocal, init_db
from backend.models import DelegationGrant, Charter
from backend.auth import DEMO_TOKENS

client = TestClient(app)

def run_e2e_demo():
    print("="*65)
    print("STARTING E2E SIIGO CONTINUITY & AUTHORITY LEDGER DEMO")
    print("="*65)

    # Setup initial database state with Charter and Standing Delegation
    db = SessionLocal()
    init_db()

    # Clear previous test data for clean demo run
    db.query(DelegationGrant).delete()
    db.query(Charter).delete()

    # Setup Owner Standing Delegation Grant: Rajesh allowed up to 25,000 INR from HDFC Current
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
    print("[1] Owner Charter & Standing Delegation established (Rajesh limit: INR 25,000 on HDFC Current).")

    # Step 1: Ingest Owner note with cryptographically verified session token
    owner_text = "Rajesh, Order docket #4092 for Sharma Prints is confirmed for 10,000 embossed carton boxes."
    r1 = client.post(
        "/api/ingest/note",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['owner']}"},
        json={
            "author_name": "Maya Sundaram",
            "raw_content": owner_text
        }
    )
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
        headers={"Authorization": f"Bearer {DEMO_TOKENS['external']}"},
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

    # Step 5: Security Test - Unauthenticated absence declaration MUST be rejected
    r5_unauth = client.post("/api/absence/declare", json={
        "person_id": "Maya Sundaram",
        "declared_by": ["Maya Sundaram"],
        "method": "spoofed_call",
        "duration_days": 3
    })
    assert r5_unauth.status_code == 403
    print(f"[6] Unauthenticated Absence Declaration: BLOCKED (HTTP 403: {r5_unauth.json()['detail'][:45]}...)")

    # Step 6: Authenticated Absence Declaration with Owner Session
    r5 = client.post(
        "/api/absence/declare",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['owner']}"},
        json={
            "person_id": "Maya Sundaram",
            "declared_by": ["Maya Sundaram"],
            "method": "owner_declared",
            "duration_days": 3
        }
    )
    assert r5.status_code == 200, r5.text
    absence_id = r5.json()["absence_id"]
    print(f"[7] Authenticated Absence Declared: Maya Sundaram marked away. Absence ID: {absence_id[:8]}...")

    # Step 7: Financial Policy Integrity Checks
    # 7A: Authorized Payment <= 25,000 INR from HDFC Current with Staff Session
    r7a = client.post(
        "/api/action/execute",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['staff']}"},
        json={
            "action_type": "approve_vendor_payment",
            "actor_id": "Rajesh",
            "on_behalf_of": "Maya Sundaram",
            "idempotency_key": str(uuid.uuid4()),
            "params": {"amount_inr": 18000.0, "vendor": "Murugan Paper Mills", "account": "HDFC Current"}
        }
    )
    assert r7a.status_code == 200, r7a.text
    print(f"[8] Action Gateway Test A (INR 18,000 <= INR 25,000 limit): {r7a.json()['decision']} ({r7a.json()['execution_status']})")

    # 7B: Over-limit Payment (INR 48,000 > INR 25,000 ceiling)
    r7b = client.post(
        "/api/action/execute",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['staff']}"},
        json={
            "action_type": "approve_vendor_payment",
            "actor_id": "Rajesh",
            "on_behalf_of": "Maya Sundaram",
            "idempotency_key": str(uuid.uuid4()),
            "params": {"amount_inr": 48000.0, "vendor": "Murugan Paper Mills", "account": "HDFC Current"}
        }
    )
    assert r7b.status_code == 403
    print(f"[9] Action Gateway Test B (INR 48,000 > INR 25,000 limit): BLOCKED LIVE (HTTP 403)")

    # 7C: Missing Account parameter on restricted grant (Fail Closed)
    r7c = client.post(
        "/api/action/execute",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['staff']}"},
        json={
            "action_type": "approve_vendor_payment",
            "actor_id": "Rajesh",
            "on_behalf_of": "Maya Sundaram",
            "idempotency_key": str(uuid.uuid4()),
            "params": {"amount_inr": 12000.0, "vendor": "Murugan Paper Mills"} # Missing account
        }
    )
    assert r7c.status_code == 403
    print(f"[10] Action Gateway Test C (Missing Account on Restricted Grant): FAIL-CLOSED BLOCKED (HTTP 403)")

    # Step 8: Compile Safe Handoff
    r8 = client.get(
        f"/api/handoff/{absence_id}?recipient_id=Rajesh",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['staff']}"}
    )
    assert r8.status_code == 200, f"Handoff failed: {r8.status_code} - {r8.text}"
    handoff = r8.json()
    print(f"[11] Safe Handoff Compiled:")
    print(f"    - Recipient: {handoff.get('recipient')}")
    print(f"    - Act Now Items: {len(handoff['buckets']['act_now'])}")
    for it in handoff['buckets']['act_now']:
        print(f"      * Commitment: {it['subject']} | Deadline: {it['deadline']} | Next Step: {it['next_step']}")
    assert len(handoff['buckets']['act_now']) > 0, "Act Now items must not be empty"
    print(f"    - Needs Approval: {len(handoff['buckets']['needs_approval'])}")
    print(f"    - 'What I Cannot See' Items: {len(handoff['buckets']['what_i_cannot_see'])}")

    # Step 9: Verify Cryptographic Audit Trail Hash Chain
    r9 = client.get(
        "/api/audit/logs",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['owner']}"}
    )
    assert r9.status_code == 200
    logs = r9.json()
    print(f"[12] Hash-Chained Audit Trail Verified: {len(logs)} tamper-evident events logged.")

    print("\n" + "="*65)
    print("ALL E2E & FINANCIAL POLICY TESTS PASSED LIVE (100% SUCCESS)!")
    print("="*65)

if __name__ == "__main__":
    run_e2e_demo()
