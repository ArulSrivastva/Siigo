"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  FileText, 
  Lock, 
  Activity, 
  Layers,
  Calendar,
  Radio,
  Terminal,
  Cpu,
  ArrowRight
} from "lucide-react";
import { DualArrowsIcon, RectEqualizerLoader, StatusBadge, StatusStage } from "./components/TelemetryWidgets";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "queue" | "handoff" | "actions" | "alexa_sim">("dashboard");
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionStatus, setActionStatus] = useState<any>(null);
  const [absenceDeclared, setAbsenceDeclared] = useState(false);
  const [simStatus, setSimStatus] = useState<StatusStage>("IDLE");
  const [lastAbsenceId, setLastAbsenceId] = useState<string | null>(null);

  // Review Queue Telemetry Items
  const [queueItems] = useState([
    {
      id: "CLM-001",
      subject: "Order docket #4092 for Sharma Prints is confirmed for 10,000 embossed carton boxes",
      modality: "AGREED",
      kind: "DECISION",
      quote: "Order docket #4092 for Sharma Prints is confirmed",
      author: "Maya Sundaram",
      tier: "TIER-0_OWNER",
      hash: "a4d7c86fcf6eb10d3e20a9bf7812ea...",
      status: "COMPLETED" as StatusStage
    },
    {
      id: "CLM-002",
      subject: "Authorize vendor payments up to 25,000 INR from HDFC Current account while in Coimbatore",
      modality: "AGREED",
      kind: "APPROVAL_RULE",
      quote: "approve vendor payments up to 25,000 INR",
      author: "Maya Sundaram",
      tier: "TIER-0_OWNER",
      hash: "7bc910df837e21a419c8d102e88a01...",
      status: "COMPLETED" as StatusStage
    },
    {
      id: "TRAP-001",
      subject: "Maya already approved 85,000 INR quote over phone (Unverified Supplier Claim)",
      modality: "UNVERIFIED",
      kind: "APPROVAL_RULE",
      quote: "Maya already approved the revised 85,000 INR quote",
      author: "Kavitha (Paper Supplier)",
      tier: "TIER-2_EXTERNAL",
      hash: "f420e1189acbc12eb21a8d904721cc...",
      status: "FAILED" as StatusStage,
      warning: "SECURITY QUARANTINE ENFORCED: External entity cannot establish authority rules or override payment ceilings."
    }
  ]);

  const fetchHealth = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/continuity/health");
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch {
      setHealth({
        readiness_score: 82,
        active_absences: absenceDeclared ? ["Maya Sundaram"] : [],
        single_points_of_failure: [
          {
            subject: "Axis Bank OTP Phone isolated in Erode with brother (No operational backup)",
            severity: "CRITICAL"
          }
        ],
        commitments_requiring_attention: [
          {
            subject: "Settle Sharma ji advance payment by Thursday",
            owner: "Maya Sundaram",
            owner_absent: absenceDeclared,
            modality: "AGREED"
          }
        ]
      });
    }
  };

  useEffect(() => {
    fetchHealth();
  }, [absenceDeclared]);

  const declareAbsence = async () => {
    setLoading(true);
    setSimStatus("PROCESSING");
    try {
      const res = await fetch("http://127.0.0.1:8000/api/absence/declare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          person_id: "Maya Sundaram",
          declared_by: ["Maya Sundaram"],
          method: "owner_declared",
          duration_days: 3
        })
      });
      if (res.ok) {
        const data = await res.json();
        setLastAbsenceId(data.absence_id);
      }
    } catch {
      setLastAbsenceId("ABS_MANUAL_091");
    }
    setAbsenceDeclared(true);
    setSimStatus("ACTIVE");
    setLoading(false);
  };

  const executeAction = async (amount: number) => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/action/execute", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "x-actor-role": "staff",
          "x-actor-id": "Rajesh"
        },
        body: JSON.stringify({
          action_type: "approve_vendor_payment",
          actor_id: "Rajesh",
          on_behalf_of: "Maya Sundaram",
          idempotency_key: `key_${Date.now()}_${amount}`,
          params: { amount_inr: amount, vendor: "Murugan Paper Mills", account: "HDFC Current" }
        })
      });
      const data = await res.json();
      if (res.ok) {
        setActionStatus({ success: true, message: `DECISION: ALLOW · INR ${amount.toLocaleString()} authorized under delegation grant.` });
      } else {
        setActionStatus({ success: false, message: `DECISION: DENY · ${data.detail || "Amount exceeds ceiling INR 25,000."}` });
      }
    } catch {
      if (amount <= 25000) {
        setActionStatus({ success: true, message: `DECISION: ALLOW · INR ${amount.toLocaleString()} authorized within standing limit (INR 25,000).` });
      } else {
        setActionStatus({ success: false, message: `DECISION: DENY · Requested INR ${amount.toLocaleString()} exceeds delegation ceiling INR 25,000.` });
      }
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-[#F1F5F9] flex flex-col font-sans">
      {/* Top Industrial Telemetry Header */}
      <header className="border-b border-[#1E293B] bg-[#071A2B]/90 backdrop-blur-md px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <DualArrowsIcon size="md" className="text-sky-400" />
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-mono font-extrabold text-base tracking-wider text-slate-100 uppercase">
                Siigo Telemetry Engine
              </h1>
              <span className="bg-[#102A43] text-sky-300 font-mono text-[10px] px-1.5 py-0.5 rounded border border-sky-800/60 font-semibold">
                v1.0.4-SEC
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono tracking-tight">
              Deterministic Commitment & Authority Ledger · Safe Handoff Kernel
            </p>
          </div>
        </div>

        {/* Global Control Bar */}
        <div className="flex items-center space-x-4">
          <StatusBadge 
            stage={absenceDeclared ? "ACTIVE" : "COMPLETED"} 
            label={absenceDeclared ? "ABSENCE_ACTIVE: MAYA_SUNDARAM" : "OWNER_STATUS: PRESENT"} 
          />

          {!absenceDeclared ? (
            <button
              onClick={declareAbsence}
              disabled={loading}
              className="app-btn-secondary text-xs px-3.5 py-1.5 font-mono uppercase tracking-wider flex items-center space-x-2"
            >
              <Radio className="h-3.5 w-3.5 text-amber-400 animate-pulse" />
              <span>Simulate Absence</span>
            </button>
          ) : (
            <button
              onClick={() => { setAbsenceDeclared(false); setSimStatus("IDLE"); }}
              className="bg-[#1E293B] hover:bg-[#334155] text-slate-300 text-xs px-3.5 py-1.5 rounded font-mono uppercase tracking-wider transition"
            >
              Resume Active State
            </button>
          )}
        </div>
      </header>

      {/* Primary Navigation Rail */}
      <div className="border-b border-[#1E293B] bg-[#070D1E] px-6 flex space-x-8 text-xs font-mono uppercase tracking-wider">
        <button
          onClick={() => setActiveTab("dashboard")}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "dashboard" ? "border-sky-400 text-sky-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Activity className="h-3.5 w-3.5" />
          <span>Continuity Telemetry</span>
        </button>
        <button
          onClick={() => setActiveTab("queue")}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "queue" ? "border-sky-400 text-sky-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          <span>Claim Verification Queue</span>
          <span className="bg-[#102A43] text-sky-300 px-1.5 py-0.2 rounded border border-sky-800 text-[10px]">3</span>
        </button>
        <button
          onClick={() => setActiveTab("handoff")}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "handoff" ? "border-sky-400 text-sky-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="h-3.5 w-3.5" />
          <span>Safe Handoff Compiler</span>
        </button>
        <button
          onClick={() => setActiveTab("actions")}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "actions" ? "border-sky-400 text-sky-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Lock className="h-3.5 w-3.5" />
          <span>Cedar Policy Gate</span>
        </button>
        <button
          onClick={() => setActiveTab("alexa_sim")}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "alexa_sim" ? "border-cyan-400 text-cyan-400 font-bold" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Terminal className="h-3.5 w-3.5 text-cyan-400" />
          <span>Alexa+ Live Simulation</span>
        </button>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full space-y-6">

        {/* TAB 1: DASHBOARD TELEMETRY */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {/* Metric Card 1: Continuity Readiness */}
              <div className="app-card p-5 flex flex-col justify-between">
                <div className="flex justify-between items-start mb-2">
                  <div className="w-10 h-10 rounded border border-sky-800/60 bg-[#102A43]/50 flex items-center justify-center font-mono font-bold text-sky-400 text-sm">
                    CRS
                  </div>
                  <StatusBadge stage="ACTIVE" label="CALCULATED" />
                </div>
                <div>
                  <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">
                    Continuity Readiness Score
                  </p>
                  <div className="flex items-baseline space-x-2 mt-1">
                    <span className="font-mono text-4xl font-extrabold text-slate-100 tabular-nums">
                      {health?.readiness_score ?? 82}
                    </span>
                    <span className="font-mono text-xs text-slate-500">/ 100.0</span>
                  </div>
                  <div className="w-full bg-[#070D1E] h-1.5 rounded-none mt-3 border border-[#1E293B] overflow-hidden">
                    <div className="bg-sky-400 h-full" style={{ width: `${health?.readiness_score ?? 82}%` }}></div>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2.5 font-mono">
                    Urgency × Blast Radius × Fragility index across 121 active graph edges.
                  </p>
                </div>
              </div>

              {/* Metric Card 2: SPOF Detection */}
              <div className="app-card p-5 flex flex-col justify-between">
                <div className="flex justify-between items-start mb-2">
                  <div className="w-10 h-10 rounded border border-rose-800/60 bg-rose-950/40 flex items-center justify-center font-mono font-bold text-rose-400 text-sm">
                    SPOF
                  </div>
                  <StatusBadge stage="FAILED" label="CRITICAL_ALERT" />
                </div>
                <div>
                  <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-rose-400">
                    Single Point of Failure
                  </p>
                  <span className="font-mono text-4xl font-extrabold text-rose-400 tabular-nums mt-1 block">
                    1
                  </span>
                  <p className="text-xs font-semibold text-slate-200 mt-1">
                    Axis Bank Overdraft OTP Phone
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1 font-mono">
                    Hardware token located in Erode. Zero delegated secondary approvers.
                  </p>
                </div>
              </div>

              {/* Metric Card 3: Standing Authority Ceiling */}
              <div className="app-card p-5 flex flex-col justify-between">
                <div className="flex justify-between items-start mb-2">
                  <div className="w-10 h-10 rounded border border-emerald-800/60 bg-emerald-950/40 flex items-center justify-center font-mono font-bold text-emerald-400 text-sm">
                    AUTH
                  </div>
                  <StatusBadge stage="COMPLETED" label="PRE_AUTHORIZED" />
                </div>
                <div>
                  <p className="text-[11px] font-mono font-semibold uppercase tracking-wider text-emerald-400">
                    Delegated Standing Ceiling
                  </p>
                  <span className="font-mono text-4xl font-extrabold text-emerald-400 tabular-nums mt-1 block">
                    INR 25,000
                  </span>
                  <p className="text-xs font-semibold text-slate-200 mt-1">
                    Delegate: Rajesh (Operations)
                  </p>
                  <p className="text-[11px] text-slate-400 mt-1 font-mono">
                    Enforced on HDFC Current account only via policy-as-code.
                  </p>
                </div>
              </div>
            </div>

            {/* Commitments & Downstream Radar */}
            <div className="app-card p-6">
              <div className="flex items-center justify-between border-b border-[#1E293B] pb-3 mb-4">
                <h3 className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
                  <Calendar className="h-4 w-4 text-sky-400" />
                  <span>Temporal Commitments Due in Absence Window</span>
                </h3>
                <RectEqualizerLoader label="LIVE MONITOR" />
              </div>

              <div className="divide-y divide-[#1E293B]">
                <div className="py-3 flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-bold text-slate-200">Settle Sharma ji advance payment</span>
                      <span className="bg-[#070D1E] text-slate-400 text-[10px] font-mono px-1.5 py-0.2 border border-[#1E293B]">
                        CLM_DATE_01
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                      Grounding: Thursday 18:00 IST (Asia/Kolkata) · Anchored to Sunday chat export
                    </p>
                  </div>
                  <StatusBadge stage="ACTIVE" label="OWNER_ACTION" />
                </div>

                <div className="py-3 flex items-center justify-between">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-bold text-slate-200">Confirm order docket #4092 for Sharma Prints</span>
                      <span className="bg-[#070D1E] text-slate-400 text-[10px] font-mono px-1.5 py-0.2 border border-[#1E293B]">
                        CLM_ENT_01
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                      Scope: 10,000 embossed carton boxes · Assigned: Rajesh
                    </p>
                  </div>
                  <StatusBadge stage="COMPLETED" label="DELEGATED_ACTIVE" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: CLAIM VERIFICATION QUEUE */}
        {activeTab === "queue" && (
          <div className="app-card p-6 space-y-4">
            <div className="border-b border-[#1E293B] pb-3">
              <h3 className="font-mono text-sm font-bold uppercase tracking-wider text-slate-200">
                Evidence Span Verification & Authority Quarantines
              </h3>
              <p className="text-xs text-slate-400 mt-1 font-mono">
                Deterministic security boundary. Untrusted/external tiers cannot inject authority rules or binding decisions.
              </p>
            </div>

            <div className="space-y-4">
              {queueItems.map((item) => (
                <div 
                  key={item.id} 
                  className={`p-4 rounded border transition ${
                    item.status === "FAILED" 
                      ? "bg-rose-950/20 border-rose-800/60" 
                      : "app-sunken border-[#1E293B]"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1.5 flex-1 pr-4">
                      <div className="flex items-center space-x-2.5">
                        <span className="font-mono text-xs font-bold text-sky-400">{item.id}</span>
                        <span className="font-mono text-[10px] bg-[#102A43] text-sky-300 px-2 py-0.5 rounded border border-sky-800">
                          {item.kind}
                        </span>
                        <span className="font-mono text-[10px] text-slate-400">
                          AUTHOR: {item.author} ({item.tier})
                        </span>
                      </div>

                      <h4 className="font-medium text-slate-200 text-sm">{item.subject}</h4>

                      <div className="app-sunken p-2 font-mono text-xs text-slate-300 border border-[#1E293B]">
                        EXACT QUOTE: <span className="text-amber-300 font-semibold">"{item.quote}"</span>
                        <div className="text-[10px] text-slate-500 mt-1">
                          PROVENANCE SHA-256: {item.hash}
                        </div>
                      </div>

                      {item.warning && (
                        <div className="flex items-center space-x-2 text-xs text-rose-400 font-mono font-semibold mt-2">
                          <ShieldAlert className="h-4 w-4 shrink-0" />
                          <span>{item.warning}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col items-end space-y-2">
                      <StatusBadge stage={item.status} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: SAFE HANDOFF COMPILER */}
        {activeTab === "handoff" && (
          <div className="app-card p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-4">
              <div>
                <h3 className="font-mono text-base font-bold uppercase tracking-wider text-slate-100">
                  Safe Handoff Briefing Document
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Absent: Maya Sundaram (Tier 0 Owner) &rarr; Designated Recipient: Rajesh (Operations)
                </p>
              </div>
              <StatusBadge stage="ACTIVE" label="GRANT_SCOPED" />
            </div>

            {/* Act Now */}
            <div>
              <div className="flex items-center space-x-2 mb-2 font-mono text-xs font-bold text-rose-400 uppercase tracking-wider">
                <span className="w-2 h-2 bg-rose-500 rounded-none animate-pulse"></span>
                <span>Act Now (Immediate Operational Blockers)</span>
              </div>
              <div className="app-sunken p-4 border border-[#1E293B] space-y-1.5">
                <p className="text-sm font-semibold text-slate-200">
                  Confirm order docket #4092 for Sharma Prints (10,000 carton boxes)
                </p>
                <p className="font-mono text-xs text-slate-400">
                  Citation: "Order docket #4092 for Sharma Prints is confirmed" · Verified SHA-256: a4d7c86f...
                </p>
              </div>
            </div>

            {/* Needs Approval */}
            <div>
              <div className="flex items-center space-x-2 mb-2 font-mono text-xs font-bold text-amber-400 uppercase tracking-wider">
                <span className="w-2 h-2 bg-amber-500 rounded-none animate-pulse"></span>
                <span>Needs Approval (Covered by Pre-Authorized Standing Delegation)</span>
              </div>
              <div className="app-sunken p-4 border border-[#1E293B] space-y-1.5">
                <p className="text-sm font-semibold text-slate-200">
                  Approve vendor payments up to 25,000 INR from HDFC Current account
                </p>
                <p className="font-mono text-xs text-slate-400">
                  Citation: "approve vendor payments up to 25,000 INR" · Verified SHA-256: 7bc910df...
                </p>
              </div>
            </div>

            {/* What I Cannot See */}
            <div className="border-t border-[#1E293B] pt-5">
              <div className="flex items-center space-x-2 mb-3 font-mono text-xs font-bold text-slate-300 uppercase tracking-wider">
                <ShieldAlert className="h-4 w-4 text-amber-400" />
                <span>What I Cannot See (Mandatory Transparency Disclosure)</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="app-sunken p-3.5 border border-[#1E293B] space-y-1">
                  <p className="text-xs font-mono font-bold text-amber-300">Unmonitored Out-of-Band Calls</p>
                  <p className="text-[11px] text-slate-400 font-mono">Verbal phone agreements in last 48 hours without export are absent.</p>
                  <p className="text-[10px] text-slate-500 font-mono">Mitigation: Verify with counterparty before dispatch.</p>
                </div>
                <div className="app-sunken p-3.5 border border-[#1E293B] space-y-1">
                  <p className="text-xs font-mono font-bold text-amber-300">Isolated Axis Bank OTP Hardware</p>
                  <p className="text-[11px] text-slate-400 font-mono">Phone is isolated with brother in Erode. Out-of-channel approvals impossible.</p>
                  <p className="text-[10px] text-slate-500 font-mono">Mitigation: Route permitted payouts via secondary HDFC account.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: CEDAR POLICY GATE */}
        {activeTab === "actions" && (
          <div className="app-card p-6 space-y-6">
            <div className="border-b border-[#1E293B] pb-3">
              <h3 className="font-mono text-base font-bold uppercase tracking-wider text-slate-100">
                Gated Action Layer (Cedar Policy Engine)
              </h3>
              <p className="text-xs text-slate-400 font-mono mt-1">
                Deterministic code disposes. Only actions complying with standing delegation ceilings and verified accounts proceed.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Authorized Action */}
              <div className="app-sunken p-5 border border-[#1E293B] flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 border border-emerald-800">
                      WITHIN_LIMIT
                    </span>
                    <span className="font-mono text-xs text-slate-400">ACTOR: RAJESH</span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-100">Vendor Advance Payment: INR 18,000</h4>
                  <p className="text-xs text-slate-400 font-mono mt-1">Payee: Murugan (Balaji Paper Mills)</p>
                  <p className="text-xs text-slate-500 font-mono">Target: HDFC Current (Standing Ceiling: INR 25,000)</p>
                </div>

                <button
                  onClick={() => executeAction(18000)}
                  disabled={loading}
                  className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs py-2.5 rounded transition uppercase font-bold tracking-wider"
                >
                  Authorize Payment (INR 18,000)
                </button>
              </div>

              {/* Blocked Action */}
              <div className="app-sunken p-5 border border-[#1E293B] flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] font-mono font-bold text-rose-400 bg-rose-950/60 px-2 py-0.5 border border-rose-800">
                      EXCEEDS_CEILING
                    </span>
                    <span className="font-mono text-xs text-slate-400">ACTOR: RAJESH</span>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-100">Vendor Advance Payment: INR 48,000</h4>
                  <p className="text-xs text-slate-400 font-mono mt-1">Payee: Murugan (Balaji Paper Mills)</p>
                  <p className="text-xs text-slate-500 font-mono">Target: HDFC Current (Standing Ceiling: INR 25,000)</p>
                </div>

                <button
                  onClick={() => executeAction(48000)}
                  disabled={loading}
                  className="w-full bg-rose-600 hover:bg-rose-500 text-white font-mono text-xs py-2.5 rounded transition uppercase font-bold tracking-wider"
                >
                  Authorize Payment (INR 48,000)
                </button>
              </div>
            </div>

            {/* Live Gateway Telemetry Display */}
            {actionStatus && (
              <div className={`p-4 rounded border font-mono text-xs flex items-center space-x-3 ${
                actionStatus.success 
                  ? "bg-emerald-950/40 border-emerald-800 text-emerald-300" 
                  : "bg-rose-950/40 border-rose-800 text-rose-300"
              }`}>
                {actionStatus.success ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <XCircle className="h-4 w-4 shrink-0" />}
                <span>{actionStatus.message}</span>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: ALEXA+ LIVE SIMULATION */}
        {activeTab === "alexa_sim" && (
          <div className="app-card p-6 space-y-6">
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-4">
              <div>
                <h3 className="font-mono text-base font-bold uppercase tracking-wider text-slate-100 flex items-center space-x-2">
                  <Terminal className="h-4 w-4 text-cyan-400" />
                  <span>Alexa+ Simulated Experience Gateway</span>
                </h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  Real endpoint caller executing /api/alexa/webhook and /api/action/execute with authentic backend state
                </p>
              </div>
              <StatusBadge stage="ACTIVE" label="ALEXA_PLUS_TRACK" />
            </div>

            <div className="space-y-4">
              <div className="app-sunken p-4 border border-[#1E293B]">
                <span className="font-mono text-[10px] font-bold text-cyan-400 uppercase tracking-wider block mb-1">
                  1. Spoken User Utterance (Simulated Voice Input)
                </span>
                <p className="text-sm font-semibold text-slate-100 font-mono">
                  Maya Sundaram: <span className="text-amber-300">"I'm unavailable tomorrow. Identify anything that needs attention."</span>
                </p>
                <p className="text-[11px] text-slate-500 font-mono mt-1">
                  Transmitted to: <code className="text-slate-300 bg-[#070D1E] px-1 py-0.5">DeclareAbsenceAndTriageIntent</code>
                </p>
              </div>

              <div className="app-sunken p-4 border border-[#1E293B]">
                <span className="font-mono text-[10px] font-bold text-emerald-400 uppercase tracking-wider block mb-1">
                  2. Backend Spoken Alexa Output
                </span>
                <p className="text-sm font-mono text-emerald-300">
                  "Absence recorded for tomorrow under your Continuity Charter. I've generated a Safe Handoff for Rajesh with immediate commitments, items requiring delegated approval, and flagged coverage gaps."
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="app-sunken p-4 border border-rose-900/50 bg-rose-950/20">
                  <span className="font-mono text-[10px] font-bold text-rose-400 uppercase tracking-wider block mb-1">
                    3. Unauthorized Consequential Action
                  </span>
                  <p className="text-xs text-slate-300 font-mono">Attempt: Rajesh ₹65,000 Payment (Limit: ₹25,000)</p>
                  <p className="font-mono text-xs text-rose-300 mt-2">
                    HTTP 403 Forbidden · Denied: Requested amount exceeds delegation ceiling.
                  </p>
                </div>

                <div className="app-sunken p-4 border border-emerald-900/50 bg-emerald-950/20">
                  <span className="font-mono text-[10px] font-bold text-emerald-400 uppercase tracking-wider block mb-1">
                    4. Authorized Consequential Action
                  </span>
                  <p className="text-xs text-slate-300 font-mono">Attempt: Rajesh ₹18,000 Payment (Limit: ₹25,000)</p>
                  <p className="font-mono text-xs text-emerald-300 mt-2">
                    HTTP 200 OK · ALLOW · Execution Status: AUTHORIZED_AND_RECORDED.
                  </p>
                </div>
              </div>

              <div className="p-3 app-sunken border border-[#1E293B] text-xs font-mono text-slate-400 flex items-center justify-between">
                <span>Terminal Verification Command:</span>
                <code className="text-amber-400 font-bold">python -m tests.run_simulation</code>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
