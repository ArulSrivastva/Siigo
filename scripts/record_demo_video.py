"""
High-Fidelity Automated Video Recorder with Visible Animated Cursor
Paced exactly to match the 160-second synchronized master timeline:
- Scene 0 (0:00 - 0:48, 48s): Continuity Overview Dashboard (Intro Pitch)
- Scene 1 (0:48 - 1:04, 16s): Transition to Alexa+ Live Simulation & Setup
- Scene 2 (1:04 - 1:21, 17s): Run Autonomous Walkthrough Pipeline
- Scene 3 (1:21 - 1:37, 16s): Evidence Grounding & Safe Handoff
- Scene 4 (1:37 - 1:55, 18s): Authority Gate Denial (₹65,000 Over-Limit)
- Scene 5 (1:55 - 2:13, 18s): Permitted Action Authorization (₹18,000 Allow)
- Scene 6 (2:13 - 2:29, 16s): Human Oversight in Evidence Review Queue
- Scene 7 (2:29 - 2:40, 11s): Closing Payoff & Continuity Guarantee
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
            transform: translate(350px, 200px);
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
    try:
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
    except Exception as e:
        pass
    return None, None

def click_element_with_cursor(page, selector, wait_before=0.5, wait_after=1.5):
    try:
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
    except Exception as e:
        pass
    return False

def record_live_demo():
    print("=" * 70, flush=True)
    print("STARTING 160-SECOND SYNCHRONIZED DEMO RECORDING (1080p)", flush=True)
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
        # Scene 0: Pitch & Continuity Overview (0:00 - 0:48, 48s)
        # Matches 00_intro_pitch.wav (47.4s)
        # ---------------------------------------------------------------------
        print("[0:00] Scene 0: Loading Continuity Overview Dashboard...", flush=True)
        page.goto("http://localhost:3000", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Ensure we are on Overview tab
        click_element_with_cursor(page, "button:has-text('Continuity Overview')", wait_before=0.3, wait_after=1.5)

        print("[0:05] Showing main value proposition...", flush=True)
        move_cursor_to_element(page, "text=Your business, still moving.", wait_after=4.0)

        print("[0:12] Highlighting Continuity Readiness Score...", flush=True)
        move_cursor_to_element(page, "text=Continuity Score", wait_after=5.0)
        move_cursor_to_element(page, "text=82%", wait_after=5.0)

        print("[0:24] Pointing out single points of failure (Maya Sundaram)...", flush=True)
        move_cursor_to_element(page, "text=Key Person Concentration", wait_after=5.0)
        move_cursor_to_element(page, "text=Maya Sundaram", wait_after=6.0)

        print("[0:36] Pointing to Fragility metrics and authority limits...", flush=True)
        move_cursor_to_element(page, "text=Financial Ceiling", wait_after=4.0)
        move_cursor_to_element(page, "text=INR 25,000", wait_after=4.0)

        print("[0:44] Gliding cursor towards sidebar 'Alexa+ Live Simulation'...", flush=True)
        move_cursor_to_element(page, "button:has-text('Alexa+ Live Simulation')", wait_after=3.5)

        # ---------------------------------------------------------------------
        # Scene 1: Transition to Live Simulation & Setup (0:48 - 1:04, 16s)
        # Matches 01_setup_problem.wav (13.0s)
        # ---------------------------------------------------------------------
        print("[0:48] Scene 1: Clicking into Alexa+ Live Simulation...", flush=True)
        click_element_with_cursor(page, "button:has-text('Alexa+ Live Simulation')", wait_before=0.3, wait_after=1.5)

        # Click Reset button to guarantee pristine state
        print("[0:51] Resetting simulation environment...", flush=True)
        click_element_with_cursor(page, "button:has-text('Reset')", wait_before=0.4, wait_after=2.0)

        # Move to Maya's absence instruction
        print("[0:55] Hovering over Maya's absence instruction...", flush=True)
        move_cursor_to_element(page, "text=I'm unavailable tomorrow. Identify anything that needs attention.", wait_after=4.0)

        # Move to Tier 0 badge
        print("[1:00] Pointing to Tier 0 Verified authentication badge...", flush=True)
        move_cursor_to_element(page, "text=Tier 0 Verified", wait_after=3.5)

        # ---------------------------------------------------------------------
        # Scene 2: Run Complete Walkthrough (1:04 - 1:21, 17s)
        # Matches 02_walkthrough_run.wav (13.1s)
        # ---------------------------------------------------------------------
        print("[1:04] Scene 2: Moving cursor to 'Run Complete Demo Walkthrough'...", flush=True)
        move_cursor_to_element(page, "button:has-text('Run Complete Demo Walkthrough')", wait_after=1.5)

        print("[1:06] Triggering autonomous walkthrough...", flush=True)
        click_element_with_cursor(page, "button:has-text('Run Complete Demo Walkthrough')", wait_before=0.3, wait_after=1.0)

        # Wait for the autonomous execution pipeline to complete
        print("       Waiting for Ingestion, Span Verifier & Alexa Output...", flush=True)
        page.wait_for_selector("text=Confirm order docket #4092 for Sharma Prints", timeout=30000)
        page.wait_for_timeout(2000)

        # Hover over Alexa output bubble
        print("[1:14] Hovering over Alexa Spoken Response...", flush=True)
        move_cursor_to_element(page, "text=ALEXA+ SPOKEN TRIAGE RESPONSE", wait_after=3.0)
        move_cursor_to_element(page, "text=Absence recorded for tomorrow under your Continuity Charter", wait_after=4.0)

        # ---------------------------------------------------------------------
        # Scene 3: Evidence Grounding & Safe Handoff (1:21 - 1:37, 16s)
        # Matches 03_evidence_grounding.wav (13.5s)
        # ---------------------------------------------------------------------
        print("[1:21] Scene 3: Gliding to Column 2: Safe Handoff Briefing...", flush=True)
        move_cursor_to_element(page, "text=2. Safe Handoff Document", wait_after=1.5)

        # Hover over Sharma Prints commitment
        print("[1:23] Pointing to Sharma Prints commitment in Act Now...", flush=True)
        move_cursor_to_element(page, "text=Confirm order docket #4092 for Sharma Prints", wait_after=3.5)

        # Point to exact verbatim quote
        print("[1:27] Highlighting verbatim source quote substring...", flush=True)
        move_cursor_to_element(page, "text=Order docket #4092 for Sharma Prints is confirmed", wait_after=3.5)

        # Point to quote SHA-256 hash badge
        move_cursor_to_element(page, "text=SHA256:", wait_after=2.5)

        # Scroll to What I Cannot See
        print("[1:33] Pointing to 'What I Cannot See' disclosures...", flush=True)
        move_cursor_to_element(page, "text=What I Cannot See", wait_after=2.0)
        move_cursor_to_element(page, "text=Personal non-exported WhatsApp chats", wait_after=2.0)

        # ---------------------------------------------------------------------
        # Scene 4: Financial Boundary Denial (1:37 - 1:55, 18s)
        # Matches 04_financial_limit_deny.wav (15.1s)
        # ---------------------------------------------------------------------
        print("[1:37] Scene 4: Moving to Column 3: Authority Gate Duel...", flush=True)
        move_cursor_to_element(page, "text=3. Authority Gate Duel", wait_after=2.0)

        # Hover over Attack Test A button
        print("[1:40] Pointing to 'Attack Test A — Over-Limit (INR 65,000)'...", flush=True)
        move_cursor_to_element(page, "text=Over-Limit (₹65,000)", wait_after=3.0)

        # Hover over the red DECISION: DENY card
        print("[1:44] Inspecting DENY (HTTP 403) policy banner...", flush=True)
        move_cursor_to_element(page, "text=DECISION: DENY", wait_after=4.0)

        # Hover over ceiling explanation
        print("[1:49] Pointing to ceiling explanation: exceeds INR 25,000...", flush=True)
        move_cursor_to_element(page, "text=exceeds delegation ceiling", wait_after=3.5)
        move_cursor_to_element(page, "text=STATUS: BLOCKED", wait_after=2.5)

        # ---------------------------------------------------------------------
        # Scene 5: Permitted Request Authorization (1:55 - 2:13, 18s)
        # Matches 05_permitted_request_allow.wav (14.7s)
        # ---------------------------------------------------------------------
        print("[1:55] Scene 5: Moving to 'Permitted Test B — Authorized (INR 18,000)'...", flush=True)
        move_cursor_to_element(page, "text=Authorized (₹18,000)", wait_after=2.5)

        print("[1:58] Clicking 'Permitted Test B'...", flush=True)
        click_element_with_cursor(page, "button:has-text('Authorized (₹18,000)')", wait_before=0.4, wait_after=1.5)

        # Verify ALLOW decision appears
        print("[2:01] Inspecting ALLOW (HTTP 200) policy card...", flush=True)
        page.wait_for_selector("text=DECISION: ALLOW", timeout=10000)
        move_cursor_to_element(page, "text=DECISION: ALLOW", wait_after=3.0)

        # Hover over status AUTHORIZED_AND_RECORDED
        print("[2:05] Highlighting AUTHORIZED_AND_RECORDED state...", flush=True)
        move_cursor_to_element(page, "text=STATUS: AUTHORIZED_AND_RECORDED", wait_after=3.5)

        # Hover over hash-chained audit trail
        print("[2:09] Showing cryptographic hash-chained audit log...", flush=True)
        move_cursor_to_element(page, "text=Hash-Chained Audit Trail", wait_after=3.5)

        # ---------------------------------------------------------------------
        # Scene 6: Human Oversight in Evidence Review Queue (2:13 - 2:29, 16s)
        # Matches 06_human_oversight.wav (12.2s)
        # ---------------------------------------------------------------------
        print("[2:13] Scene 6: Navigating to Evidence Review Queue in sidebar...", flush=True)
        move_cursor_to_element(page, "button:has-text('Evidence Review Queue')", wait_after=1.5)
        click_element_with_cursor(page, "button:has-text('Evidence Review Queue')", wait_before=0.3, wait_after=1.5)

        page.wait_for_selector("text=Evidence & Approval Review Queue", timeout=10000)

        # Point to the 3-stage lifecycle flow
        print("[2:17] Pointing to Proposed -> Verified -> Confirmed stages...", flush=True)
        move_cursor_to_element(page, "text=Proposed", wait_after=2.0)
        move_cursor_to_element(page, "text=Verified", wait_after=2.0)
        move_cursor_to_element(page, "text=Confirmed", wait_after=2.5)

        # Hover over the Sharma Prints claim in review
        print("[2:24] Inspecting Sharma Prints verified citation card...", flush=True)
        move_cursor_to_element(page, "text=Confirm order docket #4092 for Sharma Prints", wait_after=4.5)

        # ---------------------------------------------------------------------
        # Scene 7: Return to Simulation & Closing Payoff (2:29 - 2:40, 11s)
        # Matches 07_closing_payoff.wav (7.2s)
        # ---------------------------------------------------------------------
        print("[2:29] Scene 7: Returning to Alexa+ Live Simulation for closing payoff...", flush=True)
        move_cursor_to_element(page, "button:has-text('Alexa+ Live Simulation')", wait_after=1.5)
        click_element_with_cursor(page, "button:has-text('Alexa+ Live Simulation')", wait_before=0.3, wait_after=1.5)

        print("[2:33] Centering on the full command center layout...", flush=True)
        move_cursor_to_element(page, "text=Alexa+ Live Continuity Simulation", wait_after=2.5)
        page.evaluate("window.__moveCursor(960, 500)")
        page.wait_for_timeout(4500)

        print("[2:40] Demo complete! Finalizing 1080p video recording...", flush=True)
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
