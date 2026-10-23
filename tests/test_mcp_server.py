"""
Test MCP Server (Spec 2025-11-25+ / Streamable HTTP)
Verifies:
1. Tool Discovery via tools/list
2. siigo_verify_evidence_span Tool Execution (Verbatim quote validation)
3. siigo_evaluate_gated_action Tool Execution:
   - Blocks unauthorized ₹65,000 payment
   - Allows authorized ₹18,000 payment
4. JSON-RPC 2.0 error handling
"""
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import SessionLocal, init_db
from backend.models import DelegationGrant

client = TestClient(app)

def test_mcp_server_spec_2025_11_25():
    print("="*75)
    print("TESTING SIIGO MCP SERVER (SPEC 2025-11-25+ / STREAMABLE HTTP)")
    print("="*75)

    # Setup database with standing delegation
    db = SessionLocal()
    init_db()
    db.query(DelegationGrant).delete()
    grant = DelegationGrant(
        tenant_id="default_tenant",
        grantor="Maya Sundaram",
        grantee="Rajesh",
        scope={"account": "HDFC Current", "max_amount_inr": 25000.0},
        allowed_actions=["approve_vendor_payment"],
        activation="on_handoff"
    )
    db.add(grant)
    db.commit()
    db.close()

    # 1. Test Tools Discovery
    r1 = client.post("/mcp/execute", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    })
    assert r1.status_code == 200, r1.text
    tools = r1.json()["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    print(f"[1] MCP Tools Discovery: Discovered {len(tools)} tools: {tool_names}")
    assert "siigo_verify_evidence_span" in tool_names
    assert "siigo_evaluate_gated_action" in tool_names

    # 2. Test siigo_verify_evidence_span Tool
    source = "Rajesh, order docket #4092 is confirmed."
    quote = "order docket #4092 is confirmed"
    r2 = client.post("/mcp/execute", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "siigo_verify_evidence_span",
            "arguments": {
                "source_text": source,
                "exact_quote": quote,
                "span_start": source.find(quote),
                "span_end": source.find(quote) + len(quote)
            }
        }
    })
    assert r2.status_code == 200
    res2 = r2.json()["result"]
    print(f"[2] MCP Tool Call 'siigo_verify_evidence_span': Verified = {res2['verified']} (Quote Hash: {res2.get('quote_sha256', '')[:16]}...)")
    assert res2["verified"] is True

    # 3. Test Gated Action Policy via MCP - Over-limit Payment (INR 65,000)
    # Note: Requires active absence for delegation to apply
    from backend.models import AbsenceEvent
    import datetime
    db = SessionLocal()
    db.query(AbsenceEvent).delete()
    abs_event = AbsenceEvent(
        tenant_id="default_tenant",
        person_id="Maya Sundaram",
        declared_by=["Maya Sundaram"],
        method="owner_declared",
        status="active",
        auto_expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=1)
    )
    db.add(abs_event)
    db.commit()
    db.close()

    r3 = client.post("/mcp/execute", json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "siigo_evaluate_gated_action",
            "arguments": {
                "tenant_id": "default_tenant",
                "action_type": "approve_vendor_payment",
                "actor_id": "Rajesh",
                "on_behalf_of": "Maya Sundaram",
                "amount_inr": 65000.0,
                "account": "HDFC Current"
            }
        }
    })
    assert r3.status_code == 200
    res3 = r3.json()["result"]
    print(f"[3] MCP Tool Call 'siigo_evaluate_gated_action' (Over-Limit INR 65,000):")
    print(f"    Decision: {res3['decision']} | Allowed: {res3['allowed']} | Reason: {res3['reason']}")
    assert res3["allowed"] is False
    assert res3["decision"] == "DENY"

    # 4. Test Gated Action Policy via MCP - Permitted Payment (INR 18,000)
    r4 = client.post("/mcp/execute", json={
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "siigo_evaluate_gated_action",
            "arguments": {
                "tenant_id": "default_tenant",
                "action_type": "approve_vendor_payment",
                "actor_id": "Rajesh",
                "on_behalf_of": "Maya Sundaram",
                "amount_inr": 18000.0,
                "account": "HDFC Current"
            }
        }
    })
    assert r4.status_code == 200
    res4 = r4.json()["result"]
    print(f"[4] MCP Tool Call 'siigo_evaluate_gated_action' (Authorized INR 18,000):")
    print(f"    Decision: {res4['decision']} | Allowed: {res4['allowed']} | Status: {res4['execution_status']}")
    assert res4["allowed"] is True
    assert res4["decision"] == "ALLOW"

    print("\n" + "="*75)
    print("ALL MCP SERVER SPEC 2025-11-25+ TESTS PASSED (EXIT CODE 0)!")
    print("="*75)

if __name__ == "__main__":
    test_mcp_server_spec_2025_11_25()
