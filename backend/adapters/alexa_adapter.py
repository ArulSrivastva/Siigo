"""
Alexa Skill / Voice Assistant Gateway
Implements the thin-client voice skill interface:
- Intent 1: "What needs my attention?" -> Reads urgent Act Now items
- Intent 2: "What is my bus factor score?" -> Speaks continuity readiness score
- Intent 3: "Accept pending task" -> Confirms top review queue item

Strictly restricted: Alexa CANNOT authorize payments or modify charter policies.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.models import AbsenceEvent, Claim
from backend.analyzers import analyze_continuity_health

def handle_alexa_request(db: Session, tenant_id: str, request_body: Dict[str, Any]) -> Dict[str, Any]:
    req = request_body.get("request", {})
    req_type = req.get("type", "IntentRequest")
    intent_name = req.get("intent", {}).get("name", "ReadAttentionItemsIntent")

    speech_output = "Welcome to Siigo. How can I help with operations today?"

    if req_type == "LaunchRequest":
        speech_output = "Siigo continuity active. You can ask: what needs attention, or what is our readiness score."

    elif req_type == "IntentRequest":
        if intent_name == "ReadAttentionItemsIntent":
            health = analyze_continuity_health(db, tenant_id)
            commitments = health.get("commitments_requiring_attention", [])
            spofs = health.get("single_points_of_failure", [])

            if commitments:
                top = commitments[0]["subject"]
                speech_output = f"You have {len(commitments)} urgent items. Most urgent is: {top}."
                if spofs:
                    speech_output += f" Alert: {spofs[0]['subject']}."
            else:
                speech_output = "All commitments are up to date and no urgent operational blocks are detected."

        elif intent_name == "DeclareAbsenceAndTriageIntent":
            # Handles: "I'm unavailable tomorrow. Identify anything that needs attention."
            # Declares absence in backend and compiles immediate attention briefing
            from backend.models import AbsenceEvent
            from backend.handoff_compiler import compile_safe_handoff
            import datetime

            now = datetime.datetime.utcnow()
            expires_at = now + datetime.timedelta(days=1)
            absence = AbsenceEvent(
                tenant_id=tenant_id,
                person_id="Maya Sundaram",
                declared_by=["Maya Sundaram"],
                method="voice_alexa_declared",
                status="active",
                started_at=now,
                auto_expires_at=expires_at
            )
            db.add(absence)
            db.commit()
            db.refresh(absence)

            handoff = compile_safe_handoff(db, tenant_id, absence.id, recipient_id="Rajesh")
            act_now_count = len(handoff["buckets"]["act_now"])
            needs_approval_count = len(handoff["buckets"]["needs_approval"])
            cannot_see_count = len(handoff["buckets"]["what_i_cannot_see"])

            speech_output = (
                f"Absence recorded for tomorrow under your Continuity Charter. "
                f"I've generated a Safe Handoff for Rajesh with {act_now_count} immediate commitments, "
                f"{needs_approval_count} items requiring delegated approval, and flagged {cannot_see_count} coverage gaps."
            )

        elif intent_name == "ReadReadinessScoreIntent":
            health = analyze_continuity_health(db, tenant_id)
            score = health.get("readiness_score", 100)
            speech_output = f"Your current continuity readiness score is {score} out of 100."

        elif intent_name == "AMAZON.HelpIntent":
            speech_output = "You can ask for what needs attention, or check your readiness score."

        elif intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
            speech_output = "Goodbye."

    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech_output
            },
            "shouldEndSession": True
        }
    }
