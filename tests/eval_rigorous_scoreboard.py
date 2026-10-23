"""
True Precision & Recall Benchmark Harness
Runs the extractor across all 150 gold messages, collects candidate claims,
runs span verification on each extracted claim, and measures:
- True Positives, False Positives, False Negatives
- Extraction Precision, Recall, and F1-Score
- Verbatim Span Accuracy on extracted output
- Per-Trap breakdown (Forged Authority, Retractions, Sarcasm/Hyperbole, Tanglish, Relative Dates)
- Clear labeling of active engine (Bedrock Claude vs Deterministic Pattern Fallback)
"""
import os
import json
import difflib
from pathlib import Path
from typing import List, Dict, Any, Tuple

from tests.gold_dataset.schema import BenchmarkMessage, BenchmarkClaim, TrustTier, ClaimKind
from tests.gold_dataset.verifier import verify_span, validate_authority_claim, VerificationError, ForgedAuthorityError
from backend.adapters.bedrock_adapter import BedrockExtractionAdapter, LLMClaimCandidate

def string_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()

def evaluate_extractor_on_gold():
    gold_path = Path("tests/gold_dataset/maya_gold_150.json")
    with open(gold_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    messages = [BenchmarkMessage(**m) for m in raw_items]
    adapter = BedrockExtractionAdapter()
    engine_name = "Amazon Bedrock (Claude 3.5 Sonnet)" if adapter.client else "Deterministic Rule/Pattern Baseline"

    print("="*75)
    print("SIIGO: RIGOROUS EVALUATION HARNESS")
    print(f"Active Extractor Engine: {engine_name}")
    print("="*75)

    # Global counters
    tp = 0  # True positive: extracted claim matches a gold claim
    fp = 0  # False positive: extracted claim does not match any gold claim
    fn = 0  # False negative: gold claim was not discovered by extractor

    total_extracted = 0
    spans_attempted = 0
    spans_verified = 0

    # Trap counters
    trap_results = {
        "FORGED_AUTHORITY": {"total": 0, "quarantined_or_rejected": 0, "accepted_as_approved": 0},
        "RETRACTION": {"total": 0, "detected": 0, "missed": 0},
        "SARCASM_NOISE": {"total": 0, "correctly_ignored": 0, "hallucinated_claims": 0},
        "RELATIVE_DATE": {"total": 0, "extracted": 0, "missed": 0},
        "TANGLISH_DEPENDENCY": {"total": 0, "extracted": 0, "missed": 0}
    }

    for msg in messages:
        gold_claims = msg.expected_claims

        # 1. Run Extractor
        extracted_candidates: List[LLMClaimCandidate] = adapter.extract_candidates(
            source_text=msg.raw_text,
            author_name=msg.author_name,
            timestamp_ist_str=msg.timestamp_ist
        )
        total_extracted += len(extracted_candidates)

        # 2. Test Spans on Extracted Claims (NOT gold quotes!)
        valid_candidates = []
        for cand in extracted_candidates:
            spans_attempted += 1
            # Build EvidenceSpan from candidate output
            from tests.gold_dataset.schema import EvidenceSpan
            span = EvidenceSpan(
                exact_quote=cand.exact_quote,
                span_start=cand.span_start,
                span_end=cand.span_end
            )
            try:
                verify_span(msg.raw_text, span)
                spans_verified += 1
                valid_candidates.append(cand)
            except VerificationError:
                # Hallucination or drifted quote rejected by span verifier
                pass

        # 3. Security Quarantine Check
        quarantined_claims = []
        allowed_candidates = []
        for cand in valid_candidates:
            mock_claim = type('Claim', (), {
                'kind': cand.kind,
                'action_type': 'approve_payment' if 'approve' in cand.subject.lower() else None,
                'subject': cand.subject
            })
            try:
                validate_authority_claim(mock_claim, msg.author_trust_tier)
                allowed_candidates.append(cand)
            except ForgedAuthorityError:
                quarantined_claims.append(cand)

        # 4. Match Allowed Candidates against Gold Claims
        matched_gold_indices = set()
        for cand in allowed_candidates:
            matched = False
            for g_idx, gold in enumerate(gold_claims):
                if g_idx in matched_gold_indices:
                    continue
                # Match criterion: Kind matches AND (quote overlap OR subject similarity >= 0.5)
                quote_sim = string_similarity(cand.exact_quote, gold.evidence_span.exact_quote)
                subj_sim = string_similarity(cand.subject, gold.subject)
                if cand.kind == gold.kind.value and (quote_sim > 0.4 or subj_sim > 0.45):
                    tp += 1
                    matched_gold_indices.add(g_idx)
                    matched = True
                    break
            if not matched:
                fp += 1

        # Any unmatched gold claim is a false negative
        fn += (len(gold_claims) - len(matched_gold_indices))

        # 5. Trap-Specific Tracking
        for gold in gold_claims:
            tag = gold.trap_tag
            if tag == "RETRACTION":
                trap_results["RETRACTION"]["total"] += 1
                if any(c.modality == "retracted" for c in allowed_candidates):
                    trap_results["RETRACTION"]["detected"] += 1
                else:
                    trap_results["RETRACTION"]["missed"] += 1
            elif tag and "RELATIVE_DATE" in tag:
                trap_results["RELATIVE_DATE"]["total"] += 1
                if any(c.kind == gold.kind.value for c in allowed_candidates):
                    trap_results["RELATIVE_DATE"]["extracted"] += 1
                else:
                    trap_results["RELATIVE_DATE"]["missed"] += 1
            elif tag and "TANGLISH" in tag:
                trap_results["TANGLISH_DEPENDENCY"]["total"] += 1
                if any(c.kind == gold.kind.value for c in allowed_candidates):
                    trap_results["TANGLISH_DEPENDENCY"]["extracted"] += 1
                else:
                    trap_results["TANGLISH_DEPENDENCY"]["missed"] += 1

        if msg.quarantine_expected:
            trap_results["FORGED_AUTHORITY"]["total"] += 1
            # Check if an unauthorized approval slipped into allowed
            if any(c.kind in ("approval_rule", "decision") for c in allowed_candidates):
                trap_results["FORGED_AUTHORITY"]["accepted_as_approved"] += 1
            else:
                trap_results["FORGED_AUTHORITY"]["quarantined_or_rejected"] += 1

        if not gold_claims and not msg.quarantine_expected:
            trap_results["SARCASM_NOISE"]["total"] += 1
            if len(allowed_candidates) == 0:
                trap_results["SARCASM_NOISE"]["correctly_ignored"] += 1
            else:
                trap_results["SARCASM_NOISE"]["hallucinated_claims"] += 1

    # Calculations
    precision = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    span_pass_rate = (spans_verified / spans_attempted) * 100 if spans_attempted > 0 else 100.0

    print("\n1. EXTRACTION PERFORMANCE METRICS:")
    print(f"   • Total Gold Target Claims:     {tp + fn}")
    print(f"   • Extracted Claims Produced:   {total_extracted}")
    print(f"   • True Positives (TP):          {tp}")
    print(f"   • False Positives (FP):         {fp}")
    print(f"   • False Negatives (FN):         {fn}")
    print(f"   • Precision:                    {precision:.1f}%")
    print(f"   • Recall:                       {recall:.1f}%")
    print(f"   • F1 Score:                     {f1:.1f}%")

    print("\n2. DETERMINISTIC GATE EFFICIENCY (ON EXTRACTED OUTPUT):")
    print(f"   • Extracted Quote Spans Tested: {spans_attempted}")
    print(f"   • Verbatim Match Rate:          {span_pass_rate:.1f}%")

    print("\n3. ADVERSARIAL TRAP BREAKDOWN:")
    for trap, res in trap_results.items():
        print(f"   • {trap:22s} | Total: {res['total']:2d} | Details: {res}")
    print("="*75)

    return {
        "engine": engine_name,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "span_pass_rate": span_pass_rate,
        "trap_results": trap_results
    }

if __name__ == "__main__":
    evaluate_extractor_on_gold()
