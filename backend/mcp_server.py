"""
Siigo Model Context Protocol (MCP) Server
Specification: Streamable HTTP / JSON-RPC 2.0 (Spec 2024-11-05 / 2025-11-25 compatible)

Exposes Siigo continuity and authority governance tools to LLM agents and assistant gateways:
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
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AbsenceEvent, DelegationGrant
from backend.analyzers import analyze_continuity_health
from backend.handoff_compiler import compile_safe_handoff
from backend.policy_engine import evaluate_action_policy
from backend.auth import get_current_actor, AuthenticatedActor
from tests.gold_dataset.verifier import verify_span, VerificationError
from tests.gold_dataset.schema import EvidenceSpan

mcp_router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (Streamable HTTP)"])

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

def dispatch_mcp_jsonrpc(
    req: JSONRPCRequest, 
    actor: AuthenticatedActor,
    db: Session
) -> Dict[str, Any]:
    """
    Central JSON-RPC 2.0 dispatcher for Streamable HTTP MCP transport.
    Strictly tenant-scoped to actor.tenant_id.
    """
    method = req.method
    params = req.params or {}
    tenant_id = actor.tenant_id

    # 1. MCP Protocol Handshake: initialize
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": "siigo-governance-mcp",
                    "version": "1.0.0"
                }
            }
        }

    # 2. MCP Initialized Notification
    if method in ("notifications/initialized", "initialized"):
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {}
        }

    # 3. Ping
    if method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {}
        }

    # 4. Tool Discovery
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {"tools": MCP_TOOLS}
        }

    # 5. Tool Execution
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "siigo_get_continuity_health":
            health = analyze_continuity_health(db, tenant_id)
            return {
                "jsonrpc": "2.0",
                "id": req.id,
                "result": {"content": [{"type": "text", "text": json.dumps(health)}]}
            }

        elif tool_name == "siigo_compile_handoff":
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
            action_type = args.get("action_type")
            actor_id = args.get("actor_id")
            on_behalf_of = args.get("on_behalf_of")
            action_params = {
                "amount_inr": args.get("amount_inr"),
                "account": args.get("account")
            }
            allowed, reason = evaluate_action_policy(
                db=db,
                tenant_id=tenant_id,
                action_type=action_type,
                actor_id=actor_id,
                on_behalf_of=on_behalf_of,
                params=action_params,
                authenticated_actor_tier=actor.trust_tier.value
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

# Standard Streamable HTTP MCP Endpoint
@mcp_router.post("")
@mcp_router.post("/")
def handle_mcp_streamable_http(
    req: JSONRPCRequest,
    actor: AuthenticatedActor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    """Primary standard MCP Streamable HTTP endpoint accepting JSON-RPC 2.0 payloads."""
    return dispatch_mcp_jsonrpc(req, actor, db)

@mcp_router.get("")
@mcp_router.get("/")
def get_mcp_discovery():
    """Streamable HTTP discovery metadata."""
    return {
        "name": "siigo-governance-mcp",
        "protocol": "streamable_http",
        "version": "1.0.0",
        "supported_methods": ["initialize", "ping", "tools/list", "tools/call"],
        "tools_count": len(MCP_TOOLS)
    }

# Backwards compatible alias endpoints
@mcp_router.post("/execute")
def execute_mcp_tool_alias(
    req: JSONRPCRequest, 
    actor: AuthenticatedActor = Depends(get_current_actor),
    db: Session = Depends(get_db)
):
    return dispatch_mcp_jsonrpc(req, actor, db)

@mcp_router.get("/tools")
def list_mcp_tools_alias():
    return {
        "mcp_version": "2025-11-25",
        "protocol": "streamable_http",
        "tools": MCP_TOOLS
    }
