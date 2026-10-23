"""
Automated Video Recorder for Siigo 3-Minute Live Demo Runbook
Uses Playwright with Microsoft Edge to drive the browser and record a full 1080p video.
Executes the exact 8-step runbook choreography.
"""
import os
import time
import glob
import shutil
from playwright.sync_api import sync_playwright

WORKSPACE = os.path.dirname(os.path.dirname(__file__))
RECORDINGS_DIR = os.path.join(WORKSPACE, "recordings")
os.makedirs(RECORDINGS_DIR, exist_ok=True)

TARGET_VIDEO_PATH = os.path.join(RECORDINGS_DIR, "siigo_3min_demo_walkthrough.webm")

def record_live_demo():
    print("=" * 70)
    print("STARTING AUTONOMOUS SCREEN RECORDING VIA PLAYWRIGHT (1080p 60FPS)")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=RECORDINGS_DIR,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        print("[0:00] Step 1: Navigating to Siigo Command Center (http://localhost:3000)...")
        page.goto("http://localhost:3000", wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Reset to pristine state
        print("[0:05] Resetting to clean demo baseline...")
        reset_btn = page.locator("button:has-text('Reset')")
        if reset_btn.is_visible():
            reset_btn.click()
            page.wait_for_timeout(2000)

        # 0:10 - 0:30: Point to the owner utterance
        print("[0:10] Step 2: Hovering over Maya's absence utterance...")
        utterance = page.locator("text=I'm unavailable tomorrow. Identify anything that needs attention.")
        if utterance.is_visible():
            utterance.hover()
        page.wait_for_timeout(4000)

        # 0:30: Run complete walkthrough
        print("[0:30] Step 3: Triggering 'Run Complete Demo Walkthrough'...")
        walkthrough_btn = page.locator("button:has-text('Run Complete Demo Walkthrough')")
        walkthrough_btn.click()

        # Wait for the walkthrough to complete
        print("       Waiting for evidence extraction, Alexa webhook and handoff compilation...")
        page.wait_for_selector("text=Confirm order docket #4092 for Sharma Prints", timeout=30000)
        page.wait_for_timeout(4000)

        # 1:05 - 1:35: Evidence grounding
        print("[1:05] Step 4: Inspecting Safe Handoff & exact quote citation...")
        sharma_claim = page.locator("text=Confirm order docket #4092 for Sharma Prints").first
        sharma_claim.scroll_into_view_if_needed()
        sharma_claim.hover()
        page.wait_for_timeout(5000)

        # Scroll down to What I Cannot See
        print("       Highlighting 'What I Cannot See' disclosures...")
        gaps_section = page.locator("text=What I Cannot See")
        if gaps_section.is_visible():
            gaps_section.scroll_into_view_if_needed()
            page.wait_for_timeout(4000)

        # 1:35 - 2:00: Financial limit policy denial
        print("[1:35] Step 5: Highlighting Authority Gate Duel - Over-Limit Deny (INR 65,000)...", flush=True)
        gate_duel = page.locator("text=Authority Gate Duel")
        gate_duel.scroll_into_view_if_needed()
        page.wait_for_timeout(3000)

        deny_card = page.locator("text=DECISION: DENY")
        if deny_card.is_visible():
            deny_card.hover()
        page.wait_for_timeout(4000)

        # 2:00 - 2:25: Permitted request
        print("[2:00] Step 6: Triggering 'Permitted Test B - Authorized (INR 18,000)'...", flush=True)
        permit_btn = page.locator("button:has-text('Authorized (₹18,000)')")
        permit_btn.click()
        page.wait_for_selector("text=DECISION: ALLOW", timeout=10000)
        page.wait_for_timeout(4000)

        # 2:25 - 2:45: Evidence Review Queue
        print("[2:25] Step 7: Navigating to Evidence Review Queue in sidebar...", flush=True)
        review_nav = page.locator("button:has-text('Evidence Review Queue')")
        review_nav.click()
        page.wait_for_selector("text=Evidence & Approval Review Queue", timeout=10000)
        page.wait_for_timeout(5000)

        # 2:45 - 3:00: Return to simulation for closing payoff
        print("[2:45] Step 8: Returning to Alexa+ Live Simulation for payoff...", flush=True)
        sim_nav = page.locator("button:has-text('Alexa+ Live Simulation')")
        sim_nav.click()
        page.wait_for_timeout(4000)

        print("[3:00] Closing browser and finalizing video stream...", flush=True)
        video_obj = page.video
        context.close()
        browser.close()

        # Find the generated video file
        video_path = video_obj.path() if video_obj else None
        if video_path and os.path.exists(video_path):
            if os.path.exists(TARGET_VIDEO_PATH):
                os.remove(TARGET_VIDEO_PATH)
            shutil.move(video_path, TARGET_VIDEO_PATH)
            size_mb = os.path.getsize(TARGET_VIDEO_PATH) / (1024 * 1024)
            print("=" * 70)
            print(f"SUCCESS: Video recorded ({size_mb:.2f} MB)")
            print(f"Location: {TARGET_VIDEO_PATH}")
            print("=" * 70)
            return TARGET_VIDEO_PATH
        else:
            print("Video file not found!")
            return None

if __name__ == "__main__":
    record_live_demo()
