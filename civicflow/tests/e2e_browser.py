"""Browser end-to-end test (optional): python tests/e2e_browser.py
Needs: pip install playwright && playwright install chromium
Starts its own server on a temporary database, drives the real UI, prints PASS/FAIL per check."""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.getenv("E2E_PORT", "8011"))
BASE = f"http://127.0.0.1:{PORT}"
SHOTS = Path(os.getenv("E2E_SHOTS", tempfile.mkdtemp(prefix="civicflow-shots-")))
results = []


def check(name, ok, extra=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (f"  [{extra}]" if extra and not ok else ""))


def main():
    tmp = tempfile.mkdtemp()
    env = dict(os.environ, PORT=str(PORT), DATABASE_PATH=f"{tmp}/e2e.db", UPLOAD_DIR=f"{tmp}/up")
    for k in ("AI_API_KEY", "OPENAI_API_KEY"):
        env.pop(k, None)
    srv = subprocess.Popen([sys.executable, "app.py"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                urllib.request.urlopen(BASE + "/health", timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        photo = Path(tmp) / "photo.png"
        photo.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 200)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 900})
            page_errors = []
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.goto(BASE)

            # --- language switching ---
            page.select_option("#lang", "te")
            check("telugu labels", "సమస్యను నివేదించండి" in page.inner_text(".tabs") and page.locator("html").get_attribute("lang") == "te")
            page.select_option("#lang", "hi")
            check("hindi labels", "समस्या दर्ज करें" in page.inner_text(".tabs"))
            page.select_option("#lang", "en")
            check("english labels", "Report an issue" in page.inner_text(".tabs"))

            # --- client validation ---
            page.click("#report-submit")
            check("empty form shows error", page.locator("#report-error").is_visible())

            # --- citizen report A ---
            page.fill("#f-location", "Road No. 12, near the school gate, Banjara Hills")
            page.fill("#f-description", "Large, deep pothole at the school gate. Children cross here and two-wheelers swerve around it. It has been there for two weeks and it is dangerous.")
            page.click("#report-submit")
            page.wait_for_selector("#confirmation .plate", state="visible")
            ticket_a = page.inner_text("#confirmation .plate")
            check("ticket id shown", ticket_a.startswith("CF-") and len(ticket_a) == 11, ticket_a)
            check("fallback honestly labelled", "rules fallback" in page.inner_text("#confirmation").lower())
            page.screenshot(path=str(SHOTS / "1-confirmation.png"))

            # --- citizen report B (Hindi UI + photo) similar to A ---
            page.click("text=Report another issue")
            page.select_option("#lang", "hi")
            page.fill("#f-location", "Banjara Hills Road 12, school gate")
            page.fill("#f-description", "Dangerous pothole at the school entrance. A scooter fell here yesterday and children walk past the hole every morning.")
            page.set_input_files("#f-photo", str(photo))
            page.click("#report-submit")
            page.wait_for_selector("#confirmation .plate", state="visible")
            ticket_b = page.inner_text("#confirmation .plate")
            check("second ticket differs", ticket_b != ticket_a)
            page.select_option("#lang", "en")

            # --- oversized photo rejected client-side ---
            page.click("text=Report another issue")
            big = Path(tmp) / "big.jpg"
            big.write_bytes(b"\xff\xd8\xff" + b"0" * (3 * 1024 * 1024 + 10))
            page.fill("#f-location", "Lane 3, Jubilee Hills")
            page.fill("#f-description", "Garbage overflowing from the dustbin for 4 days.")
            page.set_input_files("#f-photo", str(big))
            page.click("#report-submit")
            check("oversized photo rejected", "3 MB" in page.inner_text("#report-error"))

            # --- authority desk ---
            page.click(".tab[data-view=authority]")
            page.wait_for_selector(".card")
            check("queue lists both reports", page.locator(".card").count() == 2)
            kpis = page.inner_text("#kpis")
            check("kpis show 2 reports, 1 grouped issue", "2" in kpis and "1" in kpis)
            check("related chip shown", "Possibly related to 1 more" in page.inner_text("#queue"))
            card_a = page.locator(".card", has=page.locator(".chip", has_text=ticket_a)).first
            card_a.locator("summary").click()
            body = card_a.inner_text()
            check("score reasons visible", all(w in body for w in ("Category impact", "Safety indicator", "Duration", "Related reports", "not an official")))
            check("recommendation visible", "hazard temporarily" in body)
            page.screenshot(path=str(SHOTS / "2-authority.png"), full_page=True)

            # --- status update -> citizen tracking ---
            page.select_option(f"#st-{ticket_a}", "In Progress")
            page.wait_for_selector("#toast:visible")
            check("status toast", ticket_a in page.inner_text("#toast"))
            check("details stay open after update", card_a.locator("details").get_attribute("open") is not None)
            page.click(".tab[data-view=track]")
            page.fill("#t-id", ticket_a.lower())
            page.click("#track-form button")
            page.wait_for_selector("#track-result .panel")
            tr = page.inner_text("#track-result")
            check("tracking shows updated status", "In Progress" in tr and "Road Damage" in tr)
            check("tracking shows related count", "1 other" in tr)
            page.screenshot(path=str(SHOTS / "3-track.png"), full_page=True)
            page.fill("#t-id", "CF-NOPE0000")
            page.click("#track-form button")
            page.wait_for_selector("#track-error:visible")
            check("unknown id message", "No report found" in page.inner_text("#track-error"))

            # --- photo visible on tracking for report B ---
            page.fill("#t-id", ticket_b)
            page.click("#track-form button")
            page.wait_for_selector("#track-result img")
            check("photo shown on tracking", page.locator("#track-result img").count() == 1)

            # --- demo data ---
            page.click(".tab[data-view=authority]")
            page.click("#demo-seed")
            page.wait_for_selector("text=Demo scenario loaded.")
            check("demo cards marked DEMO", page.locator(".chip.demo").count() == 3)
            check("5 reports total", page.locator(".card").count() == 5)
            page.select_option("#flt-priority", "High")
            page.wait_for_function("document.querySelectorAll('.card.Medium, .card.Low').length === 0")
            check("priority filter works", page.locator(".card").count() >= 3)
            page.select_option("#flt-priority", "")
            page.click("#demo-clear")
            page.wait_for_selector("text=Demo data removed (3).")
            check("clear demo keeps real reports", page.locator(".card").count() == 2)

            # --- mobile layout ---
            page.set_viewport_size({"width": 390, "height": 800})
            page.click(".tab[data-view=report]")
            page.click("text=Report another issue") if page.locator("text=Report another issue").is_visible() else None
            overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            check("no horizontal overflow on mobile (report)", not overflow)
            page.click(".tab[data-view=authority]")
            page.wait_for_selector(".card")
            overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            check("no horizontal overflow on mobile (authority)", not overflow)
            page.screenshot(path=str(SHOTS / "4-mobile-authority.png"), full_page=True)

            check("no uncaught JS errors", not page_errors, "; ".join(page_errors))
            browser.close()
    finally:
        srv.terminate()
        srv.wait(timeout=5)
    print(f"\n{sum(results)}/{len(results)} checks passed. Screenshots: {SHOTS}")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
