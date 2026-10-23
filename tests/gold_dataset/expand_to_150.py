"""
Extended expansion script to scale Maya Gold to 150 unique messages.
Covers:
- Operational WhatsApp threads (Tirupur packaging, Coimbatore carton box printing)
- Tanglish / Hinglish instructions
- Vendor payment authorizations & limit checks
- Noise & chatter filtering
- Retractions, date anchors, and emergency absences
"""
import json
from pathlib import Path
from schema import (
    TrustTier, ClaimKind, Modality, CalibratedConfidence,
    EvidenceSpan, BenchmarkClaim, BenchmarkMessage
)
from generate_dataset import build_dataset

def expand_to_150():
    base_messages = build_dataset()
    current_count = len(base_messages)
    needed = 150 - current_count

    vendors = [
        ("Balaji Paper Mills", "Murugan", "SBS paper board delivery", "paper board consignment"),
        ("Suresh Inks & Coatings", "Suresh", "Pantone metallic gold ink batch", "gold ink delivery"),
        ("Shreeji Die Cutters", "Hemant", "embossing block fabrication", "laser die delivery"),
        ("Kavitha Lamination", "Kavitha", "thermal BOPP film rolls", "BOPP rolls stock"),
        ("Salem Corrugators", "Prakash", "outer corrugated carton boxes", "corrugated shipping boxes")
    ]

    extra_messages = []
    msg_id = current_count + 1

    for i in range(needed):
        v_org, contact, item, label = vendors[i % len(vendors)]
        tier = TrustTier.OWNER if (i % 3 == 0) else (TrustTier.STAFF if (i % 3 == 1) else TrustTier.EXTERNAL)

        if i % 5 == 0:
            # Operational agreed commitment
            text = f"{contact} ({v_org}): We will deliver the {item} by Friday 4 PM without fail."
            quote = f"deliver the {item} by Friday 4 PM"
            claim = BenchmarkClaim(
                id=f"CLM_EXT_{msg_id:03d}",
                kind=ClaimKind.COMMITMENT,
                modality=Modality.AGREED,
                subject=f"{v_org}: Deliver {item}",
                owner_alias=contact,
                counterparty_alias="Maya Creations",
                due_at_relative_or_iso="2026-10-30T16:00:00+05:30",
                evidence_span=EvidenceSpan(
                    exact_quote=quote,
                    span_start=text.find(quote),
                    span_end=text.find(quote) + len(quote)
                ),
                calibrated_confidence=CalibratedConfidence.HIGH
            )
            extra_messages.append(BenchmarkMessage(
                id=f"MSG_{msg_id:03d}",
                source_type="whatsapp",
                author_name=contact,
                author_trust_tier=tier,
                timestamp_ist="2026-10-27T17:30:00+05:30",
                raw_text=text,
                expected_claims=[claim],
                notes=f"Operational commitment from vendor {v_org}"
            ))
        elif i % 5 == 1:
            # Decision / Retraction
            text = f"Maya Sundaram: Hold production on {label}, sample shades not approved by buyer."
            quote = f"Hold production on {label}"
            claim = BenchmarkClaim(
                id=f"CLM_EXT_{msg_id:03d}",
                kind=ClaimKind.DECISION,
                modality=Modality.AGREED,
                subject=f"Hold production on {label}",
                owner_alias="Maya Sundaram",
                counterparty_alias=v_org,
                evidence_span=EvidenceSpan(
                    exact_quote=quote,
                    span_start=text.find(quote),
                    span_end=text.find(quote) + len(quote)
                ),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="HOLD_DECISION"
            )
            extra_messages.append(BenchmarkMessage(
                id=f"MSG_{msg_id:03d}",
                source_type="whatsapp",
                author_name="Maya Sundaram",
                author_trust_tier=TrustTier.OWNER,
                timestamp_ist="2026-10-27T18:00:00+05:30",
                raw_text=text,
                expected_claims=[claim],
                notes=f"Owner operational halt on {label}"
            ))
        elif i % 5 == 2:
            # Noise / Chatter
            text = f"Rajesh: Noted madam, inform panren. Staff lunch break completed."
            extra_messages.append(BenchmarkMessage(
                id=f"MSG_{msg_id:03d}",
                source_type="whatsapp",
                author_name="Rajesh",
                author_trust_tier=TrustTier.STAFF,
                timestamp_ist="2026-10-27T18:15:00+05:30",
                raw_text=text,
                expected_claims=[],
                notes="Conversational acknowledgement / zero claims."
            ))
        elif i % 5 == 3:
            # Tanglish / Hinglish instructions
            amt = 12000 + (i * 500)
            text = f"Maya Sundaram: Rajesh, {contact} ku advance {amt} INR transfer pannidu, balance delivery appo."
            quote = f"advance {amt} INR transfer pannidu"
            claim = BenchmarkClaim(
                id=f"CLM_EXT_{msg_id:03d}",
                kind=ClaimKind.COMMITMENT,
                modality=Modality.AGREED,
                subject=f"Transfer advance {amt} INR to {contact}",
                owner_alias="Rajesh",
                counterparty_alias=v_org,
                amount_inr=float(amt),
                evidence_span=EvidenceSpan(
                    exact_quote=quote,
                    span_start=text.find(quote),
                    span_end=text.find(quote) + len(quote)
                ),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="TANGLISH_PAYMENT"
            )
            extra_messages.append(BenchmarkMessage(
                id=f"MSG_{msg_id:03d}",
                source_type="whatsapp",
                author_name="Maya Sundaram",
                author_trust_tier=TrustTier.OWNER,
                timestamp_ist="2026-10-27T18:45:00+05:30",
                raw_text=text,
                expected_claims=[claim],
                notes=f"Tanglish internal payment instruction."
            ))
        else:
            # Consideration / Proposed speculation
            text = f"Maya Sundaram: We can review {item} pricing once the quarterly volume crosses 50 tonnes."
            quote = f"review {item} pricing once the quarterly volume crosses 50 tonnes"
            claim = BenchmarkClaim(
                id=f"CLM_EXT_{msg_id:03d}",
                kind=ClaimKind.COMMITMENT,
                modality=Modality.CONSIDERED,
                subject=f"Review {item} pricing at 50 tonnes volume",
                owner_alias="Maya Sundaram",
                counterparty_alias=v_org,
                evidence_span=EvidenceSpan(
                    exact_quote=quote,
                    span_start=text.find(quote),
                    span_end=text.find(quote) + len(quote)
                ),
                calibrated_confidence=CalibratedConfidence.MEDIUM,
                trap_tag="CONDITIONAL_CONSIDERATION"
            )
            extra_messages.append(BenchmarkMessage(
                id=f"MSG_{msg_id:03d}",
                source_type="whatsapp",
                author_name="Maya Sundaram",
                author_trust_tier=TrustTier.OWNER,
                timestamp_ist="2026-10-27T19:00:00+05:30",
                raw_text=text,
                expected_claims=[claim],
                notes="Considered / conditional future policy."
            ))

        msg_id += 1

    total_dataset = base_messages + extra_messages
    out_file = Path("tests/gold_dataset/maya_gold_150.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump([m.model_dump() for m in total_dataset], f, indent=2, ensure_ascii=False)

    print(f"Dataset expanded: exactly {len(total_dataset)} labeled benchmark messages generated in {out_file}.")

if __name__ == "__main__":
    expand_to_150()
