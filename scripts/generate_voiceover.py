"""
Automated Voiceover Generator for Siigo Live Demo Video
Paced & timed down to the exact millisecond to match the 1080p video recording.
Assembles:
1. Individual scene WAV tracks: 01_setup through 07_payoff
2. A single continuous, frame-exact master track: synced_video_master_voiceover.wav (111.72 seconds)
"""
import os
import wave
import pyttsx3

WORKSPACE = os.path.dirname(os.path.dirname(__file__))
VOICEOVER_DIR = os.path.join(WORKSPACE, "voiceover")
os.makedirs(VOICEOVER_DIR, exist_ok=True)

# Scene scripts and their exact target start timestamp in the 111.72s video
SCENE_CONFIG = [
    {
        "id": "01_setup_problem",
        "start_sec": 0.8,
        "title": "Business Problem Setup",
        "text": (
            "Maya owns the business, and Rajesh must cover for her tomorrow. "
            "Instead of asking Rajesh to search through messages and guess what matters, "
            "Siigo generates a governed, evidence-backed handoff."
        )
    },
    {
        "id": "02_walkthrough_run",
        "start_sec": 17.0,
        "title": "Running Complete Walkthrough",
        "text": (
            "Let us run the complete walkthrough. "
            "The system ingests the raw order message, verifies the exact quote, "
            "and processes the Alexa triage intent, compiling an immediate handoff for Rajesh."
        )
    },
    {
        "id": "03_evidence_grounding",
        "start_sec": 34.0,
        "title": "Evidence Grounding & Transparency",
        "text": (
            "In the handoff, we see the immediate commitment for Sharma Prints, "
            "grounded in its exact verbatim quote and SHA-256 hash. "
            "The handoff also exposes operational gaps in What I Cannot See."
        )
    },
    {
        "id": "04_financial_limit_deny",
        "start_sec": 50.0,
        "title": "Financial Policy Gate Deny",
        "text": (
            "Now look at the financial boundary in Column three. "
            "Rajesh attempted a sixty-five thousand rupee payment against his twenty-five thousand rupee ceiling. "
            "The Cedar policy gate blocked it with HTTP 403."
        )
    },
    {
        "id": "05_permitted_request_allow",
        "start_sec": 68.0,
        "title": "Permitted Action Authorization",
        "text": (
            "In contrast, look at an authorized request: "
            "an eighteen thousand rupee payment within Rajesh's limit. "
            "The policy engine approves it with HTTP 200, "
            "marked AUTHORIZED AND RECORDED in the audit trail."
        )
    },
    {
        "id": "06_human_oversight",
        "start_sec": 86.0,
        "title": "Evidence Review Queue & Human Control",
        "text": (
            "In the Evidence Review Queue, human oversight is enforced. "
            "Exact quote matching proves the text was said, "
            "while the owner confirms the business decision through the three-stage lifecycle."
        )
    },
    {
        "id": "07_closing_payoff",
        "start_sec": 102.0,
        "title": "Closing Payoff",
        "text": (
            "Siigo preserves context, surfaces commitments, exposes gaps, "
            "and lets the business keep moving within safe limits."
        )
    }
]

VIDEO_TOTAL_SECONDS = 111.72

def generate_scene_voiceovers():
    print("=" * 70)
    print("1. SYNTHESIZING SCENE VOICEOVER TRACKS MATCHED TO VIDEO TIMESTAMPS")
    print("=" * 70)

    engine = pyttsx3.init()
    engine.setProperty("rate", 160)

    # Queue all speech outputs
    for s in SCENE_CONFIG:
        path = os.path.join(VOICEOVER_DIR, f"{s['id']}.wav")
        print(f"[*] Queuing: {s['id']}.wav (Target video start: {s['start_sec']}s)")
        engine.save_to_file(s["text"], path)

    engine.runAndWait()
    print("All individual scene audio files synthesized successfully.")

def assemble_master_track():
    print("=" * 70)
    print(f"2. ASSEMBLING FRAME-EXACT MASTER AUDIO TRACK ({VIDEO_TOTAL_SECONDS:.2f}s)")
    print("=" * 70)

    sample_rate = 22050
    channels = 1
    sample_width = 2
    bytes_per_second = sample_rate * channels * sample_width
    total_expected_bytes = int(VIDEO_TOTAL_SECONDS * bytes_per_second)

    # Initialize complete master buffer with silence (0x00)
    master_buffer = bytearray(total_expected_bytes)

    for s in SCENE_CONFIG:
        path = os.path.join(VOICEOVER_DIR, f"{s['id']}.wav")
        with wave.open(path, "rb") as w:
            n_frames = w.getnframes()
            frames = w.readframes(n_frames)
            duration_s = n_frames / float(sample_rate)

        start_byte = int(s["start_sec"] * bytes_per_second)
        end_byte = start_byte + len(frames)

        # Place into master buffer
        if end_byte <= total_expected_bytes:
            master_buffer[start_byte:end_byte] = frames
            print(f"  + Injected {s['id']:25s} | Start: {s['start_sec']:5.1f}s | Duration: {duration_s:4.1f}s")
        else:
            # Clip if beyond video bounds
            avail = total_expected_bytes - start_byte
            master_buffer[start_byte:total_expected_bytes] = frames[:avail]
            print(f"  + Injected (clipped) {s['id']:25s} | Start: {s['start_sec']:5.1f}s")

    # Write out master track
    master_path = os.path.join(VOICEOVER_DIR, "synced_video_master_voiceover.wav")
    with wave.open(master_path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        w.writeframes(bytes(master_buffer))

    # Also update full_3min_voiceover.wav with this master track
    compat_path = os.path.join(VOICEOVER_DIR, "full_3min_voiceover.wav")
    with wave.open(compat_path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(sample_rate)
        w.writeframes(bytes(master_buffer))

    size_mb = os.path.getsize(master_path) / (1024 * 1024)
    print("=" * 70)
    print(f"MASTER TRACK CREATED: {size_mb:.2f} MB")
    print(f"Location: {master_path}")
    print(f"Total Duration: {VIDEO_TOTAL_SECONDS:.2f} seconds (100% video-synchronized)")
    print("=" * 70)

if __name__ == "__main__":
    generate_scene_voiceovers()
    assemble_master_track()
