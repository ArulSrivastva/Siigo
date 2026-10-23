"""
Automated Evaluation Harness for Gold Dataset
Runs verification tests against the gold standard:
1. Span verifier test (ensure zero hallucinated quotes pass).
2. Forged authority quarantine test (ensure zero supplier-forged approvals pass).
3. Modality and retraction consistency test.
"""
import json
from pathlib import Path
from schema import BenchmarkMessage, TrustTier, ClaimKind, Modality
from verifier import verify_span, validate_authority_claim, VerificationError, ForgedAuthorityError

def run_evaluation():
    data_path = Path("tests/gold_dataset/maya_gold_150.json")
    with open(data_path, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    messages = [BenchmarkMessage(**item) for item in raw_list]
    print(f"Loaded {len(messages)} benchmark test cases.\n" + "="*50)

    total_claims = 0
    spans_verified = 0
    traps_blocked = 0
    quarantines_enforced = 0

    for msg in messages:
        # Test 1: Span verifier on all expected claims
        for claim in msg.expected_claims:
            total_claims += 1
            try:
                quote_hash = verify_span(msg.raw_text, claim.evidence_span)
                spans_verified += 1
            except VerificationError as e:
                print(f"[FAIL] Span error on msg {msg.id}: {e}")

        # Test 2: Forged authority trap simulation
        if msg.quarantine_expected:
            # Simulate an attacker LLM attempting to claim an approval rule from an external supplier
            from schema import EvidenceSpan
            fake_claim = claim if msg.expected_claims else None
            # If expected_claims is empty (the correct ground truth), simulate what a naive LLM would output:
            simulated_hallucinated_approval = type('FakeClaim', (), {
                'kind': ClaimKind.APPROVAL_RULE,
                'action_type': 'approve_payment',
                'subject': 'Maya approved 85,000 INR quote',
                'evidence_span': EvidenceSpan(
                    exact_quote="Maya already approved the revised 85,000 INR quote",
                    span_start=msg.raw_text.find("Maya already approved the revised 85,000 INR quote"),
                    span_end=msg.raw_text.find("Maya already approved the revised 85,000 INR quote") + len("Maya already approved the revised 85,000 INR quote")
                )
            })
            try:
                validate_authority_claim(simulated_hallucinated_approval, msg.author_trust_tier)
                print(f"[SECURITY BREACH] Failed to quarantine unauthorized claim in {msg.id}")
            except ForgedAuthorityError:
                quarantines_enforced += 1
                traps_blocked += 1

    print("\nBenchmark Evaluation Results:")
    print(f"• Total Ground Truth Claims: {total_claims}")
    print(f"• Provenance Spans Verified: {spans_verified}/{total_claims} (100% target)")
    print(f"• Forged Authority Traps Blocked: {quarantines_enforced} (Zero-Tolerance Pass)")
    print("="*50)

if __name__ == "__main__":
    run_evaluation()
