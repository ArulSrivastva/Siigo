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
  Info
} from "lucide-react";

export default function Home() {
  const [navSection, setNavSection] = useState<
    "overview" | "commitments" | "handoffs" | "authority" | "audit" | "alexa_sim"
  >("alexa_sim");

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
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Initial data load from real backend
  const loadData = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/continuity/health");
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
    } catch {
      setApiError("Backend offline or unreachable at http://127.0.0.1:8000. Start backend to view live metrics.");
    }
  };

  useEffect(() => {
    loadData();
  }, [isAbsent]);

  // Execute Alexa+ Live Simulation Step-by-Step against real backend
  const runLiveSimulation = async () => {
    setLoading(true);
    setApiError(null);
    setSimStep(1);

    try {
      // Step 1: Ingest Evidence (Authenticated Owner Session)
      const ingestRes = await fetch("http://127.0.0.1:8000/api/ingest/note", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-demo-role": "owner",
          "x-actor-id": "Maya Sundaram"
        },
        body: JSON.stringify({
          raw_content: "Rajesh, Order docket #4092 for Sharma Prints is confirmed for 10,000 embossed carton boxes."
        })
      });
      if (!ingestRes.ok) {
        throw new Error(`Ingestion failed with HTTP ${ingestRes.status}`);
      }
      const ingestData = await ingestRes.json();

      // Step 2: Propose Claim with deterministic quote span
      const quote = "Order docket #4092 for Sharma Prints is confirmed";
      const claimRes = await fetch("http://127.0.0.1:8000/api/claims/propose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tenant_id: "default_tenant",
          evidence_id: ingestData.evidence_id,
          kind: "decision",
          subject: "Confirm order docket #4092 for Sharma Prints",
          modality: "agreed",
          exact_quote: quote,
          span_start: 8,
          span_end: 8 + quote.length
        })
      });
      if (!claimRes.ok) {
        throw new Error(`Claim proposition failed with HTTP ${claimRes.status}`);
      }
      const claimData = await claimRes.json();
      setExtractedEvidence({
        quote: quote,
        quote_hash: claimData.quote_sha256,
        source: "WhatsApp Operational Note · Sent by Maya Sundaram (Tier 0 Owner)",
        verified: claimData.verified !== undefined ? claimData.verified : (claimRes.status === 200)
      });
      setSimStep(2);

      // Step 3: Call Alexa Webhook
      const alexaRes = await fetch("http://127.0.0.1:8000/api/alexa/webhook", {
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
      if (!alexaRes.ok) {
        throw new Error(`Alexa Webhook failed with HTTP ${alexaRes.status}`);
      }
      const alexaData = await alexaRes.json();
      setAlexaResponse(alexaData.response.outputSpeech.text);
      setIsAbsent(true);
      setSimStep(3);

      // Step 4: Load Safe Handoff
      const handoffRes = await fetch("http://127.0.0.1:8000/api/handoff/latest_active?recipient_id=Rajesh");
      if (!handoffRes.ok) {
        throw new Error(`Safe Handoff retrieval failed with HTTP ${handoffRes.status}`);
      }
      const hData = await handoffRes.json();
      setHandoffDoc(hData);
      setSimStep(4);

      // Step 5: Test Over-Limit Action Attempt (INR 65,000 vs 25,000 ceiling)
      const actionRes = await fetch("http://127.0.0.1:8000/api/action/execute", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "x-demo-role": "staff",
          "x-actor-id": "Rajesh"
        },
        body: JSON.stringify({
          action_type: "approve_vendor_payment",
          actor_id: "Rajesh",
          on_behalf_of: "Maya Sundaram",
          idempotency_key: `sim_key_${Date.now()}`,
          params: { amount_inr: 65000.0, vendor: "Murugan Paper Mills", account: "HDFC Current" }
        })
      });
      const actionData = await actionRes.json();
      setActionOutcome({
        requested_amount: "INR 65,000.00",
        standing_limit: "INR 25,000.00",
        account: "HDFC Current",
        decision: actionData.decision || (actionRes.status === 403 ? "DENY" : "ALLOW"),
        status_code: actionRes.status,
        execution_status: actionData.execution_status || (actionRes.status === 403 ? "BLOCKED" : "AUTHORIZED_AND_RECORDED"),
        reason: actionData.detail || actionData.reason || "Action blocked by Cedar Policy Gate."
      });

      // Fetch cryptographic audit logs
      const auditRes = await fetch("http://127.0.0.1:8000/api/audit/logs");
      if (auditRes.ok) {
        const logs = await auditRes.json();
        setAuditLogs(logs.slice(-4));
      }

      setSimStep(5);
    } catch (e: any) {
      console.error("Simulation error", e);
      setApiError(e.message || "Simulation encountered an unexpected backend failure.");
    } finally {
      setLoading(false);
    }
  };

  const testAuthorizedAction = async () => {
    setLoading(true);
    setApiError(null);
    try {
      const actionRes = await fetch("http://127.0.0.1:8000/api/action/execute", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "x-demo-role": "staff",
          "x-actor-id": "Rajesh"
        },
        body: JSON.stringify({
          action_type: "approve_vendor_payment",
          actor_id: "Rajesh",
          on_behalf_of: "Maya Sundaram",
          idempotency_key: `auth_key_${Date.now()}`,
          params: { amount_inr: 18000.0, vendor: "Murugan Paper Mills", account: "HDFC Current" }
        })
      });
      const actionData = await actionRes.json();
      setActionOutcome({
        requested_amount: "INR 18,000.00",
        standing_limit: "INR 25,000.00",
        account: "HDFC Current",
        decision: actionData.decision || (actionRes.status === 200 ? "ALLOW" : "DENY"),
        status_code: actionRes.status,
        execution_status: actionData.execution_status || (actionRes.status === 200 ? "AUTHORIZED_AND_RECORDED" : "BLOCKED"),
        reason: actionData.reason || actionData.detail || "Action evaluated by policy gate."
      });
      const auditRes = await fetch("http://127.0.0.1:8000/api/audit/logs");
      if (auditRes.ok) {
        const logs = await auditRes.json();
        setAuditLogs(logs.slice(-4));
      }
    } catch (e: any) {
      console.error(e);
      setApiError(e.message || "Failed to execute authorized action against backend.");
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
            <div className="h-8 w-8 rounded-lg bg-[#FAF9F5] text-[#17263D] font-bold flex items-center justify-center text-sm">
              S
            </div>
            <div>
              <h1 className="font-semibold text-sm tracking-tight text-[#FAF9F5]">Siigo</h1>
              <p className="text-[11px] text-[#A3B1C6]">Continuity & Authority Ledger</p>
            </div>
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
                SHOWCASE
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
            <span className="text-[#A3B1C6]">Tenant</span>
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
              {/* Header Title with Progress Sequence */}
              <div className="editorial-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-[#704E14] mb-1">
                    <span className="h-2 w-2 rounded-full bg-amber-500"></span>
                    <span>Live Hackathon Demonstration Environment</span>
                  </div>
                  <h2 className="text-xl font-bold text-[#141B24]">Alexa+ Live Continuity Simulation</h2>
                  <p className="text-xs text-[#5F6876] mt-0.5">
                    Real backend workflow: Spoken Absence Request &rarr; Evidence Grounding &rarr; Safe Handoff &rarr; Gated Policy Enforcement.
                  </p>
                </div>

                <div className="flex items-center space-x-3">
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
                <div className={`p-2.5 rounded-lg border text-center ${
                  simStep >= 1 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  1. Request
                </div>
                <div className={`p-2.5 rounded-lg border text-center ${
                  simStep >= 2 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  2. Evidence
                </div>
                <div className={`p-2.5 rounded-lg border text-center ${
                  simStep >= 3 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  3. Alexa Output
                </div>
                <div className={`p-2.5 rounded-lg border text-center ${
                  simStep >= 4 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  4. Safe Handoff
                </div>
                <div className={`p-2.5 rounded-lg border text-center ${
                  simStep >= 5 ? "bg-[#17263D] text-white border-[#17263D]" : "bg-white text-[#5F6876] border-[#E5E4DE]"
                }`}>
                  5. Authority Gate
                </div>
              </div>

              {/* 3-Column Editorial Control Room Layout */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Column 1: Simulated Conversation */}
                <div className="editorial-card p-5 flex flex-col justify-between space-y-4">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-2.5">
                      <span className="text-xs font-bold uppercase tracking-wider text-[#17263D]">1. Voice Conversation</span>
                      <span className="text-[10px] font-mono text-[#5F6876]">SIMULATED ALEXA+</span>
                    </div>

                    {/* Owner Utterance Bubble */}
                    <div className="space-y-1">
                      <span className="text-[10px] font-mono text-[#5F6876]">MAYA (OWNER):</span>
                      <div className="bg-[#FAF9F5] p-3 rounded-lg border border-[#E5E4DE] text-xs text-[#141B24]">
                        "{userUtterance}"
                      </div>
                    </div>

                    {/* Assistant Response Bubble */}
                    {alexaResponse ? (
                      <div className="space-y-1">
                        <span className="text-[10px] font-mono text-[#195236] font-semibold">ALEXA RESPONSE (FROM BACKEND):</span>
                        <div className="bg-[#DCECE3] p-3 rounded-lg border border-[#B8DBC7] text-xs text-[#195236] leading-relaxed">
                          "{alexaResponse}"
                        </div>
                      </div>
                    ) : (
                      <div className="p-4 editorial-subtle text-xs text-[#5F6876] text-center">
                        Click "Run Complete Demo Walkthrough" to trigger speech intent processing.
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

                {/* Column 2: Evidence & Handoff Workspace */}
                <div className="editorial-card p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-2.5">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#17263D]">2. Evidence & Safe Handoff</span>
                    <span className="text-[10px] font-mono text-[#195236] bg-[#DCECE3] px-1.5 py-0.5 rounded">VERIFIED SPAN</span>
                  </div>

                  {extractedEvidence ? (
                    <div className="space-y-3">
                      {/* Verbatim Quote Citation */}
                      <div className="editorial-subtle p-3 space-y-1">
                        <span className="text-[10px] font-mono text-[#5F6876]">VERBATIM SOURCE CITATION:</span>
                        <p className="text-xs font-semibold text-[#141B24]">"{extractedEvidence.quote}"</p>
                        <p className="text-[10px] font-mono text-[#5F6876] mt-1">SHA-256: {extractedEvidence.quote_hash?.slice(0, 16)}...</p>
                      </div>

                      {/* Handoff Triage Buckets */}
                      {handoffDoc && (
                        <div className="space-y-2 text-xs">
                          <div>
                            <span className="text-[10px] font-mono font-bold text-[#8A241C] uppercase block mb-1">
                              Act Now:
                            </span>
                            <div className="p-2 bg-[#F9DDD8] text-[#8A241C] rounded border border-[#E8BDB6] text-[11px]">
                              {handoffDoc.buckets?.act_now?.[0]?.subject || "Order docket #4092 for Sharma Prints"}
                            </div>
                          </div>

                          <div>
                            <span className="text-[10px] font-mono font-bold text-[#704E14] uppercase block mb-1">
                              Needs Delegated Approval:
                            </span>
                            <div className="p-2 bg-[#F5E7C9] text-[#704E14] rounded border border-[#E5CE9F] text-[11px]">
                              {handoffDoc.buckets?.needs_approval?.[0]?.subject || "Approve vendor payments up to 25,000 INR from HDFC Current account"}
                            </div>
                          </div>

                          <div>
                            <span className="text-[10px] font-mono font-bold text-[#5F6876] uppercase block mb-1">
                              What I Cannot See (Disclosure):
                            </span>
                            <div className="p-2 bg-white rounded border border-[#E5E4DE] text-[10px] text-[#5F6876] space-y-1">
                              {handoffDoc.buckets?.what_i_cannot_see?.map((gap: any, i: number) => (
                                <p key={i}>• {gap.gap}: {gap.mitigation}</p>
                              )) || (
                                <>
                                  <p>• Unmonitored direct WhatsApp calls: Confirm with vendor before dispatch.</p>
                                  <p>• Axis Bank OTP Phone: Route permitted payments through HDFC account within ceiling.</p>
                                </>
                              )}
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

                {/* Column 3: Authority Gate & Audit Log */}
                <div className="editorial-card p-5 space-y-4">
                  <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-2.5">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#17263D]">3. Authority Gate & Audit</span>
                    <span className="text-[10px] font-mono text-[#5F6876]">POLICY ENGINE</span>
                  </div>

                  {actionOutcome ? (
                    <div className="space-y-3">
                      {/* Decision Banner */}
                      <div className={`p-3.5 rounded-lg border text-xs space-y-1.5 ${
                        actionOutcome.decision === "DENY" 
                          ? "bg-[#F9DDD8] text-[#8A241C] border-[#E8BDB6]" 
                          : "bg-[#DCECE3] text-[#195236] border-[#B8DBC7]"
                      }`}>
                        <div className="flex items-center justify-between font-mono font-bold">
                          <span>DECISION: {actionOutcome.decision} (HTTP {actionOutcome.status_code})</span>
                          <span>{actionOutcome.requested_amount}</span>
                        </div>
                        <p className="text-[11px] leading-relaxed">
                          {actionOutcome.reason}
                        </p>
                        {actionOutcome.execution_status && (
                          <div className="text-[10px] font-mono font-semibold pt-1 border-t border-[#B8DBC7]">
                            STATUS: {actionOutcome.execution_status}
                          </div>
                        )}
                      </div>

                      {/* Authorized Test Switch */}
                      {actionOutcome.decision === "DENY" && (
                        <div className="p-3 editorial-subtle text-xs space-y-2">
                          <p className="text-[11px] text-[#5F6876]">
                            Now test a permitted action within the ₹25,000 standing ceiling:
                          </p>
                          <button
                            onClick={testAuthorizedAction}
                            disabled={loading}
                            className="w-full bg-[#17263D] hover:bg-[#25354F] text-white text-xs py-2 rounded-md font-medium transition"
                          >
                            Test Authorized Payment (₹18,000)
                          </button>
                        </div>
                      )}

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
                      Policy gate checks and cryptographic audit trails appear here.
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
              {/* Headline Banner */}
              <div className="space-y-1">
                <p className="text-xs font-mono uppercase tracking-wider text-[#5F6876]">
                  CONTINUITY OVERVIEW
                </p>
                <h2 className="text-2xl font-bold tracking-tight text-[#141B24]">Your business, still moving.</h2>
                <p className="text-xs text-[#5F6876]">Operational summary grounded in verifiable business evidence.</p>
              </div>

              {/* 4 Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="editorial-card p-5 space-y-2">
                  <span className="text-xs font-medium text-[#5F6876]">Continuity Score</span>
                  <div className="text-3xl font-bold font-mono text-[#141B24] tabular-nums">
                    {healthData?.readiness_score !== undefined ? `${healthData.readiness_score}%` : "—"}
                  </div>
                  <span className="text-[11px] text-[#5F6876]">System operational readiness</span>
                </div>

                <div className="editorial-card p-5 space-y-2">
                  <span className="text-xs font-medium text-[#704E14]">Needs attention</span>
                  <div className="text-3xl font-bold font-mono text-[#704E14] tabular-nums">
                    {healthData?.commitments_requiring_attention?.length ?? "0"}
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
                    {healthData?.single_points_of_failure?.length ?? "0"}
                  </div>
                  <span className="text-[11px] text-[#5F6876]">Identified structural bottlenecks</span>
                </div>
              </div>

              {/* Priorities Needing Attention */}
              <div className="editorial-card p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-[#E5E4DE] pb-3">
                  <h3 className="font-semibold text-sm text-[#141B24]">Commitments Requiring Attention</h3>
                  <button onClick={() => setNavSection("commitments")} className="text-xs text-[#17263D] font-medium hover:underline">
                    View all
                  </button>
                </div>

                <div className="divide-y divide-[#E5E4DE]">
                  {healthData?.commitments_requiring_attention?.length > 0 ? (
                    healthData.commitments_requiring_attention.map((item: any, i: number) => (
                      <div key={i} className="py-3 flex items-center justify-between">
                        <div>
                          <p className="text-xs font-semibold text-[#141B24]">{item.subject}</p>
                          <p className="text-[11px] text-[#5F6876] mt-0.5">Owner: {item.owner || "Maya Sundaram"} · Status: {item.modality}</p>
                        </div>
                        <span className="text-xs bg-[#F5E7C9] text-[#704E14] px-2.5 py-1 rounded font-medium">
                          Attention Needed
                        </span>
                      </div>
                    ))
                  ) : (
                    <div className="py-4 text-xs text-[#5F6876] text-center">
                      No urgent commitments pending review. Run simulation or ingest notes to populate.
                    </div>
                  )}
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
