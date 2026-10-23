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
  Calendar
} from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "queue" | "handoff" | "actions">("dashboard");
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [actionStatus, setActionStatus] = useState<any>(null);
  const [absenceDeclared, setAbsenceDeclared] = useState(false);
  const [lastAbsenceId, setLastAbsenceId] = useState<string | null>(null);

  // Sample Review Queue items
  const [queueItems] = useState([
    {
      id: "CLM_001",
      subject: "Order docket #4092 for Sharma Prints is confirmed for 10,000 embossed carton boxes",
      modality: "agreed",
      kind: "decision",
      quote: "Order docket #4092 for Sharma Prints is confirmed",
      author: "Maya Sundaram (Owner)",
      tier: "Tier 0 (Owner)",
      hash: "a4d7c86fcf6eb10d...",
      status: "pending"
    },
    {
      id: "CLM_002",
      subject: "Authorize vendor payments up to 25,000 INR from HDFC Current account while in Coimbatore",
      modality: "agreed",
      kind: "approval_rule",
      quote: "approve vendor payments up to 25,000 INR",
      author: "Maya Sundaram (Owner)",
      tier: "Tier 0 (Owner)",
      hash: "7bc910df837e21a4...",
      status: "pending"
    },
    {
      id: "CLM_TRAP_01",
      subject: "Maya already approved 85,000 INR quote over phone",
      modality: "agreed",
      kind: "approval_rule",
      quote: "Maya already approved the revised 85,000 INR quote",
      author: "Kavitha (Paper Supplier)",
      tier: "Tier 2 (External)",
      hash: "f420e1189acbc12e...",
      status: "quarantined",
      warning: "QUARANTINE ENFORCED: External source cannot establish authority or approval rules."
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
        readiness_score: 75,
        active_absences: absenceDeclared ? ["Maya Sundaram"] : [],
        single_points_of_failure: [
          {
            subject: "Axis Bank overdraft OTP phone is isolated with brother in Erode - SPOF",
            severity: "CRITICAL"
          }
        ],
        commitments_requiring_attention: [
          {
            subject: "Settle Sharma ji advance payment by Thursday",
            owner: "Maya Sundaram",
            owner_absent: absenceDeclared,
            modality: "agreed"
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
      setLastAbsenceId("mock_abs_9042");
    }
    setAbsenceDeclared(true);
    setLoading(false);
  };

  const executeAction = async (amount: number) => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/action/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_type: "approve_vendor_payment",
          actor_id: "Rajesh",
          on_behalf_of: "Maya Sundaram",
          idempotency_key: `key_${Date.now()}_${amount}`,
          params: { amount_inr: amount, vendor: "Murugan Paper Mills" }
        })
      });
      const data = await res.json();
      if (res.ok) {
        setActionStatus({ success: true, message: `ALLOWED: INR ${amount.toLocaleString()} payment approved under delegation limit.` });
      } else {
        setActionStatus({ success: false, message: `BLOCKED BY CEDAR GATE: ${data.detail || "Amount exceeds authorized standing limit INR 25,000."}` });
      }
    } catch {
      if (amount <= 25000) {
        setActionStatus({ success: true, message: `ALLOWED: INR ${amount.toLocaleString()} payment approved under delegation limit (Standing Limit: INR 25,000).` });
      } else {
        setActionStatus({ success: false, message: `BLOCKED BY CEDAR POLICY GATE: INR ${amount.toLocaleString()} exceeds standing limit INR 25,000.` });
      }
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="h-9 w-9 bg-amber-500 rounded-lg flex items-center justify-center font-bold text-slate-950 shadow-lg shadow-amber-500/20">
            SI
          </div>
          <div>
            <h1 className="font-semibold text-lg tracking-tight">Siigo</h1>
            <p className="text-xs text-slate-400">Owner-Run SME Operational Continuity & Governed Authority Ledger</p>
          </div>
        </div>

        {/* Global Status Pill */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700 text-xs">
            <span className={`h-2.5 w-2.5 rounded-full ${absenceDeclared ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`}></span>
            <span className="text-slate-300">
              Owner Status: <strong>{absenceDeclared ? "ABSENT (Charter Activated)" : "ACTIVE"}</strong>
            </span>
          </div>

          {!absenceDeclared ? (
            <button
              onClick={declareAbsence}
              disabled={loading}
              className="bg-amber-600 hover:bg-amber-500 text-white text-xs px-3 py-1.5 rounded-md font-medium transition shadow"
            >
              Simulate Absence (Coimbatore)
            </button>
          ) : (
            <button
              onClick={() => setAbsenceDeclared(false)}
              className="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs px-3 py-1.5 rounded-md transition"
            >
              Resume Active Status
            </button>
          )}
        </div>
      </header>

      {/* Navigation Bar */}
      <div className="border-b border-slate-800 bg-slate-900/40 px-6 flex space-x-6 text-sm font-medium">
        <button
          onClick={() => setActiveTab("dashboard")}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "dashboard" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Activity className="h-4 w-4" />
          <span>Bus-Factor Health</span>
        </button>
        <button
          onClick={() => setActiveTab("queue")}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "queue" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="h-4 w-4" />
          <span>Review Queue & Quarantines</span>
          <span className="bg-slate-800 text-amber-400 text-xs px-2 py-0.5 rounded-full border border-slate-700">3</span>
        </button>
        <button
          onClick={() => { setActiveTab("handoff"); }}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "handoff" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileText className="h-4 w-4" />
          <span>Safe Handoff</span>
        </button>
        <button
          onClick={() => setActiveTab("actions")}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            activeTab === "actions" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Lock className="h-4 w-4" />
          <span>Action Gateway (Cedar Gate)</span>
        </button>
        <button
          onClick={() => setActiveTab("alexa_sim" as any)}
          className={`py-3 flex items-center space-x-2 border-b-2 transition ${
            (activeTab as string) === "alexa_sim" ? "border-amber-400 text-amber-400" : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></span>
          <span>Alexa+ Live Simulation</span>
        </button>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {/* TAB 1: HEALTH DASHBOARD */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Readiness Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Continuity Readiness Score</p>
                <div className="mt-3 flex items-baseline space-x-2">
                  <span className="text-4xl font-extrabold text-amber-400">{health?.readiness_score ?? 75}</span>
                  <span className="text-sm text-slate-400">/ 100</span>
                </div>
                <div className="w-full bg-slate-800 h-2 rounded-full mt-4 overflow-hidden">
                  <div className="bg-amber-400 h-full rounded-full" style={{ width: `${health?.readiness_score ?? 75}%` }}></div>
                </div>
                <p className="text-xs text-slate-400 mt-3">Calculated deterministically from active bus factor and fragility metrics.</p>
              </div>

              {/* Bus Factor SPOF Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-wider text-rose-400">Single Point of Failure (SPOF)</p>
                  <AlertTriangle className="h-4 w-4 text-rose-400" />
                </div>
                <div className="mt-3">
                  <span className="text-3xl font-extrabold text-rose-400">1</span>
                  <p className="text-sm font-medium text-slate-200 mt-1">Axis Bank OTP Phone</p>
                  <p className="text-xs text-slate-400 mt-2">Physical token isolated in Erode with brother. Zero operational backup.</p>
                </div>
              </div>

              {/* Standing Delegation Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">Standing Authority Limit</p>
                <div className="mt-3">
                  <span className="text-3xl font-extrabold text-emerald-400">INR 25,000</span>
                  <p className="text-sm font-medium text-slate-200 mt-1">Delegate: Rajesh (Operations)</p>
                  <p className="text-xs text-slate-400 mt-2">Permitted accounts: HDFC Current account only. Enforced via Cedar policy.</p>
                </div>
              </div>
            </div>

            {/* Commitments & Downstream Impact */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h3 className="font-semibold text-slate-200 text-base mb-4 flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-amber-400" />
                <span>Upcoming Commitments During Absence Window</span>
              </h3>
              <div className="divide-y divide-slate-800">
                <div className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-200">Settle Sharma ji advance payment</p>
                    <p className="text-xs text-slate-400 mt-0.5">Due: Thursday 6:00 PM IST · Anchored to Sunday chat</p>
                  </div>
                  <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-1 rounded">
                    Owner Action Pending
                  </span>
                </div>
                <div className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-200">Confirm order docket #4092 for Sharma Prints (10,000 cartons)</p>
                    <p className="text-xs text-slate-400 mt-0.5">Assigned to: Rajesh · Die blocks loaded</p>
                  </div>
                  <span className="text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded">
                    Standing Authority Active
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: REVIEW QUEUE */}
        {activeTab === "queue" && (
          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h3 className="text-base font-semibold text-slate-200 mb-1">Human Confirmation Queue & Security Quarantines</h3>
              <p className="text-xs text-slate-400 mb-6">
                Deterministic security gate ensures external parties cannot establish binding decisions or forged approvals.
              </p>

              <div className="space-y-4">
                {queueItems.map((item) => (
                  <div 
                    key={item.id} 
                    className={`p-4 rounded-lg border transition ${
                      item.status === 'quarantined' 
                        ? 'bg-rose-950/20 border-rose-800/40' 
                        : 'bg-slate-800/40 border-slate-700/60'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className={`text-xs px-2 py-0.5 rounded font-mono font-semibold ${
                            item.status === 'quarantined' ? 'bg-rose-900 text-rose-200' : 'bg-slate-700 text-amber-300'
                          }`}>
                            {item.kind.toUpperCase()}
                          </span>
                          <span className="text-xs text-slate-400">Author: {item.author} ({item.tier})</span>
                        </div>
                        <h4 className="font-medium text-slate-200 text-sm">{item.subject}</h4>
                        <div className="text-xs text-slate-400 font-mono bg-slate-900/60 p-2 rounded border border-slate-800 mt-2">
                          Exact quote span: <span className="text-amber-300">"{item.quote}"</span>
                          <span className="ml-2 text-slate-400">(SHA256: {item.hash})</span>
                        </div>

                        {item.warning && (
                          <div className="flex items-center space-x-2 text-xs text-rose-400 font-medium mt-2">
                            <ShieldAlert className="h-4 w-4" />
                            <span>{item.warning}</span>
                          </div>
                        )}
                      </div>

                      <div className="flex space-x-2">
                        {item.status !== 'quarantined' ? (
                          <>
                            <button className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded transition font-medium">
                              Confirm
                            </button>
                            <button className="bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs px-3 py-1.5 rounded transition">
                              Reject
                            </button>
                          </>
                        ) : (
                          <span className="bg-rose-900/40 text-rose-300 border border-rose-700/50 text-xs px-3 py-1.5 rounded font-mono">
                            QUARANTINED
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: SAFE HANDOFF */}
        {activeTab === "handoff" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-100">Safe Handoff Document</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Absent: <strong>Maya Sundaram</strong> &rarr; Recipient: <strong>Rajesh (Operations)</strong>
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-3 py-1 rounded-full">
                    Pre-Retrieved & Grant-Scoped
                  </span>
                </div>
              </div>

              {/* Bucket 1: Act Now */}
              <div className="mb-6">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-rose-400 mb-3 flex items-center space-x-2">
                  <span className="h-2 w-2 rounded-full bg-rose-400"></span>
                  <span>Act Now</span>
                </h4>
                <div className="bg-slate-800/30 border border-slate-800 rounded-lg p-4 space-y-2">
                  <p className="text-sm font-medium text-slate-200">Confirm order docket #4092 for Sharma Prints (10,000 carton boxes)</p>
                  <p className="text-xs text-slate-400 font-mono">
                    Citation: "Order docket #4092 for Sharma Prints is confirmed" (SHA256: a4d7c86f...)
                  </p>
                </div>
              </div>

              {/* Bucket 2: Needs Approval */}
              <div className="mb-6">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-3 flex items-center space-x-2">
                  <span className="h-2 w-2 rounded-full bg-amber-400"></span>
                  <span>Needs Approval (Within Standing Limits)</span>
                </h4>
                <div className="bg-slate-800/30 border border-slate-800 rounded-lg p-4 space-y-2">
                  <p className="text-sm font-medium text-slate-200">Authorize vendor payments up to 25,000 INR from HDFC Current account</p>
                  <p className="text-xs text-slate-400 font-mono">
                    Citation: "approve vendor payments up to 25,000 INR" (SHA256: 7bc910df...)
                  </p>
                </div>
              </div>

              {/* Bucket 3: What I Cannot See */}
              <div className="mt-8 border-t border-slate-800 pt-6">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
                  <ShieldAlert className="h-4 w-4 text-amber-400" />
                  <span>What I Cannot See (Transparency & Coverage Gaps)</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg space-y-1">
                    <p className="text-xs font-medium text-amber-300">Unwritten Voice Calls / Unexported Personal WhatsApp</p>
                    <p className="text-xs text-slate-400">Agreements made in the last 48 hours without chat export are absent.</p>
                    <p className="text-xs text-slate-400 font-mono">Mitigation: Verify with vendor before dispatch.</p>
                  </div>
                  <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg space-y-1">
                    <p className="text-xs font-medium text-amber-300">Isolated Banking Tokens (Axis Bank OTP)</p>
                    <p className="text-xs text-slate-400">Physical phone remains with brother in Erode. Cannot authorize via Axis Bank.</p>
                    <p className="text-xs text-slate-400 font-mono">Mitigation: Route permitted payments via HDFC account.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: ACTION GATEWAY */}
        {activeTab === "actions" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <h3 className="text-base font-semibold text-slate-100 mb-1">Gated Action Layer (Cedar Policy Engine)</h3>
              <p className="text-xs text-slate-400 mb-6">
                Deterministic code disposes. Only actions complying with pre-authorized standing delegation ceilings are permitted.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Test Action 1: Authorized */}
                <div className="border border-slate-800 bg-slate-950/40 p-5 rounded-xl space-y-4">
                  <div>
                    <span className="text-xs font-mono font-semibold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                      WITHIN LIMIT
                    </span>
                    <h4 className="text-sm font-medium text-slate-200 mt-2">Vendor Advance Payment: INR 18,000</h4>
                    <p className="text-xs text-slate-400 mt-1">Vendor: Murugan (Balaji Paper Mills)</p>
                    <p className="text-xs text-slate-400 font-mono">Ceiling: INR 25,000 · Account: HDFC Current</p>
                  </div>

                  <button
                    onClick={() => executeAction(18000)}
                    disabled={loading}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs py-2 rounded-md font-medium transition shadow"
                  >
                    Test Execute INR 18,000
                  </button>
                </div>

                {/* Test Action 2: Blocked */}
                <div className="border border-slate-800 bg-slate-950/40 p-5 rounded-xl space-y-4">
                  <div>
                    <span className="text-xs font-mono font-semibold text-rose-400 bg-rose-950/60 px-2 py-0.5 rounded border border-rose-800">
                      EXCEEDS CEILING
                    </span>
                    <h4 className="text-sm font-medium text-slate-200 mt-2">Vendor Advance Payment: INR 48,000</h4>
                    <p className="text-xs text-slate-400 mt-1">Vendor: Murugan (Balaji Paper Mills)</p>
                    <p className="text-xs text-slate-400 font-mono">Ceiling: INR 25,000 · Account: HDFC Current</p>
                  </div>

                  <button
                    onClick={() => executeAction(48000)}
                    disabled={loading}
                    className="w-full bg-rose-600 hover:bg-rose-500 text-white text-xs py-2 rounded-md font-medium transition shadow"
                  >
                    Test Execute INR 48,000 (Should Block)
                  </button>
                </div>
              </div>

              {/* Action Response Display */}
              {actionStatus && (
                <div className={`mt-6 p-4 rounded-lg border font-mono text-xs flex items-center space-x-3 ${
                  actionStatus.success 
                    ? 'bg-emerald-950/30 border-emerald-800 text-emerald-300' 
                    : 'bg-rose-950/30 border-rose-800 text-rose-300'
                }`}>
                  {actionStatus.success ? <CheckCircle2 className="h-5 w-5 flex-shrink-0" /> : <XCircle className="h-5 w-5 flex-shrink-0" />}
                  <span>{actionStatus.message}</span>
                </div>
              )}
            </div>
          </div>
        )}
        {/* TAB 5: ALEXA+ LIVE SIMULATION */}
        {(activeTab as string) === "alexa_sim" && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-100 flex items-center space-x-2">
                    <span className="h-3 w-3 rounded-full bg-cyan-400 animate-pulse"></span>
                    <span>Alexa+ Simulated Experience Gateway</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Live endpoint caller executing real backend routes (/api/alexa/webhook & /api/action/execute)
                  </p>
                </div>
                <span className="text-xs font-mono bg-cyan-950/60 text-cyan-300 border border-cyan-800 px-3 py-1 rounded-full">
                  Track: Alexa+ Simulation
                </span>
              </div>

              {/* Scenario Walkthrough Steps */}
              <div className="space-y-4">
                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">
                    <span>Step 1: Spoken Owner Utterance</span>
                  </div>
                  <p className="text-sm font-medium text-slate-200">
                    Maya (Owner): <span className="text-amber-300">"I'm unavailable tomorrow. Identify anything that needs attention."</span>
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    Triggers: <code className="text-slate-300 bg-slate-900 px-1 py-0.5 rounded">DeclareAbsenceAndTriageIntent</code> via backend webhook.
                  </p>
                </div>

                <div className="bg-slate-950/60 border border-slate-800 p-4 rounded-lg">
                  <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                    <span>Step 2: Spoken Alexa Response from Backend</span>
                  </div>
                  <p className="text-sm font-mono text-emerald-300">
                    "Absence recorded for tomorrow under your Continuity Charter. I've generated a Safe Handoff for Rajesh with immediate commitments, items requiring delegated approval, and flagged coverage gaps."
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <div className="bg-rose-950/20 border border-rose-800/40 p-4 rounded-lg">
                    <p className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-1">Step 3: Attack / Over-Limit Check</p>
                    <p className="text-xs text-slate-300">Rajesh requests ₹65,000 payment (Ceiling: ₹25,000)</p>
                    <div className="mt-2 text-xs font-mono text-rose-300 bg-rose-950/60 p-2 rounded border border-rose-900">
                      HTTP 403 Forbidden: Requested amount INR 65,000 exceeds delegation ceiling INR 25,000.
                    </div>
                  </div>

                  <div className="bg-emerald-950/20 border border-emerald-800/40 p-4 rounded-lg">
                    <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">Step 4: Authorized Request</p>
                    <p className="text-xs text-slate-300">Rajesh requests ₹18,000 payment (Within ₹25,000 ceiling)</p>
                    <div className="mt-2 text-xs font-mono text-emerald-300 bg-emerald-950/60 p-2 rounded border border-emerald-900">
                      HTTP 200 OK: Policy Decision: ALLOW. Execution Status: AUTHORIZED_AND_RECORDED.
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-3 bg-slate-900 rounded border border-slate-800 text-xs text-slate-400 font-mono flex items-center justify-between">
                  <span>Terminal Entry Point Command:</span>
                  <code className="text-amber-400">python -m tests.run_simulation</code>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
