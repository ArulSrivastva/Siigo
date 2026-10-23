"""
Siigo Model Context Protocol (MCP) Server
Specification Version: 2025-11-25 (Streamable HTTP / SSE transport compliant)

Exposes Siigo continuity and authority governance tools to LLM agents and Alexa+:
1. siigo_get_continuity_health: Retrieves readiness score, bus factor, and single points of failure.
2. siigo_compile_handoff: Generates grant-scoped safe handoff with verbatim citations and gaps.
3. siigo_verify_evidence_span: Verifies exact substring quote against source text to prevent hallucinations.
4. siigo_evaluate_gated_action: Cedar-style policy evaluation for consequential actions (e.g. payments).
"""
import json
import uuid
import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AbsenceEvent, DelegationGrant
from backend.analyzers import analyze_continuity_health
from backend.handoff_compiler import compile_safe_handoff
from backend.policy_engine import evaluate_action_policy
from tests.gold_dataset.verifier import verify_span, VerificationError
from tests.gold_dataset.schema import EvidenceSpan

mcp_router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (2025-11-25)"])

# Standard MCP Tool Definitions
MCP_TOOLS = [
    {
        "name": "siigo_get_continuity_health",
        "description": "Returns the continuity readiness score, active single points of failure (SPOF), and pending commitments.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "default": "default_tenant"}
            }
        }
    },
    {
        "name": "siigo_compile_handoff",
        "description": "Compiles a verified, evidence-cited Safe Handoff document scoped to the recipient grant with honest coverage gaps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "default": "default_tenant"},
                "recipient_id": {"type": "string", "description": "Delegate name, e.g. Rajesh"}
            },
            "required": ["recipient_id"]
        }
    },
    {
        "name": "siigo_verify_evidence_span",
        "description": "Deterministic quote verifier. Rejects hallucinated quotes by proving verbatim substring match at character offsets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_text": {"type": "string", "description": "The exact source message text"},
                "exact_quote": {"type": "string", "description": "The extracted quote substring"},
                "span_start": {"type": "integer"},
                "span_end": {"type": "integer"}
            },
            "required": ["source_text", "exact_quote", "span_start", "span_end"]
        }
    },
    {
        "name": "siigo_evaluate_gated_action",
        "description": "Gated action policy evaluation. Evaluates whether a financial payment or delegation complies with standing limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "default": "default_tenant"},
                "action_type": {"type": "string", "enum": ["approve_vendor_payment", "dispatch_shipment"]},
                "actor_id": {"type": "string", "description": "Delegate attempting action (e.g. Rajesh)"},
                "on_behalf_of": {"type": "string", "description": "Absent principal (e.g. Maya Sundaram)"},
                "amount_inr": {"type": "number", "description": "Requested payment amount in INR"},
                "account": {"type": "string", "description": "Bank account name (e.g. HDFC Current)"}
            },
            "required": ["action_type", "actor_id", "on_behalf_of", "amount_inr"]
        }
    }
]

class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    method: str
    params: Optional[Dict[str, Any]] = None

@mcp_router.get("/tools")
def list_mcp_tools():
    """Lists MCP tools compliant with MCP spec 2025-11-25."""
    return {
        "mcp_version": "2025-11-25",
        "protocol": "streamable_http",
        "tools": MCP_TOOLS
    }

@mcp_router.post("/execute")
def execute_mcp_tool(req: JSONRPCRequest, db: Session = Depends(get_db)):
    """
    Executes an MCP tool call over standard JSON-RPC 2.0 / Streamable HTTP.
    Calls actual application logic without mocks.
    """
    method = req.method
    params = req.params or {}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {"tools": MCP_TOOLS}
        }

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "siigo_get_continuity_health":
            tenant_id = args.get("tenant_id", "default_tenant")
            health = analyze_continuity_health(db, tenant_id)
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": {"content": [{"type": "text", "text": json.dumps(health)}]}
            }

        elif tool_name == "siigo_compile_handoff":
            tenant_id = args.get("tenant_id", "default_tenant")
            recipient = args.get("recipient_id", "Rajesh")
            latest_abs = db.query(AbsenceEvent).filter(
                AbsenceEvent.tenant_id == tenant_id,
                AbsenceEvent.status == "active"
            ).order_by(AbsenceEvent.started_at.desc()).first()

            if not latest_abs:
                return {
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "error": {"code": -32602, "message": "No active absence declared for this tenant."}
                }

            handoff = compile_safe_handoff(db, tenant_id, latest_abs.id, recipient)
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": {"content": [{"type": "text", "text": json.dumps(handoff)}]}
            }

        elif tool_name == "siigo_verify_evidence_span":
            span = EvidenceSpan(
                exact_quote=args.get("exact_quote", ""),
                span_start=args.get("span_start", 0),
                span_end=args.get("span_end", 0)
            )
            try:
                quote_hash = verify_span(args.get("source_text", ""), span)
                return {
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": {"verified": True, "quote_sha256": quote_hash}
                }
            except VerificationError as e:
                return {
                    "jsonrpc": "2.0",
                    "id": req.id,
                    "result": {"verified": False, "rejection_reason": str(e)}
                }

        elif tool_name == "siigo_evaluate_gated_action":
            tenant_id = args.get("tenant_id", "default_tenant")
            action_type = args.get("action_type")
            actor_id = args.get("actor_id")
            on_behalf_of = args.get("on_behalf_of")
            action_params = {
                "amount_inr": args.get("amount_inr"),
                "account": args.get("account", "HDFC Current")
            }
            allowed, reason = evaluate_action_policy(
                db, tenant_id, action_type, actor_id, on_behalf_of, action_params
            )
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": {
                    "decision": "ALLOW" if allowed else "DENY",
                    "allowed": allowed,
                    "reason": reason,
                    "execution_status": "AUTHORIZED_AND_RECORDED" if allowed else "BLOCKED"
                }
            }

        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "error": {"code": -32601, "message": f"Tool '{tool_name}' not found."}
        }

    return {
        "jsonrpc": "2.0",
        "id": req.id,
        "error": {"code": -32600, "message": f"Unsupported JSON-RPC method '{method}'."}
    }
