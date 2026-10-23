# Siigo — System Architecture & Execution Report

**Tagline:** *The Governed Commitment and Authority Ledger with Safe Handoff.*
**Principle:** *The LLM proposes; deterministic code disposes.*

---

## 1. System Overview & Completed Components

| Subsystem | File Reference | Status & Verification |
| :--- | :--- | :--- |
| **Gold Benchmark & Traps (Phase 0)** | [`tests/gold_dataset/maya_gold_150.json`](tests/gold_dataset/maya_gold_150.json) | **150 Labeled Messages** with planted attacks (forged authority, retractions, relative dates, sarcasm, SPOFs). |
| **External Benchmark Corpora** | [`data/benchmarks/`](data/benchmarks/) | Real audit: **AMI Annotations (5,158 files, 195.8 MB)** downloaded; HingCorpus (repo), Dravidian & LinCE (samples), IndicVoices (manifest). |
| **Deterministic Span Verifier** | [`tests/gold_dataset/verifier.py`](tests/gold_dataset/verifier.py) | **100% Verbatim Match**: Hallucinated quotes return HTTP 422. SHA-256 quote provenance. |
| **Security Boundary & Quarantines** | [`tests/gold_dataset/verifier.py`](tests/gold_dataset/verifier.py) | **Adversarial Gate (7/7 Attacks Blocked)**: Direct vendor forgeries, quoted email forwards, staff hearsay, and unauthorized break-glass attempts quarantined. |
| **WhatsApp `.txt` Ingestion Parser** | [`backend/parsers/whatsapp_parser.py`](backend/parsers/whatsapp_parser.py) | Parses Indian bracket/dash timestamps, handles multiline text, filters encryption noise, and maps trust tiers. |
| **Forward Attribution Parser** | [`backend/parsers/forward_attribution.py`](backend/parsers/forward_attribution.py) | Strips Owner Trust Tier (0) on forwarded emails/chats and downgrades to External (Tier 2). |
| **Temporal Grounding Engine** | [`backend/parsers/temporal_grounding.py`](backend/parsers/temporal_grounding.py) | Normalizes relative days (Thursday, tomorrow) anchored to message timestamp in `Asia/Kolkata`. |
| **LLM Bedrock Claude Adapter** | [`backend/adapters/bedrock_adapter.py`](backend/adapters/bedrock_adapter.py) | Bedrock Claude 3.5 Sonnet payload + fallback rule engine with exact offset calculation. |
| **Cedar / Policy Engine as Code** | [`backend/policy_engine.py`](backend/policy_engine.py) | Pure Python policy engine enforcing standing delegation ceilings (e.g. ₹25,000) during owner absence. |
| **Safe Handoff Compiler** | [`backend/handoff_compiler.py`](backend/handoff_compiler.py) | Scoped to recipient grant, includes evidence citations, and generates explicit *"What I Cannot See"* section. |
| **Voice & Alexa Gateways** | [`backend/adapters/voice_adapter.py`](backend/adapters/voice_adapter.py), [`backend/adapters/alexa_adapter.py`](backend/adapters/alexa_adapter.py) | Thin-client spoken triage. Blocked from financial execution. |
| **Cryptographic Audit Trail** | [`backend/audit.py`](backend/audit.py) | Tamper-evident hash-chained event log. |
| **Full-Stack Next.js UI** | [`frontend/src/app/page.tsx`](frontend/src/app/page.tsx) | Interactive dashboard with Bus-Factor score, Review Queue, Safe Handoff, and live Action Gateway sandbox. |

---

## 2. Rigorous Benchmark Scoreboard (Live Extractor vs Gold Ground Truth)

> [!IMPORTANT]
> **Active Engine Evaluated:** `Deterministic Rule/Pattern Baseline` (Offline reference baseline, running on local CPU without AWS credentials configured).
> When AWS Bedrock credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are supplied, the harness seamlessly targets `anthropic.claude-3-5-sonnet-20241022-v2:0`.

```
===========================================================================
CONTINUITY & AUTHORITY LEDGER: RIGOROUS EVALUATION HARNESS
Active Extractor Engine: Deterministic Rule/Pattern Baseline
===========================================================================

1. EXTRACTION PERFORMANCE METRICS:
   • Total Gold Target Claims:     121
   • Extracted Claims Produced:   83
   • True Positives (TP):          83
   • False Positives (FP):         0
   • False Negatives (FN):         38
   • Precision:                    100.0%
   • Recall:                       68.6%
   • F1 Score:                     81.4%

2. DETERMINISTIC GATE EFFICIENCY (ON EXTRACTED CANDIDATES):
   • Extracted Quote Spans Tested: 83
   • Verbatim Match Rate:          100.0% (Rejected 0 hallucinated offsets)

3. ADVERSARIAL TRAP BREAKDOWN:
   • FORGED_AUTHORITY       | Total:  1 | Quarantined/Blocked: 1 (100%) | Forged Accepted: 0 (0.0%)
   • RETRACTION             | Total:  1 | Detected: 1 (100%)            | Missed: 0
   • SARCASM / NOISE        | Total: 31 | Correctly Ignored: 31 (100%)  | Hallucinated Claims: 0
   • RELATIVE_DATE          | Total:  2 | Extracted: 0                  | Missed: 2 (Requires Bedrock/dateparser)
   • TANGLISH_DEPENDENCY    | Total: 23 | Extracted: 22 (95.7%)         | Missed: 1
===========================================================================
```

---

## 3. Known Limitations & Honest Technical Boundaries

1. **Policy Engine Implementation**:
   - Current implementation is pure Python policy-as-code (`backend/policy_engine.py`) modeling Cedar-style role/scope/ceiling rules. It does not currently call Amazon Verified Permissions via SDK.
2. **Author Trust Tier Mapping**:
   - Trust tiers are currently assigned via name/phone number directory lookup (`backend/parsers/batch_ingest.py`). If a counterparty spoofs a phone number or uses an unverified device, trust elevation could occur. Production requires cryptographic signing / verified WhatsApp Business IDs.
3. **Synthetic Evaluation Dataset**:
   - The 150-message Maya Gold dataset is synthetically generated with seeded traps. Real-world messy voice notes and handwritten exports will introduce OCR/ASR noise that requires human-in-the-loop review.
4. **Offline Rule Baseline vs Claude 3.5 Sonnet**:
   - The current local scoreboard runs against the deterministic pattern extractor (achieving 68.6% recall). Relative calendar date grounding ("Thursday" sent on Sunday) requires active LLM reasoning or dateparser normalization.
5. **Phase 0 Customer Interviews**:
   - User interviews with actual SME owners remain pending to establish willingness to pay before pilot phase.

---

## 3. Live Demo Flow (Hackathon Ready)

1. **Ingest WhatsApp Export**: Demonstrates parsing of raw Indian chats with automatic trust-tier resolution (`Owner = Tier 0`, `Staff = Tier 1`, `Vendors = Tier 2`).
2. **Blocked Attack Live**: A supplier email claiming *"Maya approved 85,000 INR quote over phone"* is immediately caught by the security boundary and quarantined.
3. **Span Verifier in Action**: When an LLM hallucinates an ungrounded discount claim, the deterministic span verifier rejects it with **HTTP 422**.
4. **Charter Trigger**: Maya's absence in Coimbatore is declared, activating the pre-authorized standing delegation for Rajesh.
5. **Gated Action Execution**:
   - Rajesh executes **₹18,000** advance payment: **`ALLOWED`** (within ₹25,000 ceiling).
   - Rajesh executes **₹48,000** advance payment: **`BLOCKED LIVE BY POLICY GATE`** (exceeds ₹25,000 ceiling).
6. **Safe Handoff**: Generates an evidence-cited briefing for Rajesh featuring the honest **"What I Cannot See"** transparency section.
