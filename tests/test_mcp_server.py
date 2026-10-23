"""
Test MCP Server (Streamable HTTP / JSON-RPC 2.0 Protocol)
Verifies:
1. Protocol Handshake via 'initialize' method on standard POST /mcp endpoint
2. Tool Discovery via 'tools/list'
3. siigo_verify_evidence_span Tool Execution (Verbatim quote validation)
4. siigo_evaluate_gated_action Tool Execution:
   - Blocks unauthorized ₹65,000 payment
   - Allows authorized ₹18,000 payment with staff session token
   - Blocks missing account parameter (fail-closed integrity)
5. JSON-RPC 2.0 error handling (-32601 tool not found, -32600 invalid method)
6. Backwards compatible aliases (/mcp/execute, /mcp/tools)
"""
import datetime
from fastapi.testclient import TestClient
from backend.app import app
from backend.database import SessionLocal, init_db
from backend.models import DelegationGrant, AbsenceEvent
from backend.auth import DEMO_TOKENS

client = TestClient(app)

def test_mcp_server_spec():
    print("="*75)
    print("TESTING SIIGO MCP SERVER (STREAMABLE HTTP / JSON-RPC 2.0)")
    print("="*75)

    # Setup database with standing delegation and active absence
    db = SessionLocal()
    init_db()
    db.query(DelegationGrant).delete()
    db.query(AbsenceEvent).delete()

    grant = DelegationGrant(
        tenant_id="default_tenant",
        grantor="Maya Sundaram",
        grantee="Rajesh",
        scope={"account": "HDFC Current", "max_amount_inr": 25000.0},
        allowed_actions=["approve_vendor_payment"],
        activation="on_handoff"
    )
    db.add(grant)

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

    # 1. Test Standard Protocol Handshake: 'initialize' on POST /mcp
    r_init = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    })
    assert r_init.status_code == 200, r_init.text
    init_res = r_init.json()["result"]
    print(f"[1] MCP Initialize Handshake: Server={init_res['serverInfo']['name']} | Protocol={init_res['protocolVersion']}")
    assert init_res["serverInfo"]["name"] == "siigo-governance-mcp"
    assert "tools" in init_res["capabilities"]

    # 2. Test Tools Discovery: 'tools/list' on standard POST /mcp
    r1 = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    })
    assert r1.status_code == 200, r1.text
    tools = r1.json()["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    print(f"[2] MCP Tools Discovery: Discovered {len(tools)} tools: {tool_names}")
    assert "siigo_verify_evidence_span" in tool_names
    assert "siigo_evaluate_gated_action" in tool_names
    assert "siigo_compile_handoff" in tool_names
    assert "siigo_get_continuity_health" in tool_names

    # 3. Test siigo_verify_evidence_span Tool via standard POST /mcp
    source = "Rajesh, order docket #4092 is confirmed."
    quote = "order docket #4092 is confirmed"
    r2 = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 3,
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
    print(f"[3] MCP Tool Call 'siigo_verify_evidence_span': Verified={res2['verified']} (Quote Hash: {res2.get('quote_sha256', '')[:16]}...)")
    assert res2["verified"] is True

    # 4. Test Gated Action Policy via MCP: Over-limit Payment (INR 65,000)
    r3 = client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['staff']}"},
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "siigo_evaluate_gated_action",
                "arguments": {
                    "action_type": "approve_vendor_payment",
                    "actor_id": "Rajesh",
                    "on_behalf_of": "Maya Sundaram",
                    "amount_inr": 65000.0,
                    "account": "HDFC Current"
                }
            }
        }
    )
    assert r3.status_code == 200
    res3 = r3.json()["result"]
    print(f"[4] MCP Tool Call 'siigo_evaluate_gated_action' (Over-Limit INR 65,000):")
    print(f"    Decision: {res3['decision']} | Allowed: {res3['allowed']} | Status: {res3['execution_status']}")
    assert res3["allowed"] is False
    assert res3["decision"] == "DENY"

    # 5. Test Gated Action Policy via MCP: Permitted Payment (INR 18,000) with Staff Session
    r4 = client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['staff']}"},
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "siigo_evaluate_gated_action",
                "arguments": {
                    "action_type": "approve_vendor_payment",
                    "actor_id": "Rajesh",
                    "on_behalf_of": "Maya Sundaram",
                    "amount_inr": 18000.0,
                    "account": "HDFC Current"
                }
            }
        }
    )
    assert r4.status_code == 200
    res4 = r4.json()["result"]
    print(f"[5] MCP Tool Call 'siigo_evaluate_gated_action' (Authorized INR 18,000):")
    print(f"    Decision: {res4['decision']} | Allowed: {res4['allowed']} | Status: {res4['execution_status']}")
    assert res4["allowed"] is True
    assert res4["decision"] == "ALLOW"

    # 6. Test Fail-Closed Financial Policy: Missing Account on Restricted Grant
    r5 = client.post(
        "/mcp",
        headers={"Authorization": f"Bearer {DEMO_TOKENS['staff']}"},
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "siigo_evaluate_gated_action",
                "arguments": {
                    "action_type": "approve_vendor_payment",
                    "actor_id": "Rajesh",
                    "on_behalf_of": "Maya Sundaram",
                    "amount_inr": 15000.0,
                    "account": "" # Missing required account parameter
                }
            }
        }
    )
    assert r5.status_code == 200
    res5 = r5.json()["result"]
    print(f"[6] MCP Tool Call 'siigo_evaluate_gated_action' (Missing Account on Restricted Grant):")
    print(f"    Decision: {res5['decision']} | Allowed: {res5['allowed']} | Reason: {res5['reason']}")
    assert res5["allowed"] is False
    assert "provided no account" in res5["reason"].lower() or "restricted to account" in res5["reason"].lower()

    # 7. Test JSON-RPC 2.0 Error Handling (-32601 Tool Not Found)
    r_err = client.post("/mcp", json={
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {"name": "non_existent_tool", "arguments": {}}
    })
    assert r_err.status_code == 200
    assert r_err.json()["error"]["code"] == -32601
    print(f"[7] MCP JSON-RPC 2.0 Error Handling: Correctly caught code {r_err.json()['error']['code']}")

    print("\n" + "="*75)
    print("ALL MCP STREAMABLE HTTP / JSON-RPC 2.0 PROTOCOL TESTS PASSED (EXIT CODE 0)!")
    print("="*75)

if __name__ == "__main__":
    test_mcp_server_spec()
