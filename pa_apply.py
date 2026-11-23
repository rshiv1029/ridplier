#!/usr/bin/env python3
"""
PA job scraper + co-pilot application filler (Workday).

Usage:
  pip install httpx playwright && playwright install chromium
  python pa_apply.py scrape      # run daily via cron; finds + queues new jobs
  python pa_apply.py fill        # run at her desk; autofills, she reviews + submits
  python pa_apply.py login HOST  # one-time: open a tenant so she can create/log into her account

Files (same folder): config.json, profile.json, queue.json (auto), seen.json (auto)
"""
import json, re, sys, time
from pathlib import Path
import httpx

HERE = Path(__file__).parent
CONFIG = json.loads((HERE / "config.json").read_text())
SEEN_F, QUEUE_F = HERE / "seen.json", HERE / "queue.json"

def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default

def save(p, data):
    p.write_text(json.dumps(data, indent=2))

# ---------------------------------------------------------------- scraping
def search_tenant(t):
    """Query a Workday tenant's CXS endpoint. Returns list of posting dicts."""
    base = f"https://{t['host']}/wday/cxs/{t['tenant']}/{t['site']}"
    out, offset = [], 0
    while offset < 100:
        r = httpx.post(
            f"{base}/jobs",
            json={"appliedFacets": {}, "limit": 20, "offset": offset,
                  "searchText": CONFIG.get("search_text", "physician assistant")},
            timeout=30,
        )
        r.raise_for_status()
        postings = r.json().get("jobPostings", [])
        if not postings:
            break
        out += postings
        offset += 20
        time.sleep(1.5)  # be polite
    for p in out:
        p["_base"] = base
        p["_url"] = f"https://{t['host']}/{t['site']}{p['externalPath']}"
        p["_tenant"] = t["name"]
    return out

def description(p):
    r = httpx.get(p["_base"] + p["externalPath"], timeout=30)
    r.raise_for_status()
    html = r.json().get("jobPostingInfo", {}).get("jobDescription", "")
    return re.sub(r"<[^>]+>", " ", html)

def title_ok(title):
    t = title.lower()
    if not any(k in t for k in CONFIG["title_include"]):
        return False
    return not any(k in t for k in CONFIG["title_exclude"])

def experience_flag(text):
    """Flag (not hard-reject) postings that look like they need 2+ years."""
    m = re.search(r"\b([2-9])\+?\s*(?:or more\s*)?years?\b[^.]{0,60}(experience)", text, re.I)
    return bool(m)

def scrape():
    seen, queue = set(load(SEEN_F, [])), load(QUEUE_F, [])
    new = []
    for t in CONFIG["tenants"]:
        try:
            postings = search_tenant(t)
        except Exception as e:
            print(f"[warn] {t['name']}: {e}")
            continue
        for p in postings:
            if p["_url"] in seen or not title_ok(p["title"]):
                continue
            seen.add(p["_url"])
            try:
                text = description(p)
            except Exception:
                text = ""
            new.append({
                "employer": p["_tenant"], "title": p["title"], "url": p["_url"],
                "location": p.get("locationsText", ""), "posted": p.get("postedOn", ""),
                "needs_experience": experience_flag(text),
                "done": False,
            })
            time.sleep(1)
    queue += new
    save(SEEN_F, sorted(seen)); save(QUEUE_F, queue)
    print(f"{len(new)} new matching jobs. Queue size: {sum(not q['done'] for q in queue)}")
    for j in new:
        flag = "  [experience req?]" if j["needs_experience"] else ""
        print(f" - {j['employer']}: {j['title']} ({j['location']}) {j['posted']}{flag}\n   {j['url']}")

# ---------------------------------------------------------------- filling
# Workday's stable data-automation-id values for common fields -> profile keys
WORKDAY_FIELDS = {
    "legalNameSection_firstName": "first_name",
    "legalNameSection_lastName": "last_name",
    "addressSection_addressLine1": "address1",
    "addressSection_city": "city",
    "addressSection_postalCode": "zip",
    "phone-number": "phone",
    "email": "email",
}
# Any question whose text matches these is NEVER auto-answered.
MANUAL_STOP = re.compile(
    r"licen[sc]e|dea\b|cds|controlled|disciplin|felony|convict|sanction|malpractice|"
    r"visa|sponsor|why do you|tell us|describe|essay|salary|compensation",
    re.I,
)

LABELS = {
    "first_name": ["First Name"], "last_name": ["Last Name"],
    "address1": ["Address Line 1", "Street"], "city": ["City"],
    "zip": ["Postal Code", "ZIP"], "phone": ["Phone Number"], "email": ["Email"],
}

def autofill_page(page, profile):
    filled = []

    def put(key, loc):
        try:
            if (loc.count() and profile.get(key) and loc.first.is_visible()
                    and loc.first.input_value() == ""):
                loc.first.fill(str(profile[key]))
                loc.first.evaluate("e => e.blur()")
                filled.append(key)
                return True
        except Exception:
            pass
        return False

    for aid, key in WORKDAY_FIELDS.items():
        sel = (f'input[data-automation-id="{aid}"], [data-automation-id="{aid}"] input, '
               f'[data-automation-id="{aid}"] textarea')
        if not put(key, page.locator(sel)):
            for label in LABELS.get(key, []):
                if put(key, page.get_by_label(re.compile(rf"^\s*{label}", re.I))):
                    break
    up = page.locator('input[type="file"]')
    if up.count() and profile.get("resume_path"):
        try:
            up.first.set_input_files(profile["resume_path"]); filled.append("resume")
        except Exception:
            pass
    return filled

def flag_manual_fields(page):
    """Highlight questions the human must answer; return their labels."""
    flagged = []
    labels = page.locator("label, legend")
    for i in range(min(labels.count(), 200)):
        lab = labels.nth(i)
        try:
            txt = lab.inner_text(timeout=500).strip()
        except Exception:
            continue
        if txt and MANUAL_STOP.search(txt):
            flagged.append(txt[:110])
            lab.evaluate("e => e.style.outline = '3px solid orange'")
    return flagged

def fill():
    from playwright.sync_api import sync_playwright
    profile = load(HERE / "profile.json", {})
    queue = load(QUEUE_F, [])
    todo = [q for q in queue if not q["done"]]
    if not todo:
        print("Queue empty."); return
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(HERE / "chrome_profile"), headless=False, viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        for job in todo:
            print(f"\n=== {job['employer']} | {job['title']} ({job['location']})")
            if job["needs_experience"]:
                print("  ! Posting may require 2+ yrs experience.")
            choice = input("  [Enter]=open  s=skip  q=quit > ").strip().lower()
            if choice == "q":
                break
            if choice == "s":
                continue
            page.goto(job["url"]); page.wait_for_load_state("domcontentloaded")
            for sel in ['[data-automation-id="adventureButton"]',
                        '[data-automation-id="applyManually"]',
                        '[data-automation-id="useMyLastApplication"]']:
                btn = page.locator(sel)
                if btn.count():
                    btn.first.click(); page.wait_for_timeout(2500)
            print("  Log in / create account in the browser if prompted.")
            while True:
                input("  Page loaded. Press Enter to autofill this step... ")
                done = autofill_page(page, profile)
                manual = flag_manual_fields(page)
                print(f"  Filled: {done or 'nothing'}")
                if manual:
                    print("  ANSWER THESE YOURSELF (outlined in orange):")
                    for m in manual: print(f"    - {m}")
                    print("  License questions: pick 'pending/in process' where offered.")
                cmd = input("  Review, click Next in the browser as needed. "
                            "[Enter]=autofill next page  d=done/submitted  s=skip job > ").strip().lower()
                if cmd == "d":
                    job["done"] = True; save(QUEUE_F, queue); break
                if cmd == "s":
                    break
        ctx.close()

def login(host):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(str(HERE / "chrome_profile"), headless=False)
        ctx.new_page().goto(f"https://{host}")
        input("Create/log in to the account, then press Enter to close... ")
        ctx.close()

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "scrape": scrape()
    elif cmd == "fill": fill()
    elif cmd == "login" and len(sys.argv) > 2: login(sys.argv[2])
    else: print(__doc__)