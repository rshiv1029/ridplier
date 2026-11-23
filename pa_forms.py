"""Best-effort filling of Workday's Education and Work Experience sections from resume_data.json.
Never deletes anything. If Workday already filled a section, it is left alone and reported."""
import re

def parse_ym(s):
    """'2025-09' -> (9, 2025); '2024' -> (None, 2024)."""
    s = str(s or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", s)
    if m: return int(m.group(2)), int(m.group(1))
    return (None, int(s)) if re.fullmatch(r"\d{4}", s) else (None, None)

def _f(panel, suffix):
    return panel.locator(f'[id$="--{suffix}"]').first

def _flag(panel, suffix):
    try:
        panel.locator(f'[data-automation-id="formField-{suffix}"]').first.evaluate(
            "e => e.style.outline = '3px solid orange'")
    except Exception:
        pass

def _text(panel, suffix, value):
    if not value: return True
    try:
        el = _f(panel, suffix); el.fill(str(value)); el.evaluate("e => e.blur()")
        return el.input_value() == str(value)
    except Exception:
        return False

def _date(page, panel, suffix, ym):
    month, year = parse_ym(ym)
    ok = True
    for part, val in (("Month", month), ("Year", year)):
        if val is None: continue
        try:
            inp = panel.locator(f'[id$="--{suffix}-dateSection{part}-input"]').first
            inp.focus(); page.keyboard.press("ControlOrMeta+A")
            page.keyboard.type(str(val), delay=50); page.keyboard.press("Tab")
            ok = ok and inp.input_value().lstrip("0") == str(val)
        except Exception:
            ok = False
    return ok

def _degree(page, panel, wanted):
    try:
        panel.locator('button[name="degree"]').first.click(); page.wait_for_timeout(600)
        opts = page.get_by_role("option")
        texts = [t.strip() for t in opts.all_inner_texts()]
        print("   degree options:", texts[:40])
        for w in wanted:                       # exact match first
            for i, t in enumerate(texts):
                if t.lower() == w.lower():
                    opts.nth(i).click(); return True
        for w in wanted:                       # then whole-word match ("MS" must not match "MSL")
            for i, t in enumerate(texts):
                if re.search(rf"\b{re.escape(w)}\b", t, re.I):
                    opts.nth(i).click(); return True
        page.keyboard.press("Escape")
    except Exception as e:
        print("   degree error:", repr(e))
    return False

def _field(page, panel, text):
    try:
        inp = _f(panel, "fieldOfStudy"); inp.click(); inp.press_sequentially(text, delay=40)
        page.wait_for_timeout(1500); page.keyboard.press("Enter"); page.wait_for_timeout(600)
        label = panel.locator('[data-automation-id="promptAriaInstruction"]').first.inner_text()
        return bool(re.match(r"[1-9]\d* item", label))
    except Exception:
        return False

def fill_sections(page, profile):
    rep = {"filled": 0, "check": [], "skipped": []}
    for key, section in (("education", "Education"), ("experience", "Work-Experience")):
        entries = profile.get(key) or []
        if not entries: continue
        have = page.locator(f'[role="group"][aria-labelledby^="{section}-"][aria-labelledby$="-panel"]').count()
        if have:
            rep["skipped"].append(f"{section.replace('-', ' ')} already has {have} entries")
            continue
        add = page.locator(f'[role="group"][aria-labelledby="{section}-section"] [data-automation-id="add-button"]')
        for n, e in enumerate(entries, 1):
            try:
                add.last.click()
                panel = page.locator(f'[role="group"][aria-labelledby="{section}-{n}-panel"]')
                panel.wait_for(timeout=6000)
                checks = {}
                if key == "education":
                    checks["schoolName"] = _text(panel, "schoolName", e.get("school"))
                    checks["degree"] = _degree(page, panel, e.get("degree_options", []))
                    if e.get("field"): checks["fieldOfStudy"] = _field(page, panel, e["field"])
                    checks["firstYearAttended"] = _date(page, panel, "firstYearAttended", e.get("from"))
                    checks["lastYearAttended"] = _date(page, panel, "lastYearAttended", e.get("to"))
                else:
                    checks["jobTitle"] = _text(panel, "jobTitle", e.get("title"))
                    checks["companyName"] = _text(panel, "companyName", e.get("company"))
                    checks["location"] = _text(panel, "location", e.get("location"))
                    checks["startDate"] = _date(page, panel, "startDate", e.get("from"))
                    checks["endDate"] = _date(page, panel, "endDate", e.get("to"))
                    checks["roleDescription"] = _text(panel, "roleDescription", e.get("description"))
                bad = [k for k, ok in checks.items() if not ok]
                for k in bad: _flag(panel, k)
                rep["filled"] += 1
                if bad: rep["check"].append(f"{section.replace('-', ' ')} {n}")
            except Exception as ex:
                print("   entry error:", section, n, repr(ex))
                rep["check"].append(f"{section.replace('-', ' ')} {n} (not entered)")
                break
    return rep
