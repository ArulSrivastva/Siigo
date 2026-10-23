"""
High-Fidelity Automated Video Recorder with Visible Animated Cursor
Paces video recording to match the 2m 30s - 2m 45s voiceover narration.
Renders an amber beacon pointer cursor with click pulses and realistic human pacing.
"""
import os
import time
import shutil
from playwright.sync_api import sync_playwright

WORKSPACE = os.path.dirname(os.path.dirname(__file__))
RECORDINGS_DIR = os.path.join(WORKSPACE, "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

TARGET_VIDEO_PATH = os.path.join(RECORDINGS_DIR, "siigo_3min_demo_walkthrough.webm")

CURSOR_INJECTION_SCRIPT = """
(() => {
    function inject() {
        if (document.getElementById('virtual-cursor-root')) return;
        const container = document.createElement('div');
        container.id = 'virtual-cursor-root';
        container.innerHTML = `
          <div id="virtual-cursor" style="
            position: fixed;
            top: 0; left: 0;
            width: 32px; height: 32px;
            z-index: 2147483647;
            pointer-events: none;
            transform: translate(250px, 150px);
            transition: transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.5));
          ">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 2L21 16.5H11.5L8 24.5L4 2Z" fill="#0F172A" stroke="#FAF9F5" stroke-width="2" stroke-linejoin="round"/>
              <circle cx="10" cy="10" r="5" fill="#F59E0B" fill-opacity="0.9"/>
            </svg>
          </div>
          <style>
            .click-pulse {
              position: fixed;
              width: 36px; height: 36px;
              border-radius: 50%;
              border: 3px solid #F59E0B;
              background: rgba(245, 158, 11, 0.35);
              pointer-events: none;
              z-index: 2147483646;
              animation: pulse-out 0.55s ease-out forwards;
            }
            @keyframes pulse-out {
              0% { transform: scale(0.3); opacity: 1; }
              100% { transform: scale(2.0); opacity: 0; }
            }
          </style>
        `;
        document.body.appendChild(container);
    }
    window.addEventListener('DOMContentLoaded', inject);
    setInterval(inject, 500);

    window.__moveCursor = (x, y) => {
        const c = document.getElementById('virtual-cursor');
        if (c) c.style.transform = `translate(${x}px, ${y}px)`;
    };

    window.__clickPulse = (x, y) => {
        const p = document.createElement('div');
        p.className = 'click-pulse';
        p.style.left = `${x - 18}px`;
        p.style.top = `${y - 18}px`;
        document.body.appendChild(p);
        setTimeout(() => p.remove(), 550);
    };
})();
"""

def move_cursor_to_element(page, selector, offset_x=0, offset_y=0, wait_after=1.0):
    loc = page.locator(selector).first
    if loc.is_visible():
        loc.scroll_into_view_if_needed()
        box = loc.bounding_box()
        if box:
            x = box["x"] + box["width"] / 2 + offset_x
            y = box["y"] + box["height"] / 2 + offset_y
            page.evaluate(f"window.__moveCursor({x}, {y})")
            page.wait_for_timeout(int(wait_after * 1000))
            return x, y
    return None, None

def click_element_with_cursor(page, selector, wait_before=0.5, wait_after=1.5):
    loc = page.locator(selector).first
    loc.scroll_into_view_if_needed()
    box = loc.bounding_box()
    if box:
        x = box["x"] + box["width"] / 2
        y = box["y"] + box["height"] / 2
        page.evaluate(f"window.__moveCursor({x}, {y})")
        page.wait_for_timeout(int(wait_before * 1000))
        page.evaluate(f"window.__clickPulse({x}, {y})")
        loc.click()
        page.wait_for_timeout(int(wait_after * 1000))
        return True
    return False

def record_live_demo():
    print("=" * 70, flush=True)
    print("STARTING HIGH-FIDELITY SCREEN RECORDING WITH VISIBLE CURSOR (1080p)", flush=True)
    print("=" * 70, flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=RECORDINGS_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        page.add_init_script(CURSOR_INJECTION_SCRIPT)

        # ---------------------------------------------------------------------
        # Scene 1: Initial Setup & Business Problem (0:00 - 0:16, ~16s)
        # Matches 01_setup_problem.wav (12.7s)
        # ---------------------------------------------------------------------
        print("[0:00] Scene 1: Loading Siigo Command Center...", flush=True)
        page.goto("http://localhost:3000", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Click Reset button to guarantee pristine state
        print("       Resetting to pristine demo state...", flush=True)
        click_element_with_cursor(page, "button:has-text('Reset')", wait_before=0.4, wait_after=2.0)

        # Move to Maya's absence utterance
        print("[0:05] Hovering over Maya's absence instruction...", flush=True)
        move_cursor_to_element(page, "text=I'm unavailable tomorrow. Identify anything that needs attention.", wait_after=3.5)

        # Move to Tier 0 badge
        print("[0:10] Pointing to Tier 0 Verified authentication badge...", flush=True)
        move_cursor_to_element(page, "text=Tier 0 Verified", wait_after=3.0)

        # Point to active actor dropdown
        move_cursor_to_element(page, "select", wait_after=3.0)

        # ---------------------------------------------------------------------
        # Scene 2: Run Complete Walkthrough (0:16 - 0:41, ~25s)
        # Matches 02_walkthrough_run.wav (22.4s)
        # ---------------------------------------------------------------------
        print("[0:16] Scene 2: Moving cursor to 'Run Complete Demo Walkthrough'...", flush=True)
        move_cursor_to_element(page, "button:has-text('Run Complete Demo Walkthrough')", wait_after=1.5)

        print("[0:18] Clicking 'Run Complete Demo Walkthrough'...", flush=True)
        click_element_with_cursor(page, "button:has-text('Run Complete Demo Walkthrough')", wait_before=0.5, wait_after=1.0)

        # Let the autonomous execution pipeline run
        print("       Waiting for Ingestion, Span Verifier & Alexa Output...", flush=True)
        page.wait_for_selector("text=Confirm order docket #4092 for Sharma Prints", timeout=30000)
        page.wait_for_timeout(3000)

        # Hover over Alexa output bubble
        print("[0:30] Hovering over Alexa Spoken Response...", flush=True)
        move_cursor_to_element(page, "text=ALEXA+ SPOKEN TRIAGE RESPONSE", wait_after=4.0)
        move_cursor_to_element(page, "text=Absence recorded for tomorrow under your Continuity Charter", wait_after=6.0)

        # ---------------------------------------------------------------------
        # Scene 3: Evidence Grounding & Safe Handoff (0:41 - 1:09, ~28s)
        # Matches 03_evidence_grounding.wav (24.6s)
        # ---------------------------------------------------------------------
        print("[0:41] Scene 3: Gliding to Column 2: Safe Handoff Briefing...", flush=True)
        move_cursor_to_element(page, "text=2. Safe Handoff Document", wait_after=2.0)

        # Hover over Sharma Prints commitment
        print("[0:45] Pointing to Sharma Prints commitment in Act Now...", flush=True)
        move_cursor_to_element(page, "text=Confirm order docket #4092 for Sharma Prints", wait_after=5.0)

        # Point to exact verbatim quote
        print("[0:52] Highlighting verbatim source quote substring...", flush=True)
        move_cursor_to_element(page, "text=Order docket #4092 for Sharma Prints is confirmed", wait_after=4.0)

        # Point to quote SHA-256 hash badge
        move_cursor_to_element(page, "text=SHA256:", wait_after=4.0)

        # Scroll down to What I Cannot See
        print("[1:00] Scrolling to 'What I Cannot See' disclosures...", flush=True)
        move_cursor_to_element(page, "text=What I Cannot See", wait_after=3.0)
        move_cursor_to_element(page, "text=Personal non-exported WhatsApp chats", wait_after=5.0)

        # ---------------------------------------------------------------------
        # Scene 4: Financial Boundary Denial (1:09 - 1:38, ~29s)
        # Matches 04_financial_limit_deny.wav (25.9s)
        # ---------------------------------------------------------------------
        print("[1:09] Scene 4: Moving to Column 3: Authority Gate Duel...", flush=True)
        move_cursor_to_element(page, "text=3. Authority Gate Duel", wait_after=3.0)

        # Hover over Attack Test A button
        print("[1:14] Pointing to 'Attack Test A — Over-Limit (INR 65,000)'...", flush=True)
        move_cursor_to_element(page, "text=Over-Limit (₹65,000)", wait_after=4.0)

        # Hover over the red DECISION: DENY card
        print("[1:20] Inspecting DENY (HTTP 403) policy banner...", flush=True)
        move_cursor_to_element(page, "text=DECISION: DENY", wait_after=5.0)

        # Hover over ceiling explanation
        print("[1:27] Pointing to ceiling explanation: exceeds INR 25,000...", flush=True)
        move_cursor_to_element(page, "text=exceeds delegation ceiling", wait_after=5.0)
        move_cursor_to_element(page, "text=STATUS: BLOCKED", wait_after=4.0)

        # ---------------------------------------------------------------------
        # Scene 5: Permitted Request Authorization (1:38 - 2:08, ~30s)
        # Matches 05_permitted_request_allow.wav (27.6s)
        # ---------------------------------------------------------------------
        print("[1:38] Scene 5: Moving to 'Permitted Test B — Authorized (INR 18,000)'...", flush=True)
        move_cursor_to_element(page, "text=Authorized (₹18,000)", wait_after=3.0)

        print("[1:43] Clicking 'Permitted Test B'...", flush=True)
        click_element_with_cursor(page, "button:has-text('Authorized (₹18,000)')", wait_before=0.5, wait_after=2.0)

        # Verify ALLOW decision appears
        print("[1:47] Inspecting ALLOW (HTTP 200) policy card...", flush=True)
        page.wait_for_selector("text=DECISION: ALLOW", timeout=10000)
        move_cursor_to_element(page, "text=DECISION: ALLOW", wait_after=4.0)

        # Hover over status AUTHORIZED_AND_RECORDED
        print("[1:54] Highlighting AUTHORIZED_AND_RECORDED state...", flush=True)
        move_cursor_to_element(page, "text=STATUS: AUTHORIZED_AND_RECORDED", wait_after=6.0)

        # Hover over hash-chained audit trail
        print("[2:02] Showing cryptographic hash-chained audit log...", flush=True)
        move_cursor_to_element(page, "text=Hash-Chained Audit Trail", wait_after=5.0)

        # ---------------------------------------------------------------------
        # Scene 6: Human Oversight in Evidence Review Queue (2:08 - 2:32, ~24s)
        # Matches 06_human_oversight.wav (20.4s)
        # ---------------------------------------------------------------------
        print("[2:08] Scene 6: Navigating to Evidence Review Queue in sidebar...", flush=True)
        move_cursor_to_element(page, "button:has-text('Evidence Review Queue')", wait_after=2.0)
        click_element_with_cursor(page, "button:has-text('Evidence Review Queue')", wait_before=0.4, wait_after=2.0)

        page.wait_for_selector("text=Evidence & Approval Review Queue", timeout=10000)

        # Point to the 3-stage lifecycle flow
        print("[2:14] Pointing to Proposed -> Verified -> Confirmed stages...", flush=True)
        move_cursor_to_element(page, "text=Proposed", wait_after=2.5)
        move_cursor_to_element(page, "text=Verified", wait_after=2.5)
        move_cursor_to_element(page, "text=Confirmed", wait_after=3.0)

        # Hover over the Sharma Prints claim in review
        print("[2:22] Inspecting Sharma Prints verified citation card...", flush=True)
        move_cursor_to_element(page, "text=Confirm order docket #4092 for Sharma Prints", wait_after=5.0)

        # ---------------------------------------------------------------------
        # Scene 7: Return to Simulation & Closing Payoff (2:32 - 2:48, ~16s)
        # Matches 07_closing_payoff.wav (15.1s)
        # ---------------------------------------------------------------------
        print("[2:32] Scene 7: Returning to Alexa+ Live Simulation for closing payoff...", flush=True)
        move_cursor_to_element(page, "button:has-text('Alexa+ Live Simulation')", wait_after=2.0)
        click_element_with_cursor(page, "button:has-text('Alexa+ Live Simulation')", wait_before=0.4, wait_after=2.0)

        print("[2:38] Centering on the full command center layout...", flush=True)
        move_cursor_to_element(page, "text=Alexa+ Live Continuity Simulation", wait_after=3.0)
        page.evaluate("window.__moveCursor(960, 500)")
        page.wait_for_timeout(4000)

        print("[2:48] Demo complete! Finalizing 1080p video recording...", flush=True)
        video_obj = page.video
        context.close()
        browser.close()

        video_path = video_obj.path() if video_obj else None
        if video_path and os.path.exists(video_path):
            if os.path.exists(TARGET_VIDEO_PATH):
                os.remove(TARGET_VIDEO_PATH)
            shutil.move(video_path, TARGET_VIDEO_PATH)
            size_mb = os.path.getsize(TARGET_VIDEO_PATH) / (1024 * 1024)
            print("=" * 70, flush=True)
            print(f"SUCCESS: Paced 1080p Video Recorded ({size_mb:.2f} MB)", flush=True)
            print(f"Location: {TARGET_VIDEO_PATH}", flush=True)
            print("=" * 70, flush=True)
            return TARGET_VIDEO_PATH
        else:
            print("ERROR: Video file was not generated!", flush=True)
            return None

if __name__ == "__main__":
    record_live_demo()
