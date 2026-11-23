#!/usr/bin/env python3
"""PA Job Helper: a simple local web app on top of pa_apply.py. Run: python app.py"""
import hashlib, queue, re, threading, time, webbrowser
from pathlib import Path
from flask import Flask, redirect, render_template_string, request, jsonify
import pa_apply as core
import pa_forms
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

HERE = core.HERE
PROFILE_F = HERE / "profile.json"
PORT = 5055  # not 5000: macOS uses that for AirPlay
app = Flask(__name__)
STATUS = {"scrape": "", "fill": ""}
CMDS = queue.Queue()
SCRAPE_LOCK = threading.Lock()
BUSY = threading.Event()
LAST_F = HERE / "last_check.txt"

def checked_recently(hours):
    try:
        return time.time() - float(LAST_F.read_text()) < hours * 3600
    except Exception:
        return False

def jid(url): return hashlib.md5(url.encode()).hexdigest()[:10]

def jobs():
    q = core.load(core.QUEUE_F, [])
    for j in q:
        j.setdefault("state", "applied" if j.get("done") else "new")
        j["id"] = jid(j["url"])
    return q

def age(p):
    p = p.lower()
    if "today" in p: return 0
    if "yesterday" in p: return 1
    m = re.search(r"(\d+)", p)
    return int(m.group(1)) if m else 99

# ------------------------------------------------------------ job search
def scrape_new():
    if not SCRAPE_LOCK.acquire(blocking=False):
        return
    try:
        STATUS["scrape"] = "Checking for new jobs..."
        LAST_F.write_text(str(time.time()))
        seen, q, added = set(core.load(core.SEEN_F, [])), jobs(), 0
        for t in core.CONFIG["tenants"]:
            try:
                postings = core.search_tenant(t)
            except Exception as e:
                print("scrape error:", e)
                if "429" in str(e):
                    STATUS["scrape"] = "NYP asked us to slow down. Wait about an hour, then try again."
                else:
                    STATUS["scrape"] = f"Couldn’t reach {t['name']}. Check your internet and try again."
                return
            for p in postings:
                if p["_url"] in seen or not core.title_ok(p["title"]):
                    continue
                seen.add(p["_url"])
                try:
                    text = core.description(p)
                except Exception:
                    text = ""
                q.append({"employer": p["_tenant"], "title": p["title"], "url": p["_url"],
                          "location": p.get("locationsText", ""), "posted": p.get("postedOn", ""),
                          "needs_experience": core.experience_flag(text), "state": "new"})
                added += 1
                time.sleep(1)
        core.save(core.SEEN_F, sorted(seen)); core.save(core.QUEUE_F, q)
        STATUS["scrape"] = f"Job list updated: {added} new job(s)."
    finally:
        SCRAPE_LOCK.release()

# ------------------------------------------------------------ browser worker
def debug_dump(page, profile, filled):
    rows = page.evaluate("""() => [...document.querySelectorAll('input,select,textarea')]
      .filter(e => e.offsetParent !== null).slice(0, 40)
      .map(e => [e.type, e.getAttribute('data-automation-id')||'', e.id||'', e.getAttribute('aria-label')||''].join(' | '))""")
    print("---- page:", page.url[:90])
    print("profile has:", [k for k, v in profile.items() if v])
    print("filled:", filled)
    print("visible fields (type | automation-id | id | aria-label):")
    for r in rows:
        print("  ", r)

def run_job(ctx, job):
    profile = core.load(PROFILE_F, {})
    profile.update(core.load(HERE / "resume_data.json", {}))
    name = job["title"][:60]
    page = ctx.new_page()
    STATUS["fill"] = f"Opening: {name}"
    js = ("() => location.href + '|' + document.querySelectorAll('input,select,textarea').length"
          " + '|' + ((document.querySelector('h2')||{}).innerText||'')")
    try:
        page.goto(job["url"]); page.wait_for_load_state("domcontentloaded")
        btn = page.locator('[data-automation-id="adventureButton"]')
        if btn.count():
            btn.first.click(); page.wait_for_timeout(2000)
        STATUS["fill"] = ("In the pop-up choose “Apply Manually” (I’ll enter your education and experience "
                          "from your saved profile) and sign in if asked.")
        last = None
        done = set()
        while not page.is_closed():
            try:
                sig = page.evaluate(js)
            except Exception:
                page.wait_for_timeout(1000); continue
            if sig != last:
                last = sig
                page.wait_for_timeout(1500)
                try:
                    filled = core.autofill_page(page, profile, done)
                    manual = core.flag_manual_fields(page)
                    debug_dump(page, profile, filled)
                except Exception as e:
                    print("AUTOFILL ERROR:", repr(e))
                    filled, manual = [], []
                msg = f"{name}: filled {len(filled)} field(s) for you."
                if manual:
                    msg += f" Please answer the {len(manual)} question(s) outlined in orange yourself."
                try:
                    if page.get_by_role("heading", name="My Experience").count():
                        msg += " Check every school, degree and date."
                        if "sections" not in done and (profile.get("education") or profile.get("experience")):
                            done.add("sections")
                            STATUS["fill"] = f"{name}: entering your education and experience. This takes a minute..."
                            r = pa_forms.fill_sections(page, profile)
                            msg = f"{name}: entered {r['filled']} entries from your profile."
                            if r["skipped"]:
                                msg += " Workday had already filled: " + "; ".join(r["skipped"]) + ". Please check them."
                            if r["check"]:
                                msg += " Fix the fields outlined in orange in: " + ", ".join(r["check"]) + "."
                except Exception:
                    pass
                STATUS["fill"] = msg + " Review, then click Next in the browser window."
            page.wait_for_timeout(1500)
    except Exception as e:
        if not (page.is_closed() or "closed" in str(e).lower()):
            raise
    STATUS["fill"] = ""

def worker():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ctx = None
        while True:
            job = CMDS.get()
            BUSY.set()
            for attempt in (1, 2):
                try:
                    if ctx is None:
                        ctx = pw.chromium.launch_persistent_context(
                            str(HERE / "chrome_profile"), headless=False, no_viewport=True,
                            args=["--start-maximized"])
                    run_job(ctx, job)
                    break
                except Exception as e:
                    print("fill error:", e)
                    try: ctx.close()
                    except Exception: pass
                    ctx = None
                    if attempt == 2:
                        STATUS["fill"] = "Something went wrong. Click Apply again."
            BUSY.clear()

# ------------------------------------------------------------ pages
STYLE = """<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2430;--mut:#667085;--line:#e4e7ec;--acc:#1f6feb;--ok:#e6f4ea;--warn:#fff4e0}
@media(prefers-color-scheme:dark){:root{--bg:#14181f;--card:#1d232d;--ink:#e8ecf2;--mut:#98a2b3;--line:#2b3340;--acc:#5b9dff;--ok:#1d3326;--warn:#3a2f17}}
*{box-sizing:border-box}body{font:16px/1.45 system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--ink);margin:0}
.wrap{max-width:820px;margin:0 auto;padding:20px 16px 80px}
nav{display:flex;gap:16px;align-items:center;margin-bottom:12px}nav a{color:var(--acc);text-decoration:none;font-weight:600}
h1{font-size:22px;margin:0 auto 0 0;color:var(--ink)}
#bar{position:sticky;top:0;background:var(--acc);color:#fff;padding:10px 14px;border-radius:10px;margin:8px 0 14px;display:none}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:10px 0}
.t{font-weight:650}.m{color:var(--mut);font-size:14px;margin-top:2px}
.tag{display:inline-block;font-size:12px;padding:2px 8px;border-radius:99px;margin:6px 6px 0 0;background:var(--warn)}
.tag.g{background:var(--ok)}
.row{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
button,.btn{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--ink);padding:8px 14px;border-radius:8px;cursor:pointer}
button.p{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600}
input[type=text],input[type=email]{width:100%;padding:9px;border:1px solid var(--line);border-radius:8px;font:inherit;background:var(--card);color:var(--ink)}
label{display:block;margin:12px 0 4px;font-weight:600;font-size:14px}h2{font-size:17px;margin:26px 0 4px}
.notice{background:var(--warn);padding:12px 14px;border-radius:10px;margin:10px 0}
</style>"""

SCRIPT = """<script>
async function poll(){try{const s=await (await fetch('/status')).json();
const t=[s.scrape,s.fill].filter(Boolean).join('  •  ');const b=document.getElementById('bar');
b.innerText=t;b.style.display=t?'block':'none';}catch(e){}}
setInterval(poll,2000);poll();
</script>"""

HEAD = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PA Job Helper</title>""" + STYLE + "</head><body><div class='wrap'>" \
       "<nav><h1>PA Job Helper</h1><a href='/'>Jobs</a><a href='/settings'>My info</a></nav><div id='bar'></div>"
TAIL = "</div>" + SCRIPT + "</body></html>"

INDEX = HEAD + """
{% if setup_needed %}<div class="notice">First, go to <a href="/settings">My info</a> and fill in your details and resume.</div>{% endif %}
<div class="row" style="margin:0 0 6px"><form method="post" action="/scrape"><button>Check for new jobs</button></form></div>
<h2>To apply ({{ todo|length }})</h2>
{% for j in todo %}<div class="card"><div class="t">{{ j.title }}</div>
<div class="m">{{ j.employer }} · {{ j.location }} · {{ j.posted }}</div>
{% if j.new_grad %}<span class="tag g">Open to new grads</span>{% endif %}
{% if j.per_diem %}<span class="tag">Per diem</span>{% endif %}
{% if j.needs_experience %}<span class="tag">May require experience</span>{% endif %}
<div class="row">
<form method="post" action="/apply/{{ j.id }}"><button class="p">Apply</button></form>
<form method="post" action="/mark/{{ j.id }}/applied"><button>I applied</button></form>
<form method="post" action="/mark/{{ j.id }}/skipped"><button>Skip</button></form></div></div>
{% else %}<p class="m">Nothing new right now. Check back tomorrow.</p>{% endfor %}
{% if done %}<h2>Applied ({{ done|length }})</h2>{% for j in done %}<div class="card"><div class="t">{{ j.title }}</div>
<div class="m">{{ j.employer }} · {{ j.location }}</div></div>{% endfor %}{% endif %}
""" + TAIL

SETTINGS = HEAD + """
<form method="post" enctype="multipart/form-data">
{% for k,l in fields %}<label>{{ l }}</label><input type="text" name="{{ k }}" value="{{ p.get(k,'') }}">{% endfor %}
<label>Resume (PDF)</label><input type="file" name="resume" accept=".pdf,.doc,.docx">
{% if p.get('resume_path') %}<div class="m">Saved: {{ p.resume_path.split('/')[-1].split('\\\\')[-1] }}</div>{% endif %}
<label><input type="checkbox" name="exclude_per_diem" {% if p.get('exclude_per_diem') %}checked{% endif %}> Hide per diem jobs</label>
<div class="row"><button class="p">Save</button></div></form>
<div class="notice" style="margin-top:20px">The app never submits anything for you. You answer license, DEA and other questions yourself, and click Submit yourself.</div>
""" + TAIL

FIELDS = [("first_name", "First name"), ("last_name", "Last name"), ("email", "Email"),
          ("phone", "Phone"), ("address1", "Street address"), ("city", "City"), ("zip", "ZIP code")]

@app.route("/")
def index():
    prof = core.load(PROFILE_F, {})
    js = jobs()
    for j in js:
        j["per_diem"] = "per diem" in j["title"].lower()
        j["new_grad"] = "new grad" in j["title"].lower()
    todo = [j for j in js if j["state"] == "new" and not (prof.get("exclude_per_diem") and j["per_diem"])]
    todo.sort(key=lambda j: age(j.get("posted", "")))
    done = [j for j in js if j["state"] == "applied"]
    return render_template_string(INDEX, todo=todo, done=done, setup_needed=not prof.get("first_name"))

@app.route("/scrape", methods=["POST"])
def scrape_route():
    if checked_recently(0.25):
        STATUS["scrape"] = "Already checked a few minutes ago. Try again later."
    else:
        threading.Thread(target=scrape_new, daemon=True).start()
    return redirect("/")

@app.route("/apply/<job_id>", methods=["POST"])
def apply_route(job_id):
    if BUSY.is_set() or not CMDS.empty():
        STATUS["fill"] = "Finish or close the open application window first."
        return redirect("/")
    for j in jobs():
        if j["id"] == job_id:
            CMDS.put(j)
            STATUS["fill"] = f"Opening: {j['title'][:60]}"
    return redirect("/")

@app.route("/mark/<job_id>/<state>", methods=["POST"])
def mark(job_id, state):
    if state in ("applied", "skipped", "new"):
        q = jobs()
        for j in q:
            if j["id"] == job_id:
                j["state"] = state
        core.save(core.QUEUE_F, q)
    return redirect("/")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    p = core.load(PROFILE_F, {})
    if request.method == "POST":
        for k, _ in FIELDS:
            p[k] = request.form.get(k, "").strip()
        p["exclude_per_diem"] = "exclude_per_diem" in request.form
        f = request.files.get("resume")
        if f and f.filename:
            ext = Path(f.filename).suffix.lower()
            if ext in (".pdf", ".doc", ".docx"):
                dest = HERE / f"resume{ext}"
                f.save(dest); p["resume_path"] = str(dest)
        core.save(PROFILE_F, p)
        return redirect("/")
    return render_template_string(SETTINGS, p=p, fields=FIELDS)

@app.route("/status")
def status():
    return jsonify(STATUS)

if __name__ == "__main__":
    threading.Thread(target=worker, daemon=True).start()
    if not checked_recently(6):
        threading.Thread(target=scrape_new, daemon=True).start()
    threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    print(f"PA Job Helper running at http://127.0.0.1:{PORT}  (close this window to quit)")
    app.run(host="127.0.0.1", port=PORT)