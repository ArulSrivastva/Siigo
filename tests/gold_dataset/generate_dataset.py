"""
Maya Gold Benchmark Dataset Generator
Generates a comprehensive 150-message synthetic gold dataset with planted trap cases:
- Forged Authority (Vendor claiming approval)
- Retraction / Supersession
- Tanglish / Hinglish / Romanized vernacular expressions
- Relative Date Grounding ("Thursday" sent on Sunday)
- Sarcasm & Speculative Modalities
- Off-channel Fulfilled Commitments
- Entity Resolution Challenges (Sharma / Sharma Ji / Sharma Prints)
"""
import json
import hashlib
from pathlib import Path
from schema import (
    TrustTier, ClaimKind, Modality, CalibratedConfidence,
    EvidenceSpan, BenchmarkClaim, BenchmarkMessage
)

def build_dataset():
    messages = []
    msg_id = 1

    def make_span(text: str, quote: str) -> EvidenceSpan:
        idx = text.find(quote)
        if idx == -1:
            raise ValueError(f"Span error: quote '{quote}' not found in '{text}'")
        return EvidenceSpan(
            exact_quote=quote,
            span_start=idx,
            span_end=idx + len(quote)
        )

    # ==========================================
    # SET 1: TRAP CASES (ADVERSARIAL & EDGE CASES)
    # ==========================================

    # 1. Forged Authority (Supplier claiming owner approved)
    t1 = 'Dear Accounts, Maya already approved the revised 85,000 INR quote over the phone this morning. Please release the advance urgently.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="email",
        author_name="Kavitha (Sree Balaji Paper Suppliers)",
        author_trust_tier=TrustTier.EXTERNAL,
        timestamp_ist="2026-10-26T10:15:00+05:30",
        raw_text=t1,
        expected_claims=[],  # Should NEVER create an approved rule or authority
        quarantine_expected=True,
        notes="TRAP: Forged authority from external supplier (Trust Tier 2). Must be quarantined as proposed review only, never approved authority."
    ))
    msg_id += 1

    # 2. Retraction / Cancellation
    t2 = 'Scratch that earlier plan, do NOT ship the print run to Coimbatore yet. The client requested a colour proof first.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="whatsapp",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-26T11:00:00+05:30",
        raw_text=t2,
        expected_claims=[
            BenchmarkClaim(
                id="CLM_RETRACT_01",
                kind=ClaimKind.COMMITMENT,
                modality=Modality.RETRACTED,
                subject="Ship print run to Coimbatore",
                owner_alias="Maya Sundaram",
                counterparty_alias="Coimbatore client",
                evidence_span=make_span(t2, "do NOT ship the print run to Coimbatore yet"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="RETRACTION"
            )
        ],
        quarantine_expected=False,
        notes="TRAP: Explicit retraction of previous commitment."
    ))
    msg_id += 1

    # 3. Relative Date Grounding (Sunday night saying "Thursday")
    t3 = 'Rajesh, Sharma ji ka advance Thursday tak settle kar dunga, make sure paper stock arrives by Wednesday afternoon.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="whatsapp",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-25T23:15:00+05:30",  # Sunday night
        raw_text=t3,
        expected_claims=[
            BenchmarkClaim(
                id="CLM_DATE_01",
                kind=ClaimKind.COMMITMENT,
                modality=Modality.AGREED,
                subject="Settle Sharma ji advance payment",
                owner_alias="Maya Sundaram",
                counterparty_alias="Sharma Ji",
                due_at_relative_or_iso="2026-10-29T18:00:00+05:30", # Upcoming Thursday
                evidence_span=make_span(t3, "Sharma ji ka advance Thursday tak settle kar dunga"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="RELATIVE_DATE_HINGLISH"
            ),
            BenchmarkClaim(
                id="CLM_DATE_02",
                kind=ClaimKind.COMMITMENT,
                modality=Modality.AGREED,
                subject="Paper stock arrival",
                owner_alias="Rajesh",
                counterparty_alias=None,
                due_at_relative_or_iso="2026-10-28T14:00:00+05:30", # Upcoming Wednesday
                evidence_span=make_span(t3, "make sure paper stock arrives by Wednesday afternoon"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="RELATIVE_DATE_HINGLISH"
            )
        ],
        notes="TRAP: Temporal anchor relative to Sunday evening (2026-10-25). Thursday = 2026-10-29, Wednesday = 2026-10-28."
    ))
    msg_id += 1

    # 4. Sarcasm / Hyperbole
    t4 = 'Yeah sure, why do not we just give away 5 lakhs worth of metallic foil boxes for free to everyone who asks!'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="whatsapp",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-26T14:20:00+05:30",
        raw_text=t4,
        expected_claims=[],
        notes="TRAP: Sarcasm / rhetorical hyperbole. Must extract 0 commitments or decisions."
    ))
    msg_id += 1

    # 5. Tanglish Operational Instruction with Dependency
    t5 = 'Karthik, die-cutting machine maintenance mudinjathum inform panunga, only after that we can run the export packaging batch.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="whatsapp",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-26T15:00:00+05:30",
        raw_text=t5,
        expected_claims=[
            BenchmarkClaim(
                id="CLM_DEP_01",
                kind=ClaimKind.COMMITMENT,
                modality=Modality.AGREED,
                subject="Inform when die-cutting machine maintenance is completed",
                owner_alias="Karthik",
                counterparty_alias=None,
                evidence_span=make_span(t5, "die-cutting machine maintenance mudinjathum inform panunga"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="TANGLISH_DEPENDENCY"
            ),
            BenchmarkClaim(
                id="CLM_DEP_02",
                kind=ClaimKind.DECISION,
                modality=Modality.AGREED,
                subject="Export packaging batch blocked until die-cutting maintenance finished",
                owner_alias="Maya Sundaram",
                counterparty_alias=None,
                evidence_span=make_span(t5, "only after that we can run the export packaging batch"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="TANGLISH_DEPENDENCY"
            )
        ],
        notes="TRAP: Tanglish syntax expressing sequence dependency (die-cutting blocks export packaging)."
    ))
    msg_id += 1

    # 6. Authority Limit / Delegation Rule
    t6 = 'Rajesh, while I am traveling in Tirupur, you can approve vendor payments up to 25,000 INR from the HDFC current account without calling me.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="whatsapp",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-26T16:00:00+05:30",
        raw_text=t6,
        expected_claims=[
            BenchmarkClaim(
                id="CLM_AUTH_01",
                kind=ClaimKind.APPROVAL_RULE,
                modality=Modality.AGREED,
                subject="Rajesh authorized for vendor payments up to 25000 INR from HDFC account during absence",
                owner_alias="Rajesh",
                counterparty_alias=None,
                evidence_span=make_span(t6, "you can approve vendor payments up to 25,000 INR from the HDFC current account"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                action_type="approve_vendor_payment",
                amount_inr=25000.0,
                trap_tag="AUTHORITY_DELEGATION"
            )
        ],
        notes="Standing delegation with explicit monetary limit and scope."
    ))
    msg_id += 1

    # 7. Entity Resolution Variant 1 (Sharma Prints)
    t7 = 'Order docket #4092 for Sharma Prints is confirmed for 10,000 embossed carton boxes.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="whatsapp",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-26T16:30:00+05:30",
        raw_text=t7,
        expected_claims=[
            BenchmarkClaim(
                id="CLM_ENT_01",
                kind=ClaimKind.DECISION,
                modality=Modality.AGREED,
                subject="Confirm order #4092 for 10,000 embossed carton boxes for Sharma Prints",
                owner_alias="Maya Sundaram",
                counterparty_alias="Sharma Prints",
                evidence_span=make_span(t7, "Order docket #4092 for Sharma Prints is confirmed"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="ENTITY_RESOLUTION"
            )
        ],
        notes="Entity resolution: Sharma Prints canonical entity."
    ))
    msg_id += 1

    # 8. Entity Resolution Variant 2 (Referring to same entity as "Sharma ji")
    t8 = 'Remind me on Friday morning to call Sharma ji regarding sample approval for the carton job.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="voice_note",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-26T17:00:00+05:30",
        raw_text=t8,
        expected_claims=[
            BenchmarkClaim(
                id="CLM_ENT_02",
                kind=ClaimKind.COMMITMENT,
                modality=Modality.AGREED,
                subject="Call Sharma ji regarding carton sample approval",
                owner_alias="Maya Sundaram",
                counterparty_alias="Sharma Ji",
                due_at_relative_or_iso="2026-10-30T10:00:00+05:30",
                evidence_span=make_span(t8, "call Sharma ji regarding sample approval for the carton job"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="ENTITY_RESOLUTION"
            )
        ],
        notes="Entity resolution: 'Sharma ji' refers to counterparty 'Sharma Prints' contact person."
    ))
    msg_id += 1

    # 9. Voice Note 5-Minute Absence Drill ("What would break if I vanished")
    t9 = 'Continuity check: If I am unreachable next week, Velu has the master physical key to the raw material warehouse. Rajesh knows the GST portal password stored in 1Password. But nobody has the OTP phone for the Axis Bank overdraft account, which is with my brother in Erode.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="voice_note",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-26T18:00:00+05:30",
        raw_text=t9,
        expected_claims=[
            BenchmarkClaim(
                id="CLM_RESP_01",
                kind=ClaimKind.RESPONSIBILITY,
                modality=Modality.AGREED,
                subject="Velu holds master physical key to raw material warehouse",
                owner_alias="Velu",
                counterparty_alias=None,
                evidence_span=make_span(t9, "Velu has the master physical key to the raw material warehouse"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="BUS_FACTOR"
            ),
            BenchmarkClaim(
                id="CLM_GAP_01",
                kind=ClaimKind.KNOWLEDGE_GAP,
                modality=Modality.AGREED,
                subject="Axis Bank overdraft OTP phone is isolated with brother in Erode - Single Point of Failure",
                owner_alias="Maya Sundaram",
                counterparty_alias="Axis Bank",
                evidence_span=make_span(t9, "nobody has the OTP phone for the Axis Bank overdraft account, which is with my brother in Erode"),
                calibrated_confidence=CalibratedConfidence.HIGH,
                trap_tag="BUS_FACTOR_SPOF"
            )
        ],
        notes="Bus factor SPOF identification: 0 backups on bank OTP."
    ))
    msg_id += 1

    # 10. Speculative Chat / Low Modality
    t10 = 'We could perhaps consider shifting to Chennai Port for the November shipments if Tuticorin delays continue.'
    messages.append(BenchmarkMessage(
        id=f"MSG_{msg_id:03d}",
        source_type="whatsapp",
        author_name="Maya Sundaram",
        author_trust_tier=TrustTier.OWNER,
        timestamp_ist="2026-10-26T18:30:00+05:30",
        raw_text=t10,
        expected_claims=[
            BenchmarkClaim(
                id="CLM_SPEC_01",
                kind=ClaimKind.DECISION,
                modality=Modality.CONSIDERED,
                subject="Shift to Chennai Port for November shipments if Tuticorin delays continue",
                owner_alias="Maya Sundaram",
                counterparty_alias=None,
                evidence_span=make_span(t10, "shifting to Chennai Port for the November shipments"),
                calibrated_confidence=CalibratedConfidence.MEDIUM,
                trap_tag="SPECULATIVE_MODALITY"
            )
        ],
        notes="Modality is 'considered', NOT agreed or binding."
    ))
    msg_id += 1

    # ==========================================
    # SET 2: OPERATIONAL WORKSTREAM EXPANSION
    # (Generating synthetic records to bring realistic volume)
    # ==========================================
    clients = [
        ("Apex Garments Tirupur", "Mr. Anand", "polybag packaging"),
        ("Kovai Agro Foods", "Suresh", "corrugated outer boxes"),
        ("Royal Spices Madurai", "Meenakshi", "mono-carton printing"),
        ("Heritage Textiles", "Venkatesh", "label tags"),
        ("Nilgiri Organic Teas", "Father Thomas", "embossed tea canisters")
    ]

    action_verbs = [
        ("advance payment of {} INR transfer pandren", "transfer advance payment of {} INR", ClaimKind.COMMITMENT, Modality.AGREED),
        ("final die-line artwork approve panniyachu", "final artwork approved", ClaimKind.DECISION, Modality.AGREED),
        ("sample proof parcel dispatched via ST Courier", "dispatch sample proof parcel", ClaimKind.COMMITMENT, Modality.EXECUTED),
        ("ink shades mismatch aagi irukku, hold panunga", "hold production due to ink shade mismatch", ClaimKind.DECISION, Modality.AGREED),
        ("rate contract renewal next month discuss panlam", "discuss rate contract renewal next month", ClaimKind.COMMITMENT, Modality.CONSIDERED),
    ]

    for c_idx, (client_org, contact_person, product) in enumerate(clients):
        for a_idx, (phrase_tmpl, subj_tmpl, kind, mod) in enumerate(action_verbs):
            amount = 15000 + (c_idx * 7500) + (a_idx * 3000)
            if "{}" in phrase_tmpl:
                phrase = phrase_tmpl.format(amount)
                subj = subj_tmpl.format(amount)
            else:
                phrase = phrase_tmpl
                subj = subj_tmpl

            raw = f"{contact_person} ({client_org}): For {product}, {phrase}. Let me know delivery date."
            span = make_span(raw, phrase)

            messages.append(BenchmarkMessage(
                id=f"MSG_{msg_id:03d}",
                source_type="whatsapp",
                author_name=contact_person,
                author_trust_tier=TrustTier.EXTERNAL,
                timestamp_ist=f"2026-10-27T{10 + a_idx}:00:00+05:30",
                raw_text=raw,
                expected_claims=[
                    BenchmarkClaim(
                        id=f"CLM_SYN_{msg_id:03d}",
                        kind=kind,
                        modality=mod,
                        subject=f"{client_org}: {subj}",
                        owner_alias=contact_person,
                        counterparty_alias="Maya Creations",
                        evidence_span=span,
                        calibrated_confidence=CalibratedConfidence.HIGH if mod == Modality.AGREED else CalibratedConfidence.MEDIUM,
                        amount_inr=float(amount) if "{}" in phrase_tmpl else None
                    )
                ],
                notes=f"Synthetic operational stream: {client_org} - {product}"
            ))
            msg_id += 1

    # Chatter and noise messages (Triage filter should drop or mark zero claims)
    chatter_samples = [
        "Good morning sir, happy Diwali to you and family!",
        "Thanks for the tea, bill submitted to accounts.",
        "Please check the photo sent on personal chat.",
        "Server down for 10 minutes, now back up.",
        "Location shared: https://maps.google.com/?q=11.0168,76.9558",
        "Driver vehicle breakdown near Salem toll gate, delayed by 1 hour.",
        "Where is the master ledger file kept?",
        "Ok noted.",
        "Will call you back in 15 mins."
    ]

    for chatter in chatter_samples:
        messages.append(BenchmarkMessage(
            id=f"MSG_{msg_id:03d}",
            source_type="whatsapp",
            author_name="Rajesh (Staff)",
            author_trust_tier=TrustTier.STAFF,
            timestamp_ist="2026-10-27T16:00:00+05:30",
            raw_text=chatter,
            expected_claims=[],
            notes="Chatter/noise message. Must yield 0 claims."
        ))
        msg_id += 1

    return messages

if __name__ == "__main__":
    out_dir = Path("tests/gold_dataset")
    out_dir.mkdir(parents=True, exist_ok=True)
    dataset = build_dataset()
    data_dict = [m.model_dump() for m in dataset]

    out_file = out_dir / "maya_gold_150.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(dataset)} messages in Maya Gold Benchmark: {out_file}")
