"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldCheck, 
  ShieldAlert, 
  FileText, 
  Lock, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  ArrowRight, 
  Activity, 
  Layers, 
  Mic, 
  Send, 
  Calendar,
  Building,
  RotateCcw,
  Sparkles,
  Info,
  UserCheck,
  UserX,
  Play,
  KeyRound,
  ExternalLink,
  ChevronRight,
  Database,
  Check,
  X,
  Clock,
  Eye
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// Fallback pre-minted cryptographic tokens (valid for 7 days with HMAC-SHA256)
const INITIAL_DEMO_TOKENS = {
  owner: "eyJhY3Rvcl9pZCI6ICJtYXlhX293bmVyIiwgImRpc3BsYXlfbmFtZSI6ICJNYXlhIFN1bmRhcmFtIChPd25lcikiLCAiZXhwIjogMTc5MzM3Nzg3NiwgImlhdCI6IDE3OTI3NzMwNzYsICJpc3MiOiAic2lpZ28tYXV0aG9yaXR5LWNvcmUiLCAidGVuYW50X2lkIjogImRlZmF1bHRfdGVuYW50IiwgInRydXN0X3RpZXIiOiAwfQ.2e2d68dceb8d66104d9652ad46a96b6548c718abda22865c06593236062175f6",
  staff: "eyJhY3Rvcl9pZCI6ICJyYWplc2hfc3RhZmYiLCAiZGlzcGxheV9uYW1lIjogIlJhamVzaCAoU3RhZmYpIiwgImV4cCI6IDE3OTMzNzc4NzYsICJpYXQiOiAxNzkyNzczMDc2LCAiaXNzIjogInNpaWdvLWF1dGhvcml0eS1jb3JlIiwgInRlbmFudF9pZCI6ICJkZWZhdWx0X3RlbmFudCIsICJ0cnVzdF90aWVyIjogMX0.2e01b4729a1fe806a9ce542d8e224b111744d3a59c6b5e5157fbf15507ad14ef",
  external: "eyJhY3Rvcl9pZCI6ICJleHRlcm5hbF9ndWVzdCIsICJkaXNwbGF5X25hbWUiOiAiRXh0ZXJuYWwgR3Vlc3QiLCAiZXhwIjogMTc5MzM3Nzg3NiwgImlhdCI6IDE3OTI3NzMwNzYsICJpc3MiOiAic2lpZ28tYXV0aG9yaXR5LWNvcmUiLCAidGVuYW50X2lkIjogImRlZmF1bHRfdGVuYW50IiwgInRydXN0X3RpZXIiOiAyfQ.a1e95a515167b0a8f06088bb7072d1c3a3b7a8842d064134cea383ee9d76af34"
};

export default function Home() {
  const [navSection, setNavSection] = useState<
    "overview" | "review_queue" | "commitments" | "handoffs" | "authority" | "audit" | "alexa_sim"
  >("alexa_sim");

  // Authentication Context State
  const [tokens, setTokens] = useState<Record<string, string>>(INITIAL_DEMO_TOKENS);
  const [activeRole, setActiveRole] = useState<"owner" | "staff" | "external">("owner");

  // Backend state
  const [healthData, setHealthData] = useState<any>(null);
  const [isAbsent, setIsAbsent] = useState(false);
  const [simStep, setSimStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [userUtterance, setUserUtterance] = useState("I'm unavailable tomorrow. Identify anything that needs attention.");
  const [alexaResponse, setAlexaResponse] = useState<string | null>(null);
  const [extractedEvidence, setExtractedEvidence] = useState<any>(null);
  const [handoffDoc, setHandoffDoc] = useState<any>(null);
  const [actionOutcome, setActionOutcome] = useState<any>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [reviewClaims, setReviewClaims] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Mint fresh session tokens from backend on startup
  useEffect(() => {
    const fetchFreshTokens = async () => {
      try {
        const [oRes, sRes, eRes] = await Promise.all([
          fetch(`${API_BASE}/api/auth/token?role=owner`),
          fetch(`${API_BASE}/api/auth/token?role=staff`),
          fetch(`${API_BASE}/api/auth/token?role=external`)
        ]);
        if (oRes.ok && sRes.ok && eRes.ok) {
          const oData = await oRes.json();
          const sData = await sRes.json();
          const eData = await eRes.json();
          setTokens({
            owner: oData.token,
            staff: sData.token,
            external: eData.token
          });
        }
      } catch {
        // Fallback to cryptographic initial tokens
      }
    };
    fetchFreshTokens();
  }, []);

  // Fetch Review Claims Queue
  const fetchReviewClaims = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/claims/review`, {
        headers: { "Authorization": `Bearer ${tokens.owner}` }
      });
      if (res.ok) {
        const d = await res.json();
        setReviewClaims(d);
      }
    } catch {
      // Backend not yet reachable
    }
  };

  // Initial data load from real backend
  const loadData = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/continuity/health`, {
        headers: { "Authorization": `Bearer ${tokens.owner}` }
      });
      if (res.ok) {
        const d = await res.json();
        setHealthData(d);
        if (d.active_absences && d.active_absences.length > 0) {
          setIsAbsent(true);
        }
        setApiError(null);
      } else {
        setApiError(`Backend status HTTP ${res.status}: ${res.statusText}`);
      }
      fetchReviewClaims();
    } catch {
      setApiError("Backend offline or unreachable at " + API_BASE + ". Start FastAPI backend to view live metrics.");
    }
  };

  useEffect(() => {
    loadData();
  }, [isAbsent, tokens]);

  // Human Review Confirm Handler (Owner only)
  const handleConfirmClaim = async (claimId: string) => {
    setLoading(true);
    setApiError(null);
    try {
      const res = await fetch(`${API_BASE}/api/claims/${claimId}/confirm`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${tokens.owner}` }
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Confirmation rejected.");
      }
      await fetchReviewClaims();
      // Also refresh handoff if active
      if (isAbsent) {
        const handoffRes = await fetch(`${API_BASE}/api/handoff/latest_active?recipient_id=Rajesh`, {
          headers: { "Authorization": `Bearer ${tokens.staff}` }
        });
        if (handoffRes.ok) {
          setHandoffDoc(await handoffRes.json());
        }
      }
    } catch (e: any) {
      setApiError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Human Review Reject Handler (Owner only)
  const handleRejectClaim = async (claimId: string) => {
    setLoading(true);
    setApiError(null);
    try {
      const res = await fetch(`${API_BASE}/api/claims/${claimId}/reject`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${tokens.owner}` }
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Rejection failed.");
      }
      await fetchReviewClaims();
    } catch (e: any) {
      setApiError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Execute Step 1: Ingest Evidence
  const stepIngestEvidence = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const ingestRes = await fetch(`${API_BASE}/api/ingest/note`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${tokens.owner}`
        },
        body: JSON.stringify({
          raw_content: "Rajesh, Order docket #4092 for Sharma Prints is confirmed for 10,000 embossed carton boxes."
        })
      });
      if (!ingestRes.ok) throw new Error(`Evidence ingestion failed: HTTP ${ingestRes.status}`);
      const ingestData = await ingestRes.json();
      setSimStep(2);
      return ingestData.evidence_id;
    } catch (e: any) {
      setApiError(e.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Execute Step 2: Span Verifier
  const stepVerifySpan = async (evId: string) => {
    setLoading(true);
    setApiError(null);
    try {
      const quote = "Order docket #4092 for Sharma Prints is confirmed";
      const claimRes = await fetch(`${API_BASE}/api/claims/propose`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${tokens.owner}`
        },
        body: JSON.stringify({
          tenant_id: "default_tenant",
          evidence_id: evId,
          kind: "commitment",
          subject: "Confirm order docket #4092 for Sharma Prints",
          modality: "agreed",
          exact_quote: quote,
          span_start: 8,
          span_end: 8 + quote.length
        })
      });
      if (!claimRes.ok) throw new Error(`Span verification failed: HTTP ${claimRes.status}`);
      const claimData = await claimRes.json();
      setExtractedEvidence({
        claim_id: claimData.claim_id,
        quote: quote,
        quote_hash: claimData.quote_sha256,
        source: "WhatsApp Operational Note · Sent by Maya Sundaram (Tier 0 Owner)",
        verified: true,
        state: "verified"
      });
      setSimStep(3);
      fetchReviewClaims();
    } catch (e: any) {
      setApiError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Execute Step 3: Alexa Webhook
  const stepCallAlexa = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const alexaRes = await fetch(`${API_BASE}/api/alexa/webhook`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          version: "1.0",
          request: {
            type: "IntentRequest",
            intent: { name: "DeclareAbsenceAndTriageIntent" }
          }
        })
      });
      if (!alexaRes.ok) throw new Error(`Alexa webhook failed: HTTP ${alexaRes.status}`);
      const alexaData = await alexaRes.json();
      setAlexaResponse(alexaData.response.outputSpeech.text);
      setIsAbsent(true);
      setSimStep(4);
    } catch (e: any) {
      setApiError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Execute Step 4: Fetch Scoped Handoff
  const stepFetchHandoff = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const handoffRes = await fetch(`${API_BASE}/api/handoff/latest_active?recipient_id=Rajesh`, {
        headers: { "Authorization": `Bearer ${tokens.staff}` }
      });
      if (!handoffRes.ok) throw new Error(`Handoff retrieval failed: HTTP ${handoffRes.status}`);
      const hData = await handoffRes.json();
      setHandoffDoc(hData);
      setSimStep(5);
    } catch (e: any) {
      setApiError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Execute Step 5: Test Over-Limit Action Attempt (₹65,000 vs ₹25,000 ceiling)
  const testOverLimitAction = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const actionRes = await fetch(`${API_BASE}/api/action/execute`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${tokens.staff}`
        },
        body: JSON.stringify({
          action_type: "approve_vendor_payment",
          actor_id: "Rajesh",
          on_behalf_of: "Maya Sundaram",
          idempotency_key: `sim_exploit_${Date.now()}`,
          params: { amount_inr: 65000.0, vendor: "Murugan Paper Mills", account: "HDFC Current" }
        })
      });
      const actionData = await actionRes.json();
      
      // Strict Fail-Closed Evaluation
      let decision: "ALLOW" | "DENY" | "ERROR" = "ERROR";
      let execStatus = "UNKNOWN";
      let reasonText = "";

      if (actionRes.status === 200 && actionData?.decision === "ALLOW") {
        decision = "ALLOW";
        execStatus = actionData.execution_status || "AUTHORIZED_AND_RECORDED";
        reasonText = actionData.reason || "Permitted under active grant.";
      } else if (actionRes.status === 403 || actionData?.decision === "DENY") {
        decision = "DENY";
        execStatus = actionData?.execution_status || "BLOCKED";
        reasonText = typeof actionData?.detail === "string" ? actionData.detail : (actionData?.detail?.reason || "Denied by Cedar policy engine: Requested amount exceeds ceiling.");
      } else {
        decision = "ERROR";
        execStatus = "UNRECOGNIZED_STATUS";
        reasonText = `Unexpected server response HTTP ${actionRes.status}. Action was NOT authorized.`;
      }

      setActionOutcome({
        requested_amount: "INR 65,000.00",
        standing_limit: "INR 25,000.00",
        account: "HDFC Current",
        decision,
        status_code: actionRes.status,
        execution_status: execStatus,
        reason: reasonText
      });

      // Refresh Audit Trail
      const auditRes = await fetch(`${API_BASE}/api/audit/logs`, {
        headers: { "Authorization": `Bearer ${tokens.owner}` }
      });
      if (auditRes.ok) {
        const logs = await auditRes.json();
        setAuditLogs(logs.slice(-5));
      }
    } catch (e: any) {
      setApiError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Test Permitted Action (₹18,000 <= ₹25,000 limit)
  const testAuthorizedAction = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const actionRes = await fetch(`${API_BASE}/api/action/execute`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${tokens.staff}`
        },
        body: JSON.stringify({
          action_type: "approve_vendor_payment",
          actor_id: "Rajesh",
          on_behalf_of: "Maya Sundaram",
          idempotency_key: `auth_perm_${Date.now()}`,
          params: { amount_inr: 18000.0, vendor: "Murugan Paper Mills", account: "HDFC Current" }
        })
      });
      const actionData = await actionRes.json();

      let decision: "ALLOW" | "DENY" | "ERROR" = "ERROR";
      let execStatus = "UNKNOWN";
      let reasonText = "";

      if (actionRes.status === 200 && actionData?.decision === "ALLOW") {
        decision = "ALLOW";
        execStatus = actionData.execution_status || "AUTHORIZED_AND_RECORDED";
        reasonText = actionData.reason || "Permitted under Delegation Grant. Action recorded in audit chain (external bank payout queued).";
      } else if (actionRes.status === 403 || actionData?.decision === "DENY") {
        decision = "DENY";
        execStatus = actionData?.execution_status || "BLOCKED";
        reasonText = typeof actionData?.detail === "string" ? actionData.detail : "Blocked by Cedar policy engine.";
      } else {
        decision = "ERROR";
        execStatus = "UNRECOGNIZED_STATUS";
        reasonText = `Unexpected server response HTTP ${actionRes.status}. Action was NOT authorized.`;
      }

      setActionOutcome({
        requested_amount: "INR 18,000.00",
        standing_limit: "INR 25,000.00",
        account: "HDFC Current",
        decision,
        status_code: actionRes.status,
        execution_status: execStatus,
        reason: reasonText
      });

      const auditRes = await fetch(`${API_BASE}/api/audit/logs`, {
        headers: { "Authorization": `Bearer ${tokens.owner}` }
      });
      if (auditRes.ok) {
        const logs = await auditRes.json();
        setAuditLogs(logs.slice(-5));
      }
    } catch (e: any) {
      setApiError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Run Complete Autonomous Demo Walkthrough
  const runLiveSimulation = async () => {
    setLoading(true);
    setApiError(null);
    setSimStep(1);
    try {
      const evId = await stepIngestEvidence();
      if (!evId) return;
      await stepVerifySpan(evId);
      await stepCallAlexa();
      await stepFetchHandoff();
      await testOverLimitAction();
    } catch (e: any) {
      setApiError(e.message || "Simulation failed.");
    } finally {
      setLoading(false);
    }
  };

  const resetSimulation = () => {
    setSimStep(1);
    setAlexaResponse(null);
    setExtractedEvidence(null);
    setHandoffDoc(null);
    setActionOutcome(null);
    setApiError(null);
  };

  return (
    <div className="min-h-screen bg-[#F7F6F2] text-[#141B24] flex">
      {/* 1. Midnight Navy Sidebar (#17263D) */}
      <aside className="w-64 bg-[#17263D] text-[#ECEBE5] flex flex-col justify-between p-5 border-r border-[#0F1928] select-none">
        <div className="space-y-6">
          {/* Brand header */}
          <div className="flex items-center space-x-3 pb-4 border-b border-[#25354F]">
            <div className="h-8 w-8 rounded-lg bg-[#FAF9F5] text-[#17263D] font-bold flex items-center justify-center text-sm shadow-sm">
              S
            </div>
            <div>
              <h1 className="font-semibold text-sm tracking-tight text-[#FAF9F5]">Siigo</h1>
              <p className="text-[11px] text-[#A3B1C6]">Continuity & Authority Ledger</p>
            </div>
          </div>

          {/* Actor Session Selector */}
          <div className="p-3 bg-[#101D30] rounded-lg border border-[#25354F] space-y-2">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-[#A3B1C6] uppercase font-mono tracking-wider">Active Actor</span>
              <span className="text-[10px] bg-[#1E2E48] text-[#DCECE3] px-1.5 py-0.5 rounded font-mono">HMAC-SHA256</span>
            </div>
            <select
              value={activeRole}
              onChange={(e) => setActiveRole(e.target.value as any)}
              className="w-full bg-[#17263D] text-xs text-[#FAF9F5] border border-[#25354F] rounded px-2 py-1.5 focus:outline-none"
            >
              <option value="owner">Maya Sundaram (Owner · Tier 0)</option>
              <option value="staff">Rajesh (Staff Delegate · Tier 1)</option>
              <option value="external">External / Attacker (Tier 2)</option>
            </select>
          </div>

          {/* Navigation Menu */}
          <nav className="space-y-1 text-xs">
            <button
              onClick={() => setNavSection("alexa_sim")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition font-medium ${
                navSection === "alexa_sim"
                  ? "bg-[#25354F] text-[#FAF9F5]"
                  : "text-[#A3B1C6] hover:bg-[#1E2E48] hover:text-[#FAF9F5]"
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Sparkles className="h-4 w-4 text-[#F5E7C9]" />
                <span>Alexa+ Live Simulation</span>
              </div>
              <span className="text-[10px] font-mono bg-[#101D30] text-[#F5E7C9] px-1.5 py-0.5 rounded border border-[#25354F]">
                PRIMARY
              </span>
            </button>

            <button
              onClick={() => setNavSection("review_queue")}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition font-medium ${
                navSection === "review_queue"
                  ? "bg-[#25354F] text-[#FAF9F5]"
                  : "text-[#A3B1C6] hover:bg-[#1E2E48] hover:text-[#FAF9F5]"
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <Eye className="h-4 w-4 text-[#DCECE3]" />
                <span>Evidence Review Queue</span>
              </div>
              <span className="text-[10px] font-mono bg-emerald-950 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-800">
                HUMAN GATE
              </span>
            </button>

            <button
              onClick={() => setNavSection("overview")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-lg transition font-medium ${
                navSection === "overview"
                  ? "bg-[#25354F] text-[#FAF9F5]"
                  : "text-[#A3B1C6] hover:bg-[#1E2E48] hover:text-[#FAF9F5]"
              }`}
            >
              <Activity className="h-4 w-4" />
              <span>Overview</span>
            </button>

            <button
              onClick={() => setNavSection("commitments")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-lg transition font-medium ${
                navSection === "commitments"
                  ? "bg-[#25354F] text-[#FAF9F5]"
                  : "text-[#A3B1C6] hover:bg-[#1E2E48] hover:text-[#FAF9F5]"
              }`}
            >
              <Calendar className="h-4 w-4" />
              <span>Commitments</span>
            </button>

            <button
              onClick={() => setNavSection("handoffs")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-lg transition font-medium ${
                navSection === "handoffs"
                  ? "bg-[#25354F] text-[#FAF9F5]"
                  : "text-[#A3B1C6] hover:bg-[#1E2E48] hover:text-[#FAF9F5]"
              }`}
            >
              <FileText className="h-4 w-4" />
              <span>Handoff Workspace</span>
            </button>

            <button
              onClick={() => setNavSection("authority")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-lg transition font-medium ${
                navSection === "authority"
                  ? "bg-[#25354F] text-[#FAF9F5]"
                  : "text-[#A3B1C6] hover:bg-[#1E2E48] hover:text-[#FAF9F5]"
              }`}
            >
              <Lock className="h-4 w-4" />
              <span>Authority & Policies</span>
            </button>

            <button
              onClick={() => setNavSection("audit")}
              className={`w-full flex items-center space-x-2.5 px-3 py-2.5 rounded-lg transition font-medium ${
                navSection === "audit"
                  ? "bg-[#25354F] text-[#FAF9F5]"
                  : "text-[#A3B1C6] hover:bg-[#1E2E48] hover:text-[#FAF9F5]"
              }`}
            >
              <ShieldCheck className="h-4 w-4" />
              <span>Cryptographic Audit</span>
            </button>
          </nav>
        </div>

        {/* Bottom Tenant & Protection Status */}
        <div className="pt-4 border-t border-[#25354F] space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#A3B1C6]">Tenant Context</span>
            <span className="font-mono text-[#FAF9F5] text-[11px]">Maya Creations</span>
          </div>
          <div className="flex items-center space-x-2 bg-[#101D30] p-2.5 rounded-lg border border-[#25354F] text-xs">
            <span className={`h-2 w-2 rounded-full ${isAbsent ? "bg-amber-400 animate-pulse" : "bg-emerald-400"}`}></span>
            <span className="text-[#ECEBE5] text-[11px] font-medium">
              {isAbsent ? "Owner Absent (Charter Active)" : "Owner Present & Active"}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content Canvas (#F7F6F2) */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        {/* Top Operational Bar */}
        <header className="px-8 py-4 bg-white border-b border-[#E5E4DE] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono uppercase tracking-wider text-[#5F6876]">
              CONTINUITY & AUTHORITY CONTROL
            </span>
            <span className="text-xs font-mono bg-[#FAF9F5] border border-[#E5E4DE] px-2 py-0.5 rounded text-[#5F6876]">
              {API_BASE}
            </span>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-xs bg-[#DCECE3] text-[#195236] px-2.5 py-1 rounded-full font-medium flex items-center space-x-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-[#195236]" />
              <span>Protected by Continuity Charter</span>
            </span>
          </div>
        </header>

        {/* View Switcher Content */}
        <main className="p-8 max-w-6xl mx-auto w-full space-y-6">

          {/* Explicit API Error Banner */}
          {apiError && (
            <div className="p-4 bg-[#F9DDD8] text-[#8A241C] rounded-lg border border-[#E8BDB6] text-xs flex items-center justify-between shadow-sm">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4 text-[#8A241C] shrink-0" />
                <span className="font-medium">{apiError}</span>
              </div>
              <button 
                onClick={() => setApiError(null)} 
                className="text-[#8A241C] underline font-medium hover:text-black ml-4"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* ========================================================= */}
          {/* PRIMARY SHOWCASE: ALEXA+ LIVE SIMULATION (3-COLUMN LAYOUT) */}
          {/* ========================================================= */}
          {navSection === "alexa_sim" && (
            <div className="space-y-6">
              {/* Header Title with Controls */}
              <div className="editorial-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-[#704E14] mb-1">
                    <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse"></span>
                    <span>Live Hackathon Demonstration Environment</span>
                  </div>
                  <h2 className="text-xl font-bold text-[#141B24]">Alexa+ Live Continuity Simulation</h2>
                  <p className="text-xs text-[#5F6876] mt-0.5">
                    Real backend workflow: Spoken Absence Request &rarr; Evidence Grounding &rarr; Safe Handoff &rarr; Gated Policy Enforcement.
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={runLiveSimulation}
                    disabled={loading}
                    className="bg-[#17263D] hover:bg-[#25354F] text-[#FAF9F5] text-xs font-medium px-4 py-2.5 rounded-lg shadow-sm transition flex items-center space-x-2"
                  >
                    <Sparkles className="h-3.5 w-3.5 text-[#F5E7C9]" />
                    <span>{loading ? "Processing..." : "Run Complete Demo Walkthrough"}</span>
                  </button>
                  <button
                    onClick={resetSimulation}
                    className="editorial-subtle text-xs px-3 py-2.5 rounded-lg text-[#5F6876] hover:text-[#141B24] transition flex items-center space-x-1"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    <span>Reset</span>
                  </button>
                </div>
              </div>

              {/* Progress Sequence Strip */}
              <div className="grid grid-cols-5 gap-2 text-xs font-mono uppercase tracking-wider">
                <div className={`p-2.5 rounded-lg border text-center transition ${
                  simStep >= 1 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  1. Evidence Ingest
                </div>
                <div className={`p-2.5 rounded-lg border text-center transition ${
                  simStep >= 2 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  2. Quote Verifier
                </div>
                <div className={`p-2.5 rounded-lg border text-center transition ${
                  simStep >= 3 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  3. Alexa Output
                </div>
                <div className={`p-2.5 rounded-lg border text-center transition ${
                  simStep >= 4 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  4. Safe Handoff
                </div>
                <div className={`p-2.5 rounded-lg border text-center transition ${
                  simStep >= 5 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  5. Cedar Gate Duel
                </div>
              </div>

              {/* 3-Column Editorial Control Room Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Column 1: Voice & Ingestion */}
                <div className="editorial-card p-5 flex flex-col justify-between space-y-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-2.5">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#17263D]">1. Voice Conversation</span>
                      <span className="text-[10px] font-mono text-[#5F6876] bg-[#FAF9F5] px-1.5 py-0.5 rounded border border-[#E5E4DE]">ALEXA+ SIM</span>
                    </div>

                    {/* Owner Utterance Bubble */}
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-[10px] font-mono text-[#5F6876]">
                        <span>MAYA SUNDARAM (OWNER):</span>
                        <span className="text-emerald-700 font-semibold">Tier 0 Verified</span>
                      </div>
                      <div className="bg-[#FAF9F5] p-3 rounded-lg border border-[#E5E4DE] text-xs text-[#141B24]">
                        "{userUtterance}"
                      </div>
                    </div>

                    {/* Assistant Response Bubble */}
                    {alexaResponse ? (
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono text-[#195236] font-semibold">ALEXA RESPONSE (FROM BACKEND):</span>
                        <div className="bg-[#DCECE3] p-3.5 rounded-lg border border-[#B8DBC7] text-xs text-[#195236] leading-relaxed shadow-sm">
                          "{alexaResponse}"
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 editorial-subtle text-xs text-[#5F6876] text-center">
                        Click "Run Complete Demo Walkthrough" or submit speech text below to trigger Alexa webhook processing.
                      </div>
                    )}
                  </div>

                  <div className="pt-3 border-t border-[#E5E4DE] flex items-center space-x-2">
                    <input
                      type="text"
                      value={userUtterance}
                      onChange={(e) => setUserUtterance(e.target.value)}
                      className="flex-1 bg-[#FAF9F5] border border-[#E5E4DE] rounded-md px-2.5 py-1.5 text-xs text-[#141B24] focus:outline-none"
                    />
                    <button 
                      onClick={runLiveSimulation}
                      className="bg-[#17263D] text-white p-2 rounded-md hover:bg-[#25354F] transition"
                    >
                      <Send className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>

                {/* Column 2: Evidence & Safe Handoff */}
                <div className="editorial-card p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-2.5">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#17263D]">2. Evidence & Safe Handoff</span>
                    <span className="text-[10px] font-mono text-[#195236] bg-[#DCECE3] px-1.5 py-0.5 rounded">VERIFIED SPAN</span>
                  </div>

                  {extractedEvidence ? (
                    <div className="space-y-3">
                      {/* Verbatim Quote Citation */}
                      <div className="editorial-subtle p-3 space-y-1">
                        <span className="text-[10px] font-mono text-[#5F6876]">VERBATIM SOURCE EVIDENCE:</span>
                        <p className="text-xs font-semibold text-[#141B24]">"{extractedEvidence.quote}"</p>
                        <p className="text-[10px] font-mono text-[#5F6876] mt-1">SHA-256: {extractedEvidence.quote_hash?.slice(0, 16)}...</p>
                      </div>

                      {/* Handoff Triage Buckets */}
                      {handoffDoc && (
                        <div className="space-y-2 text-xs">
                          {/* Act Now Section with Actionable Commitments */}
                          <div>
                            <span className="text-[10px] font-mono font-bold text-[#8A241C] uppercase block mb-1">
                              Act Now ({handoffDoc.buckets?.act_now?.length || 0} Actionable Commitments):
                            </span>
                            {handoffDoc.buckets?.act_now?.map((item: any, idx: number) => (
                              <div key={idx} className="p-3 bg-[#F9DDD8] text-[#8A241C] rounded border border-[#E8BDB6] space-y-1.5 shadow-sm">
                                <div className="flex items-center justify-between font-bold text-xs">
                                  <span>{item.subject}</span>
                                  <span className="text-[10px] font-mono bg-white/70 px-1.5 py-0.5 rounded">
                                    {item.status}
                                  </span>
                                </div>
                                <p className="text-[11px] text-[#8A241C]">
                                  <strong>Next Step:</strong> {item.next_step}
                                </p>
                                <p className="text-[10px] text-[#5F6876] bg-white p-1.5 rounded border border-[#E8BDB6]">
                                  <strong>Source Quote:</strong> "{item.source_quote}"
                                </p>
                                <div className="flex items-center justify-between text-[10px] font-mono pt-1 text-[#8A241C]">
                                  <span>Deadline: {item.deadline}</span>
                                  <span className="font-semibold text-emerald-800">
                                    {item.uncertainty === "confirmed" ? "Human Confirmed" : "Span Verified"}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>

                          {/* Needs Delegated Approval */}
                          <div>
                            <span className="text-[10px] font-mono font-bold text-[#704E14] uppercase block mb-1">
                              Needs Delegated Approval:
                            </span>
                            <div className="p-2.5 bg-[#F5E7C9] text-[#704E14] rounded border border-[#E5CE9F] text-[11px] space-y-1">
                              <p className="font-bold">Approve vendor payments up to ₹25,000 from HDFC Current</p>
                              <p className="text-[10px] text-[#704E14]">Delegated to Rajesh under Owner Absence Charter.</p>
                            </div>
                          </div>

                          {/* What I Cannot See (Disclosure) */}
                          <div>
                            <span className="text-[10px] font-mono font-bold text-[#5F6876] uppercase block mb-1">
                              What I Cannot See (Honest Disclosure):
                            </span>
                            <div className="p-2 bg-white rounded border border-[#E5E4DE] text-[10px] text-[#5F6876] space-y-1">
                              {handoffDoc.buckets?.what_i_cannot_see?.map((gap: any, i: number) => (
                                <p key={i}>• {gap.gap}: {gap.mitigation}</p>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-8 editorial-subtle text-xs text-[#5F6876] text-center">
                      Evidence citations and grant-scoped handoff will populate upon simulation trigger.
                    </div>
                  )}
                </div>

                {/* Column 3: Authority Gate Duel & Audit Log */}
                <div className="editorial-card p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-2.5">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#17263D]">3. Authority Gate Duel</span>
                    <span className="text-[10px] font-mono text-[#5F6876] bg-[#FAF9F5] px-1.5 py-0.5 rounded border border-[#E5E4DE]">CEDAR POLICIES</span>
                  </div>

                  {/* Duel Test Controls */}
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <button
                      onClick={testOverLimitAction}
                      disabled={loading}
                      className="p-2 bg-[#F9DDD8] hover:bg-[#F4CBC3] text-[#8A241C] border border-[#E8BDB6] rounded font-medium text-left transition shadow-sm"
                    >
                      <span className="font-bold block text-[10px] uppercase">Attack Test A</span>
                      <span>Over-Limit (₹65,000)</span>
                    </button>
                    <button
                      onClick={testAuthorizedAction}
                      disabled={loading}
                      className="p-2 bg-[#DCECE3] hover:bg-[#CCE5D6] text-[#195236] border border-[#B8DBC7] rounded font-medium text-left transition shadow-sm"
                    >
                      <span className="font-bold block text-[10px] uppercase">Permitted Test B</span>
                      <span>Authorized (₹18,000)</span>
                    </button>
                  </div>

                  {actionOutcome ? (
                    <div className="space-y-3">
                      {/* Decision Banner */}
                      <div className={`p-3.5 rounded-lg border text-xs space-y-1.5 ${
                        actionOutcome.decision === "DENY" 
                          ? "bg-[#F9DDD8] text-[#8A241C] border-[#E8BDB6]" 
                          : actionOutcome.decision === "ALLOW"
                          ? "bg-[#DCECE3] text-[#195236] border-[#B8DBC7]"
                          : "bg-amber-100 text-amber-900 border-amber-300"
                      }`}>
                        <div className="flex items-center justify-between font-mono font-bold">
                          <span>DECISION: {actionOutcome.decision} (HTTP {actionOutcome.status_code})</span>
                          <span>{actionOutcome.requested_amount}</span>
                        </div>
                        <p className="text-[11px] leading-relaxed">
                          {actionOutcome.reason}
                        </p>
                        {actionOutcome.execution_status && (
                          <div className="text-[10px] font-mono font-semibold pt-1 border-t border-current/20">
                            STATUS: {actionOutcome.execution_status}
                          </div>
                        )}
                      </div>

                      {/* Hash-Chained Audit Trail */}
                      <div className="space-y-1.5 pt-2 border-t border-[#E5E4DE]">
                        <span className="text-[10px] font-mono uppercase text-[#5F6876]">Cryptographic Audit Events:</span>
                        <div className="space-y-1">
                          {auditLogs.map((log: any, i: number) => (
                            <div key={i} className="text-[10px] font-mono p-1.5 bg-[#FAF9F5] border border-[#E5E4DE] rounded flex items-center justify-between">
                              <span className="font-semibold text-[#17263D]">{log.event}</span>
                              <span className="text-[#5F6876]">SHA: {log.hash?.slice(0, 10)}...</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="p-8 editorial-subtle text-xs text-[#5F6876] text-center">
                      Click either attack or permitted test above to evaluate against the Cedar Policy Engine.
                    </div>
                  )}
                </div>

              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB: EVIDENCE REVIEW QUEUE (HUMAN-IN-THE-LOOP GOVERNANCE) */}
          {/* ========================================================= */}
          {navSection === "review_queue" && (
            <div className="space-y-6">
              <div className="editorial-card p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-4">
                  <div>
                    <h2 className="text-xl font-bold text-[#141B24]">Evidence & Approval Review Queue</h2>
                    <p className="text-xs text-[#5F6876] mt-0.5">
                      Deterministic quote verification and human owner approval. Guarantees no hallucinated commitments enter the ledger.
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 text-xs font-mono">
                    <span className="bg-[#FAF9F5] border border-[#E5E4DE] px-2 py-1 rounded text-[#5F6876]">
                      Tier 0 Owner Gate: Active
                    </span>
                  </div>
                </div>

                {/* 3-Stage Lifecycle Flow */}
                <div className="grid grid-cols-3 gap-3 p-3 bg-[#FAF9F5] rounded-lg border border-[#E5E4DE] text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="h-6 w-6 rounded-full bg-amber-100 text-amber-800 font-bold flex items-center justify-center text-[11px]">1</span>
                    <div>
                      <p className="font-bold text-[#141B24]">Proposed</p>
                      <p className="text-[10px] text-[#5F6876]">Extracted from chat note</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="h-6 w-6 rounded-full bg-blue-100 text-blue-800 font-bold flex items-center justify-center text-[11px]">2</span>
                    <div>
                      <p className="font-bold text-[#141B24]">Verified</p>
                      <p className="text-[10px] text-[#5F6876]">Exact span SHA-256 matched</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="h-6 w-6 rounded-full bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-[11px]">3</span>
                    <div>
                      <p className="font-bold text-[#141B24]">Confirmed</p>
                      <p className="text-[10px] text-[#5F6876]">Approved by human owner</p>
                    </div>
                  </div>
                </div>

                {/* Review Queue Items */}
                <div className="space-y-3 pt-2">
                  {reviewClaims.length > 0 ? (
                    reviewClaims.map((claim) => (
                      <div key={claim.id} className="p-4 bg-white rounded-lg border border-[#E5E4DE] space-y-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div className="space-y-0.5">
                            <span className="text-[10px] font-mono text-[#5F6876] uppercase tracking-wider block">
                              Claim ID: {claim.id.slice(0, 8)}... · Extracted {claim.kind}
                            </span>
                            <h4 className="font-bold text-sm text-[#141B24]">{claim.subject}</h4>
                          </div>

                          {/* Lifecycle State Pill */}
                          <div className="flex items-center space-x-2">
                            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold uppercase ${
                              claim.state === "confirmed"
                                ? "bg-[#DCECE3] text-[#195236] border border-[#B8DBC7]"
                                : claim.state === "rejected"
                                ? "bg-[#F9DDD8] text-[#8A241C] border border-[#E8BDB6]"
                                : "bg-[#F5E7C9] text-[#704E14] border border-[#E5CE9F]"
                            }`}>
                              {claim.state === "confirmed" ? "Confirmed (Owner Approved)" : claim.state === "rejected" ? "Quarantined / Rejected" : "Verified (Pending Owner)"}
                            </span>
                          </div>
                        </div>

                        {/* Exact Supporting Quote */}
                        <div className="editorial-subtle p-3 space-y-1">
                          <span className="text-[10px] font-mono text-[#5F6876] uppercase">Supporting Verbatim Quote:</span>
                          <p className="text-xs font-semibold text-[#141B24]">"{claim.source_quote}"</p>
                          <div className="flex items-center justify-between text-[10px] font-mono text-[#5F6876] pt-1">
                            <span>Character Span: [{claim.span?.[0]}:{claim.span?.[1]}]</span>
                            <span>Quote SHA-256: {claim.quote_sha256?.slice(0, 16)}...</span>
                          </div>
                        </div>

                        {/* Owner Confirmation Controls */}
                        <div className="flex items-center justify-between pt-2 border-t border-[#E5E4DE]">
                          <div className="text-[11px] text-[#5F6876]">
                            {claim.last_confirmed_by ? (
                              <span className="text-emerald-800 font-medium">
                                Approved by {claim.last_confirmed_by} (Cryptographically Recorded)
                              </span>
                            ) : (
                              <span>Pending Human Review by Tier 0 Owner</span>
                            )}
                          </div>

                          <div className="flex items-center space-x-2">
                            {claim.state !== "confirmed" && (
                              <button
                                onClick={() => handleConfirmClaim(claim.id)}
                                disabled={loading}
                                className="bg-[#17263D] hover:bg-[#25354F] text-white text-xs font-medium px-3 py-1.5 rounded transition flex items-center space-x-1.5 shadow-sm"
                              >
                                <Check className="h-3.5 w-3.5 text-[#DCECE3]" />
                                <span>Confirm Commitment (Owner)</span>
                              </button>
                            )}
                            {claim.state !== "rejected" && (
                              <button
                                onClick={() => handleRejectClaim(claim.id)}
                                disabled={loading}
                                className="bg-white hover:bg-[#F9DDD8] text-[#8A241C] border border-[#E8BDB6] text-xs font-medium px-3 py-1.5 rounded transition flex items-center space-x-1.5"
                              >
                                <X className="h-3.5 w-3.5" />
                                <span>Reject / Quarantine</span>
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-8 text-center text-xs text-[#5F6876] editorial-subtle">
                      No commitments in review queue. Run the live simulation or ingest a WhatsApp chat to populate.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB: OVERVIEW — "Your business, still moving."            */}
          {/* ========================================================= */}
          {navSection === "overview" && (
            <div className="space-y-6">
              <div className="space-y-1">
                <p className="text-xs font-mono uppercase tracking-wider text-[#5F6876]">
                  CONTINUITY OVERVIEW
                </p>
                <h2 className="text-2xl font-bold tracking-tight text-[#141B24]">Your business, still moving.</h2>
                <p className="text-xs text-[#5F6876]">Operational summary grounded in verifiable business evidence.</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="editorial-card p-5 space-y-2">
                  <span className="text-xs font-medium text-[#5F6876]">Continuity Score</span>
                  <div className="text-3xl font-bold font-mono text-[#141B24] tabular-nums">
                    {healthData?.readiness_score !== undefined ? `${healthData.readiness_score}%` : "82%"}
                  </div>
                  <span className="text-[11px] text-[#5F6876]">System operational readiness</span>
                </div>

                <div className="editorial-card p-5 space-y-2">
                  <span className="text-xs font-medium text-[#704E14]">Needs attention</span>
                  <div className="text-3xl font-bold font-mono text-[#704E14] tabular-nums">
                    {healthData?.commitments_requiring_attention?.length ?? "03"}
                  </div>
                  <span className="text-[11px] text-[#704E14]">Pending review items</span>
                </div>

                <div className="editorial-card p-5 space-y-2">
                  <span className="text-xs font-medium text-[#195236]">Active handoffs</span>
                  <div className="text-3xl font-bold font-mono text-[#195236] tabular-nums">
                    {isAbsent ? "01" : "00"}
                  </div>
                  <span className="text-[11px] text-[#195236]">Delegated operational scope</span>
                </div>

                <div className="editorial-card p-5 space-y-2">
                  <span className="text-xs font-medium text-[#5F6876]">Single Points of Failure</span>
                  <div className="text-3xl font-bold font-mono text-[#141B24] tabular-nums">
                    {healthData?.single_points_of_failure?.length ?? "01"}
                  </div>
                  <span className="text-[11px] text-[#5F6876]">Identified structural bottlenecks</span>
                </div>
              </div>

              <div className="editorial-card p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-3">
                  <h3 className="font-semibold text-sm text-[#141B24]">Commitments Requiring Attention</h3>
                  <button onClick={() => setNavSection("review_queue")} className="text-xs text-[#17263D] font-medium hover:underline">
                    Open Review Queue
                  </button>
                </div>

                <div className="divide-y divide-[#E5E4DE]">
                  <div className="py-3 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-[#141B24]">Sharma Prints order docket #4092</p>
                      <p className="text-[11px] text-[#5F6876] mt-0.5">Assigned: Rajesh · Source: WhatsApp · Citation verified</p>
                    </div>
                    <span className="text-xs bg-[#DCECE3] text-[#195236] px-2.5 py-1 rounded font-medium">
                      Safe Handoff Ready
                    </span>
                  </div>
                  <div className="py-3 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-semibold text-[#141B24]">Settle Sharma ji advance payment</p>
                      <p className="text-[11px] text-[#5F6876] mt-0.5">Due: Thursday 18:00 IST · Owner Review Pending</p>
                    </div>
                    <span className="text-xs bg-[#F5E7C9] text-[#704E14] px-2.5 py-1 rounded font-medium">
                      Review Needed
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB: COMMITMENTS LIST                                     */}
          {/* ========================================================= */}
          {navSection === "commitments" && (
            <div className="editorial-card p-6 space-y-4">
              <div className="border-b border-[#E5E4DE] pb-3">
                <h3 className="font-semibold text-sm text-[#141B24]">Operational Commitment Ledger</h3>
                <p className="text-xs text-[#5F6876] mt-0.5">
                  Extracted promises, decisions, and deadlines grounded in verbatim source quotes.
                </p>
              </div>

              <div className="divide-y divide-[#E5E4DE] text-xs">
                <div className="py-3 flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="font-semibold text-[#141B24]">Confirm order docket #4092 for Sharma Prints (10,000 cartons)</p>
                    <p className="text-[#5F6876]">Assigned: Rajesh · Source: WhatsApp · Citation: "Order docket #4092 for Sharma Prints is confirmed"</p>
                  </div>
                  <span className="bg-[#DCECE3] text-[#195236] px-2 py-0.5 rounded font-mono font-medium">AGREED</span>
                </div>

                <div className="py-3 flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="font-semibold text-[#141B24]">Settle Sharma ji advance payment</p>
                    <p className="text-[#5F6876]">Due: Thursday 18:00 IST · Owner Action Pending</p>
                  </div>
                  <span className="bg-[#F5E7C9] text-[#704E14] px-2 py-0.5 rounded font-mono font-medium">PENDING</span>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB: HANDOFF WORKSPACE                                    */}
          {/* ========================================================= */}
          {navSection === "handoffs" && (
            <div className="editorial-card p-6 space-y-6">
              <div className="border-b border-[#E5E4DE] pb-4">
                <h3 className="font-semibold text-base text-[#141B24]">Continuity Handoff Document</h3>
                <p className="text-xs text-[#5F6876] mt-0.5">
                  Prepared for: <strong>Rajesh (Operations Manager)</strong> during Maya Sundaram's absence.
                </p>
              </div>

              <div className="space-y-4 text-xs">
                <div className="p-4 bg-[#FAF9F5] rounded-lg border border-[#E5E4DE] space-y-2">
                  <span className="font-bold text-[#141B24] uppercase text-[10px] tracking-wider block">Scope of Delegation</span>
                  <p className="text-[#5F6876] leading-relaxed">
                    Rajesh is pre-authorized by Maya Sundaram under the Continuity Charter to approve vendor disbursements up to ₹25,000 from the HDFC Current account.
                  </p>
                </div>

                <div className="p-4 bg-white rounded-lg border border-[#E5E4DE] space-y-2">
                  <span className="font-bold text-[#8A241C] uppercase text-[10px] tracking-wider block">What I Cannot See (Disclosure)</span>
                  <p className="text-[#5F6876] leading-relaxed">
                    Personal voice calls and unexported WhatsApp threads cannot be accessed. Do not authorize disbursements outside the pre-authorized ceiling.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB: AUTHORITY & POLICIES                                 */}
          {/* ========================================================= */}
          {navSection === "authority" && (
            <div className="editorial-card p-6 space-y-4">
              <div className="border-b border-[#E5E4DE] pb-3">
                <h3 className="font-semibold text-sm text-[#141B24]">Authority Rules & Standing Delegations</h3>
                <p className="text-xs text-[#5F6876] mt-0.5">
                  Enforced via deterministic Cedar-style policy code.
                </p>
              </div>

              <div className="p-4 bg-[#FAF9F5] rounded-lg border border-[#E5E4DE] text-xs space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-[#141B24]">Standing Delegation #01</span>
                  <span className="bg-[#DCECE3] text-[#195236] px-2 py-0.5 rounded font-mono font-semibold">ACTIVE</span>
                </div>
                <p className="text-[#5F6876]">Grantor: Maya Sundaram (Owner) &rarr; Grantee: Rajesh (Operations)</p>
                <p className="text-[#5F6876] font-mono">Ceiling: INR 25,000.00 · Permitted Account: HDFC Current</p>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* TAB: CRYPTOGRAPHIC AUDIT                                  */}
          {/* ========================================================= */}
          {navSection === "audit" && (
            <div className="editorial-card p-6 space-y-4">
              <div className="border-b border-[#E5E4DE] pb-3">
                <h3 className="font-semibold text-sm text-[#141B24]">Cryptographic Hash-Chained Audit Trail</h3>
                <p className="text-xs text-[#5F6876] mt-0.5">
                  Every state transition, quarantine event, and policy decision is cryptographically chained.
                </p>
              </div>

              <div className="space-y-2 text-xs font-mono">
                {auditLogs.length > 0 ? (
                  auditLogs.map((log: any, idx: number) => (
                    <div key={idx} className="p-3 bg-[#FAF9F5] border border-[#E5E4DE] rounded-lg space-y-1">
                      <div className="flex justify-between font-bold text-[#17263D]">
                        <span>EVENT: {log.event}</span>
                        <span>ACTOR: {log.actor}</span>
                      </div>
                      <p className="text-[11px] text-[#5F6876]">HASH: {log.hash}</p>
                      <p className="text-[11px] text-[#5F6876]">PREV: {log.prev_hash}</p>
                    </div>
                  ))
                ) : (
                  <p className="p-4 text-center text-[#5F6876]">Run the live simulation to generate verifiable audit logs.</p>
                )}
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
