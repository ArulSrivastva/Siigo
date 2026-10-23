# Siigo

A governed commitment and authority ledger with an emergency Safe Handoff mode for owner-run businesses.

## Overview

Siigo provides an operational continuity layer for owner-dependent businesses where critical commitments, authority limits, and decisions reside in chat channels and unwritten conversations. Siigo captures operational promises, grounds every claim in verbatim source evidence, enforces authority limits through policy-as-code, and compiles a citation-backed Safe Handoff when a key person is unavailable.

## Architectural Principle

The LLM proposes; deterministic code disposes.

Language models extract candidate commitments and draft natural-language briefings. Graph calculations, policy gates, span integrity checks, and action executions are performed strictly by deterministic code.

## Key Subsystems

1. Evidence Store
An append-only, content-hashed repository storing raw chat exports, emails, and voice notes. Each record is stamped with a cryptographic SHA-256 hash and assigned a security trust tier.

2. Deterministic Span Verifier
Validates that every claim extracted by an LLM contains a verbatim substring matching the source document at exact character offsets. Fabricated quotes and drifted boundaries are rejected with HTTP 422.

3. Security Boundary and Trust Tiers
Source tiers govern authority rights:
- Tier 0: Verified Owner
- Tier 1: Staff Contributor
- Tier 2: External Client or Vendor
- Tier 3: Untrusted External Source

Untrusted and external tiers cannot establish approval rules, define decisions, or execute out-of-channel approvals. Quoted forwards and forwarded messages automatically strip elevated forwarder privileges and downgrade to Tier 2.

4. Authority Policy Engine
A deterministic policy layer enforcing pre-authorized standing delegations and monetary ceilings. Payments exceeding delegation limits or lacking explicit positive amounts fail closed and return HTTP 403.

5. Safe Handoff Compiler
Compiles an evidence-cited operational briefing during an absence. Claims are filtered by recipient grants and divided into Act Now, Needs Approval, and Can Wait. Every handoff includes an explicit What I Cannot See transparency section identifying unmonitored channels and operational gaps.

6. Hash-Chained Audit Trail
Every state transition, quarantine event, and policy execution is linked through an immutable SHA-256 hash chain.

## Repository Layout

- backend/
  - app.py: FastAPI REST service and route definitions
  - auth.py: Server-side identity and tenant context extraction
  - models.py: SQLAlchemy database models for evidence, claims, charter, and audit logs
  - policy_engine.py: Deterministic policy-as-code engine
  - handoff_compiler.py: Scoped handoff briefing compiler
  - audit.py: Cryptographic hash-chained audit logger
  - analyzers.py: Bus-factor, fragility, and single-point-of-failure analyzers
  - parsers/
    - whatsapp_parser.py: WhatsApp bracket and dash export parser
    - batch_ingest.py: Evidence ingestion pipeline with trust resolution
    - forward_attribution.py: Quoted forward detection and privilege-stripping engine
    - temporal_grounding.py: Deterministic Asia/Kolkata date normalizer
  - adapters/
    - bedrock_adapter.py: Amazon Bedrock Claude 3.5 Sonnet payload and pattern fallback
    - voice_adapter.py: Spoken audio note transcription adapter
    - alexa_adapter.py: Alexa thin-client triage gateway

- frontend/
  - Next.js application containing Bus-Factor Health Dashboard, Confirmation Queue, Safe Handoff Viewer, and Policy Sandbox

- tests/
  - test_e2e_demo.py: Full end-to-end integration and security test
  - test_adversarial_suite.py: 10-scenario adversarial attack test suite with fail-closed assertions
  - test_whatsapp_extraction.py: Verification of real WhatsApp export parsing
  - eval_rigorous_scoreboard.py: Precision, recall, and per-trap evaluation harness
  - gold_dataset/
    - maya_gold_150.json: 150 labeled operational messages with planted adversarial traps
    - verifier.py: Production span verifier and authority quarantine validator

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend Setup

1. Install backend dependencies:
   pip install fastapi uvicorn sqlalchemy pydantic

2. Run tests:
   python -m tests.test_e2e_demo
   python -m tests.test_adversarial_suite
   python -m tests.eval_rigorous_scoreboard

3. Start backend API:
   python -m uvicorn backend.app:app --reload --port 8000

The API documentation is accessible at http://127.0.0.1:8000/docs.

### Frontend Setup

1. Install frontend dependencies:
   cd frontend
   npm install

2. Start development server:
   npm run dev

The web interface is accessible at http://localhost:3000.

## Alexa+ Simulated Experience (Hackathon Track Entry Point)

Siigo includes a runnable simulation entry point satisfying the Alexa+ Simulated Experience track:
- Simulation Script: tests/run_simulation.py
- Architecture Pattern: Thin-client voice gateway forwarding typed IntentRequests to backend policy and handoff compilers.

### Running the Live Simulation Walkthrough

1. Run the automated scenario via terminal:
   python -m tests.run_simulation

2. Walkthrough Scenario Executed:
   - Step 1: Owner operational instruction is ingested and content-hashed.
   - Step 2: Extracted decision is validated by the deterministic span verifier with exact character offsets.
   - Step 3: Simulated Alexa+ voice utterance: "I'm unavailable tomorrow. Identify anything that needs attention."
   - Step 4: Backend /api/alexa/webhook processes DeclareAbsenceAndTriageIntent and returns speech output.
   - Step 5: Safe Handoff compiled for delegate Rajesh with exact quote citations and honest "What I Cannot See" section.
   - Step 6: Unauthorized action attempt: Rajesh requests INR 65,000 payment (standing ceiling is INR 25,000) -> Blocked with HTTP 403.
   - Step 7: Permitted action attempt: Rajesh requests INR 18,000 payment -> HTTP 200 ALLOW (labeled AUTHORIZED_AND_RECORDED).
   - Step 8: Cryptographic hash-chained audit trail verification.

3. Interactive Browser Demo:
   Start the application and navigate to http://localhost:3000 -> "Alexa+ Live Simulation".

Evaluated against the 150-message Maya Gold Benchmark using the deterministic baseline engine:
- Total Ground-Truth Target Claims: 121
- Extracted Claims: 85
- Precision: 100.0%
- Recall: 70.2%
- F1 Score: 82.5%
- Extracted Span Verbatim Match: 100.0%
- Adversarial Attack Defense: 7/7 attack scenarios quarantined (100% fail-closed)
- Relative Date Normalization: 2/2 extracted and anchored to Asia/Kolkata
