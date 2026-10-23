"""
Automated Voiceover Generator for Siigo 3-Minute Live Demo Runbook
Synthesizes professional WAV voiceover tracks timed exactly to the 8 demo steps.
Uses Windows native speech synthesis (SAPI5).
"""
import os
import pyttsx3

VOICEOVER_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voiceover")
os.makedirs(VOICEOVER_DIR, exist_ok=True)

SCRIPTS = {
    "01_setup_problem": {
        "timing": "0:00 - 0:30",
        "title": "Business Problem Setup",
        "text": (
            "Maya owns the business. Rajesh must cover for her tomorrow. "
            "Instead of asking Rajesh to search through messages and guess what matters, "
            "we are going to generate an evidence-backed handoff."
        )
    },
    "02_walkthrough_run": {
        "timing": "0:30 - 1:05",
        "title": "Running Complete Walkthrough",
        "text": (
            "Let us run the complete walkthrough. "
            "The system ingests the raw order evidence, content-hashes it, and validates the exact quote against the source text. "
            "The Alexa skill processes the absence triage intent, compiles the Safe Handoff for Rajesh, "
            "and automatically evaluates an unauthorized sixty-five thousand rupee payment attempt."
        )
    },
    "03_evidence_grounding": {
        "timing": "1:05 - 1:35",
        "title": "Evidence Grounding & Transparency",
        "text": (
            "Notice the middle panel. We have an immediate commitment: "
            "Confirm order docket forty ninety-two for Sharma Prints, with its exact verbatim source quote and SHA-256 hash. "
            "The important difference is that this is not just an AI summary. "
            "We can trace this commitment back to its exact source text, "
            "and the handoff makes uncertainty visible with honest coverage disclosures."
        )
    },
    "04_financial_limit_deny": {
        "timing": "1:35 - 2:00",
        "title": "Financial Policy Gate Deny",
        "text": (
            "Now look at the financial boundary in the right panel. "
            "Rajesh attempted a sixty-five thousand rupee vendor payment against his twenty-five thousand rupee standing limit. "
            "The Cedar policy engine immediately blocked it with HTTP 403 Forbidden. "
            "Continuity does not mean unlimited autonomy. "
            "Rajesh can inherit responsibility without inheriting unlimited financial authority."
        )
    },
    "05_permitted_request_allow": {
        "timing": "2:00 - 2:25",
        "title": "Permitted Action Authorization",
        "text": (
            "In contrast, let us examine an authorized request: "
            "an eighteen thousand rupee vendor payment, well within Rajesh's twenty-five thousand rupee limit. "
            "The policy engine approves it with HTTP 200, marked AUTHORIZED AND RECORDED. "
            "The system distinguishes an action that exceeds the grant from one that fits within the configured limit, "
            "recording policy approval without pretending to initiate an unmonitored bank wire."
        )
    },
    "06_human_oversight": {
        "timing": "2:25 - 2:45",
        "title": "Evidence Review Queue & Human Control",
        "text": (
            "Next, let us look at human oversight in the Evidence Review Queue. "
            "Here is the Sharma Prints claim with its source quote, character span, and review controls. "
            "Exact quote verification proves that the text matches its source; "
            "human confirmation ensures business decisions remain firmly under owner control."
        )
    },
    "07_closing_payoff": {
        "timing": "2:45 - 3:00",
        "title": "Closing Payoff",
        "text": (
            "Siigo does not replace Maya's judgment. "
            "It preserves context, surfaces commitments, exposes gaps, and helps Rajesh act within defined limits. "
            "The business can keep moving without pretending the system knows everything."
        )
    }
}

def generate_voiceovers():
    print("=" * 65)
    print("GENERATING SYNTHESIZED VOICEOVER TRACKS (WINDOWS SAPI5)")
    print("=" * 65)

    engine = pyttsx3.init()
    # Moderate, clear pacing (155-160 WPM is standard documentary / demo pace)
    engine.setProperty("rate", 155)

    full_text_segments = []

    for key, data in SCRIPTS.items():
        filename = f"{key}.wav"
        filepath = os.path.join(VOICEOVER_DIR, filename)
        print(f"[*] Generating: {filename} [{data['timing']}] - {data['title']}")
        engine.save_to_file(data["text"], filepath)
        full_text_segments.append(f"... ... {data['text']}")

    # Also generate full continuous track
    full_track_path = os.path.join(VOICEOVER_DIR, "full_3min_voiceover.wav")
    print(f"[*] Generating: full_3min_voiceover.wav (Combined continuous narration)")
    combined_script = " ".join(full_text_segments)
    engine.save_to_file(combined_script, full_track_path)

    engine.runAndWait()
    print("=" * 65)
    print(f"SUCCESS: All voiceover tracks saved in: {VOICEOVER_DIR}")
    print("=" * 65)

if __name__ == "__main__":
    generate_voiceovers()
