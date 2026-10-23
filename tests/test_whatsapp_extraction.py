"""
Test WhatsApp Ingestion & Bedrock Claude Extraction Adapter
Tests:
1. Parsing real Indian format WhatsApp export ([25/10/26, 11:15:30 AM] Author: text)
2. Handling multiline messages and system notices
3. Ingesting into the Evidence Store with automatic trust-tier resolution
4. Running Bedrock Claude extraction adapter and verifying exact quote offsets
"""
from fastapi.testclient import TestClient
from backend.app import app
from backend.parsers.whatsapp_parser import parse_whatsapp_txt

client = TestClient(app)

SAMPLE_WHATSAPP_EXPORT = """
[25/10/26, 9:30:15 AM] Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.
[25/10/26, 9:32:00 AM] Maya Sundaram: Rajesh, Order docket #4092 for Sharma Prints is confirmed for 10,000 embossed carton boxes.
Please make sure the dies are loaded today.
[25/10/26, 10:15:20 AM] Rajesh: Noted madam. Loading the die blocks on machine #2 now.
[25/10/26, 11:00:10 AM] Maya Sundaram: Rajesh, approve vendor payments up to 25,000 INR from the HDFC current account while I am away in Coimbatore.
[25/10/26, 11:45:00 AM] Murugan (Balaji Paper): Madam, advance 18,000 INR transfer pannidu, balance delivery appo.
[25/10/26, 1:15:00 PM] Maya Sundaram: Scratch that earlier shipment to Madurai, do NOT ship the batch yet until buyer inspects proof.
"""

def test_whatsapp_parsing_and_extraction():
    print("="*60)
    print("TESTING WHATSAPP PARSER & BEDROCK EXTRACTION ADAPTER")
    print("="*60)

    # 1. Parse raw text locally
    parsed = parse_whatsapp_txt(SAMPLE_WHATSAPP_EXPORT)
    print(f"[1] Parsed WhatsApp chat lines: {len(parsed)} operational messages recovered.")
    assert len(parsed) == 5, f"Expected 5 operational messages, got {len(parsed)}"

    # 2. Upload via FastAPI /api/ingest/whatsapp
    resp = client.post("/api/ingest/whatsapp", json={
        "tenant_id": "test_tenant",
        "chat_export_text": SAMPLE_WHATSAPP_EXPORT
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    records = data["records"]
    print(f"[2] Successfully ingested {len(records)} messages into Evidence Store.")

    # 3. Test extraction on Maya's authority rule message
    auth_ev = next(r for r in records if "approve vendor payments up to 25,000 INR" in r["preview"])
    ext_resp = client.post(f"/api/evidence/{auth_ev['evidence_id']}/extract")
    assert ext_resp.status_code == 200, ext_resp.text
    cand_data = ext_resp.json()
    candidates = cand_data["candidates"]
    print(f"[3] Extraction Adapter on Evidence {auth_ev['evidence_id'][:8]}... produced {len(candidates)} candidate claims.")
    assert len(candidates) > 0

    first_claim = candidates[0]
    print(f"    - Extracted Kind: {first_claim['kind']}")
    print(f"    - Modality: {first_claim['modality']}")
    print(f"    - Subject: {first_claim['subject']}")
    print(f"    - Exact Quote: '{first_claim['exact_quote']}' (Offsets: {first_claim['span_start']} to {first_claim['span_end']})")

    # Verify offset points directly to exact quote
    source_msg = [m for m in parsed if "approve vendor payments up to 25,000 INR" in m.content][0]
    assert source_msg.content[first_claim["span_start"]:first_claim["span_end"]] == first_claim["exact_quote"]
    print("[4] Verified verbatim quote alignment with 0 character drift!")

    # 4. Test extraction on Retraction message
    retract_ev = next(r for r in records if "Scratch that earlier shipment" in r["preview"])
    retract_resp = client.post(f"/api/evidence/{retract_ev['evidence_id']}/extract")
    assert retract_resp.status_code == 200
    retract_cands = retract_resp.json()["candidates"]
    print(f"[5] Extraction Adapter on Retraction Evidence: {retract_cands[0]['modality'].upper()} -> '{retract_cands[0]['exact_quote']}'")
    assert retract_cands[0]["modality"] == "retracted"

    print("\n" + "="*60)
    print("WHATSAPP INGESTION & EXTRACTION TESTS COMPLETED SUCCESSFULLY!")
    print("="*60)

if __name__ == "__main__":
    test_whatsapp_parsing_and_extraction()
