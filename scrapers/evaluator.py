import re
from typing import List, Optional, Tuple

# Non-new-grad / leadership / non-full-time titles to strictly exclude
EXCLUDE_TITLE_WORDS = [
    r"\bsenior\b",
    r"\blead\b",
    r"\bchief\b",
    r"\bmanager\b",
    r"\bdirector\b",
    r"\bsupervisor\b",
    r"\bassistant professor\b",
    r"\bfaculty\b",
    r"\bper diem\b",
    r"\bprn\b",
    r"\bpart[\s-]?time\b",
    r"\bcasual\b",
    r"\bcontingent\b",
    r"\bexperience\s+required\b",
    r"\bexper\s+req\b",
]

# Valid PA / APP title markers
INCLUDE_TITLE_WORDS = [
    r"\bphysician assistant\b",
    r"\bphysician\s+asst\b",
    r"\bpa-c\b",
    r"\bpa\b",
    r"\badvanced practice provider\b",
    r"\bapp\b",
]

# Tier 1: High Chance (Explicit new-grad friendly signals)
HIGH_CHANCE_PATTERNS = [
    r"new grad(?:uate)?s?\s*(?:welcome|encouraged|accepted|invited|considered)",
    r"will consider new grad(?:uate)?s?",
    r"open to new grad(?:uate)?s?",
    r"new graduates who have completed",
    r"recent grad(?:uate)?s?",
    r"entry level",
    r"physician assistant\s+i\b",
    r"pa\s+i\b",
    r"0\s*[-–]\s*1\s*years?",
    r"no experience required",
]

# Tier 3: Lower Chance (2+ years preferred/required, but not a hard 5+ year rejection)
LOWER_CHANCE_PATTERNS = [
    r"(?:2|two)\+?\s*years?\s+(?:of\s+)?(?:clinical\s+|surgical\s+|inpatient\s+|outpatient\s+)?experience\s+(?:is\s+)?preferred",
    r"preferred[^.]{0,50}(?:2|two)\+?\s*years?",
    r"minimum\s+(?:of\s+)?(?:2|two)\+?\s*years?",
    r"(?:2|two)\+?\s*years?\s+prior\s+experience",
    r"experience\s+is\s+preferred",
]

# Hard experience blockers (3+ years strictly required -> exclude entirely)
HARD_EXPERIENCE_BLOCKERS = [
    r"minimum\s+(?:3|4|5)\+?\s*years?\s+(?:of\s+)?(?:clinical\s+)?experience",
    r"at least\s+(?:3|4|5)\s*years?\s+(?:of\s+)?(?:clinical\s+)?experience",
    r"requires\s+(?:3|4|5)\+?\s*years?",
    r"not open to new grads",
    r"not open to new graduates",
    r"experience\s+(?:is\s+)?required",
    r"prior\s+experience\s+required",
    r"must\s+have\s+(?:at\s+least\s+)?(?:2|3|4|5)\s+years",
    r"completion\s+of\s+a\s+fellowship\s+required",
]

# Tier 2: Moderate Chance (1 year preferred)
MODERATE_CHANCE_PATTERNS = [
    r"(?:1|one)\+?\s*years?\s+(?:of\s+)?(?:clinical\s+|surgical\s+|inpatient\s+)?experience",
    r"minimum\s+(?:of\s+)?(?:1|one)\+?\s*years?",
    r"preferred[^.]{0,50}(?:1|one)\s*years?",
]

# Top 5 Desired Specialties
TOP_SPECIALTIES = {
    "ENT / Head & Neck": r"\b(ent|otolaryngology|head\s*(?:and|&)\s*neck|ear[,\s]+nose[,\s]+throat|otorhinolaryngology)\b",
    "Dermatology": r"\b(dermatology|dermatologic|derm)\b",
    "Emergency Medicine (ER)": r"\b(emergency\s*medicine|emergency\s*department|emergency\s*room|\ber\b|\bed\b|trauma|emergency\s*services)\b",
    "Surgery": r"\b(surgery|surgical|operating\s*room|perioperative|general\s*surgery|robotic|transplant|cardiothoracic|cardiac\s*surgery|orthopedic|ortho|neurosurgery|thoracic|vascular|colorectal|plastics|plastic\s*surgery)\b",
    "Urgent Care": r"\b(urgent\s*care|walk[- ]in|immediate\s*care|express\s*care|fast\s*track)\b",
}

OTHER_SPECIALTIES = {
    "Critical Care / ICU": r"\b(critical\s*care|icu|intensive\s*care)\b",
    "Cardiology": r"\b(cardiology|electrophysiology|heart)\b",
    "Internal Medicine": r"\b(internal\s*medicine|hospitalist|inpatient\s*medicine)\b",
    "Primary Care": r"\b(primary\s*care|outpatient|family\s*medicine|ambulatory)\b",
    "Obstetrics & Gynecology": r"\b(obstetrics|gynecology|ob\/gyn|obgyn|women'?s\s*health)\b",
}

def detect_specialty(title: str, description: str = "") -> Tuple[str, bool]:
    """
    Identifies the clinical department/specialty from title and description.
    Title matches always take precedence over description body keywords.
    Returns: (specialty_name, is_top_specialty)
    """
    title_lower = title.lower()
    full_text = f"{title}\n{description}".lower()

    # Pass 1: Title-level match (Highest accuracy)
    # Check title specifically for ER / ED acronyms or Emergency
    if re.search(r"\b(er|ed|emergency|trauma)\b", title_lower):
        return "Emergency Medicine (ER)", True

    for spec, pat in TOP_SPECIALTIES.items():
        if spec == "Emergency Medicine (ER)":
            continue
        if re.search(pat, title_lower):
            return spec, True

    for spec, pat in OTHER_SPECIALTIES.items():
        if re.search(pat, title_lower):
            return spec, False

    # Pass 2: Description-level match (Fallback if title is generic APP/PA)
    if re.search(r"\b(emergency\s*department|emergency\s*medicine|emergency\s*room)\b", full_text):
        return "Emergency Medicine (ER)", True

    for spec, pat in TOP_SPECIALTIES.items():
        if spec == "Emergency Medicine (ER)":
            continue
        if re.search(pat, full_text):
            return spec, True

    for spec, pat in OTHER_SPECIALTIES.items():
        if re.search(pat, full_text):
            return spec, False

    return "General / Inpatient", False

def classify_nyc_location(location_str: str, title_str: str = "") -> Tuple[bool, str]:
    """
    Determines if a location in the NYC hub is inside the 5 boroughs or outside (suburbs).
    Returns: (is_outside_nyc, borough_or_suburb_label)
    """
    text = f"{location_str} {title_str}".lower()
    
    # 1. Suburban / Outside NYC markers
    if re.search(r"\b(westchester|bronxville|white\s*plains|sleepy\s*hollow|valhalla|yonkers|new\s*rochelle|tarrytown|mount\s*vernon|hudson\s*valley|cortlandt|harrison|west\s*harrison|newburgh|cornwall)\b", text):
        return True, "Westchester (Outside City)"
    if re.search(r"\b(long\s*island|nassau|suffolk|manhasset|new\s*hyde\s*park|mineola|huntington|stony\s*brook|garden\s*city|plainview|uniondale|commack|hauppauge)\b", text):
        return True, "Long Island (Outside City)"
    if re.search(r"\b(rockland|nyack|connecticut|stamford|greenwich|new\s*jersey|jersey|hoboken|paramus|montvale|basking\s*ridge|middletown|bergen)\b", text):
        return True, "Outside NYC Suburbs"
        
    # 2. In-City Boroughs
    if re.search(r"\b(manhattan|new\s*york\s*city|new\s*york,\s*ny|ny,?\s*ny|weill\s*cornell|columbia|allen|morningside|midtown|downtown|uptown|kellen\s*tower|hospital\s*for\s*special\s*surgery|sloan\s*kettering|mskcc)\b", text):
        return False, "Manhattan"
    if re.search(r"\b(brooklyn|brooklyn\s*methodist|maimonides)\b", text):
        return False, "Brooklyn"
    if re.search(r"\b(queens|elmhurst|jamaica|flushing|astoria|long\s*island\s*city)\b", text):
        return False, "Queens"
    if re.search(r"\b(bronx|jacobi|lincoln|montefiore|210th\s*street|waters\s*place|eastchester|bainbridge|wakefield|einstein|moses)\b", text):
        return False, "Bronx"
    if re.search(r"\b(staten\s*island)\b", text):
        return False, "Staten Island"

    # Default assumption for NYC hospital systems if unlisted
    return False, "NYC (5 Boroughs)"

def is_title_eligible(title: str) -> bool:
    title_clean = re.sub(r"[_\-]+", " ", title.lower())
    for pat in EXCLUDE_TITLE_WORDS:
        if re.search(pat, title_clean):
            return False
    for pat in INCLUDE_TITLE_WORDS:
        if re.search(pat, title_clean):
            return True
    return False

def evaluate_new_grad(title: str, description: str = "") -> Tuple[bool, str, str]:
    """
    Evaluates new grad eligibility and probability tier.
    Returns: (is_eligible, probability_tier, match_reason)
    probability_tier is one of: "high", "moderate", "lower"
    """
    text = f"{title}\n{description}"
    text_clean = re.sub(r"<[^>]+>", " ", text)
    text_clean = re.sub(r"[_\-]+", " ", text_clean.lower())
    text_clean = re.sub(r"\s+", " ", text_clean)

    # 1. Hard blockers -> not eligible
    for pat in HARD_EXPERIENCE_BLOCKERS:
        m = re.search(pat, text_clean)
        if m:
            return False, "lower", f"Strict experience barrier: '{m.group(0)}'"

    # 2. High Chance: Explicit new-grad welcome / Grade I PA
    for pat in HIGH_CHANCE_PATTERNS:
        m = re.search(pat, text_clean)
        if m:
            return True, "high", f"New Grad Welcome: '{m.group(0)}'"

    # 3. Lower Chance: 2+ years preferred
    for pat in LOWER_CHANCE_PATTERNS:
        m = re.search(pat, text_clean)
        if m:
            return True, "lower", f"2+ Years Preferred: '{m.group(0)}'"

    # 4. Moderate Chance: 1 year preferred
    for pat in MODERATE_CHANCE_PATTERNS:
        m = re.search(pat, text_clean)
        if m:
            return True, "moderate", f"1 Year Preferred: '{m.group(0)}'"

    # 5. Default Moderate: Standard PA listing without specific year blockers
    return True, "moderate", "Standard PA listing (typical hospital boilerplate)"


def _format_salary(low: float, high: Optional[float], is_hourly: bool) -> Tuple[str, int]:
    """Normalize numeric salary values into a compact display badge and annualized minimum."""
    if is_hourly:
        low_s = f"${int(round(low))}" if abs(low - round(low)) < 0.05 else f"${low:.2f}"
        if high and high > low:
            high_s = f"${int(round(high))}" if abs(high - round(high)) < 0.05 else f"${high:.2f}"
            return f"{low_s} – {high_s}/hr", int(round(low * 2080))
        return f"{low_s}/hr", int(round(low * 2080))

    low_k = round(low / 1000)
    if high and high > low:
        high_k = round(high / 1000)
        return f"${low_k}k – ${high_k}k/yr", int(round(low))
    return f"${low_k}k/yr", int(round(low))


def extract_salary_range(
    description: str = "",
    explicit_salary: str = "",
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> Tuple[Optional[str], Optional[int]]:
    """
    Extract a normalized compensation range (e.g. '$131k – $149k/yr' or '$67 – $89/hr')
    and annualized minimum USD integer from structured fields or description text.
    """
    # 1. Structured numeric values (e.g. Jibe salary_min_value / salary_max_value)
    if min_val is not None:
        try:
            lo = float(min_val)
            hi = float(max_val) if max_val is not None else None
            if 30 <= lo <= 250:
                return _format_salary(lo, hi if hi and 30 <= hi <= 300 else None, is_hourly=True)
            if 35000 <= lo <= 500000:
                return _format_salary(lo, hi if hi and 35000 <= hi <= 600000 else None, is_hourly=False)
        except (TypeError, ValueError):
            pass

    # 2. Scan explicit salary string first, then cleaned HTML description
    sources = []
    if explicit_salary:
        sources.append(str(explicit_salary))
    if description:
        clean_desc = re.sub(r"<[^>]+>", " ", description)
        clean_desc = re.sub(r"\s+", " ", clean_desc)
        sources.append(clean_desc)

    range_pat = re.compile(
        r"\$\s*([\d,]+(?:\.\d{1,2})?)\s*(?:k\b)?\s*(?:\*|\bUSD\b)?\s*(?:-|–|—|to)\s*(?:\$|\bUSD\s*\$?)?\s*([\d,]+(?:\.\d{1,2})?)\s*(?:k\b)?\s*\*?\s*(?:/\s*|per\s+)?(hr|hour|hourly|yr|year|annual|annually)?",
        re.IGNORECASE,
    )
    single_pat = re.compile(
        r"(?:salary(?:\s+range)?|hiring\s+range|base\s+salary|compensation|pay\s+range)\s*[:\-]?\s*(?:\bUSD\s*)?\$\s*([\d,]+(?:\.\d{1,2})?)\s*(?:k\b)?\s*(?:/\s*|per\s+)?(hr|hour|hourly|yr|year|annual|annually)?",
        re.IGNORECASE,
    )

    for src in sources:
        for m in range_pat.finditer(src):
            raw_lo, raw_hi, unit = m.group(1), m.group(2), (m.group(3) or "").lower()
            ctx_slice = src[max(0, m.start() - 25) : min(len(src), m.end() + 25)].lower()
            try:
                lo = float(raw_lo.replace(",", ""))
                hi = float(raw_hi.replace(",", ""))
            except ValueError:
                continue
            if "k" in m.group(0).lower() and lo < 1000:
                lo *= 1000
                hi *= 1000
            if hi < lo:
                continue

            is_hourly_ctx = bool(re.search(r"\b(hr|hour|hourly)\b|/hr\b", unit + " " + ctx_slice))
            if is_hourly_ctx and 30 <= lo <= 250 and hi <= 300:
                return _format_salary(lo, hi, is_hourly=True)
            if 35000 <= lo <= 500000 and hi <= 600000:
                return _format_salary(lo, hi, is_hourly=False)

        for m in single_pat.finditer(src):
            raw_lo, unit = m.group(1), (m.group(2) or "").lower()
            ctx_slice = src[max(0, m.start() - 10) : min(len(src), m.end() + 20)].lower()
            try:
                lo = float(raw_lo.replace(",", ""))
            except ValueError:
                continue
            if "k" in m.group(0).lower() and lo < 1000:
                lo *= 1000
            is_hourly_ctx = bool(re.search(r"\b(hr|hour|hourly)\b|/hr\b", unit + " " + ctx_slice))
            if is_hourly_ctx and 30 <= lo <= 250:
                return _format_salary(lo, None, is_hourly=True)
            if 35000 <= lo <= 500000:
                return _format_salary(lo, None, is_hourly=False)

    return None, None


def _normalize_shift_token(text: str) -> Optional[str]:
    low = text.lower()
    if any(k in low for k in ["rotat", "flex", "variable", "day/night", "days/nights"]):
        return "Rotating"
    if any(k in low for k in ["night", "nocturnist", "overnight", "7p-7a", "7pm-7am", "1900-0700", "12am-8am", "11pm"]):
        return "Nights"
    if any(k in low for k in ["swing", "mid-shift", "midshift", "mid shift", "evening", "afternoon", "4pm-12am", "4pm - 12am"]):
        return "Evenings / Swing"
    if "weekend" in low:
        return "Weekends"
    if any(k in low for k in ["day", "morning", "monday-friday", "monday - friday", "monday – friday", "mon-fri", "m-f", "8am-4pm", "8am - 4pm"]):
        return "Days"
    return None


def detect_shift(
    title: str = "",
    description: str = "",
    explicit_shift: str = "",
) -> Optional[str]:
    """Identify work shift cadence cleanly from structured metadata, title, or schedule lines."""
    if explicit_shift:
        res = _normalize_shift_token(explicit_shift)
        if res:
            return res

    title_res = _normalize_shift_token(title)
    if title_res:
        return title_res

    if description:
        clean_desc = re.sub(r"<[^>]+>", " ", description)
        clean_desc = re.sub(r"\s+", " ", clean_desc)
        # Check structured Shift/Schedule/Work lines first to avoid incidental 'call' mentions
        structured = re.findall(
            r"(?:shift|schedule|work\s*hours?|work)\s*:\s*([^.;\n]{3,60})",
            clean_desc,
            re.IGNORECASE,
        )
        for seg in structured:
            res = _normalize_shift_token(seg)
            if res:
                return res

        # Explicit multi-word schedule phrases anywhere in description
        explicit_phrases = re.findall(
            r"\b(?:night\s+shift|day\s+shift|rotating\s+shift|swing\s+shift|evening\s+shift|weekend\s+shift|monday\s*[-–to]+\s*friday|7\s*on\s*/?\s*7\s*off)\b",
            clean_desc,
            re.IGNORECASE,
        )
        for ph in explicit_phrases:
            res = _normalize_shift_token(ph)
            if res:
                return res

    return None


POSTING_REQUIREMENT_PATTERNS = [
    # Life support & hospital credentialing certs
    ("ACLS", r"\b(?:acls|advanced\s+cardiac\s+life\s+support|advanced\s+cardiovascular\s+life\s+support)\b"),
    ("PALS", r"\b(?:pals|pediatric\s+advanced\s+life\s+support)\b"),
    ("ATLS", r"\b(?:atls|advanced\s+trauma\s+life\s+support)\b"),
    ("BLS", r"\b(?:bls|basic\s+life\s+support)\b"),
    ("DEA", r"\b(?:dea\s+(?:registration|license|certification|number|eligible)|controlled\s+substance\s+registration)\b"),
    ("NYS Infection Control", r"\b(?:infection\s+control\s+(?:certificate|certification|course|training)|mandated\s+reporter)\b"),
    # Setting & surgical/procedural specifics
    ("First-Assist", r"\b(?:first[\s-]+assist(?:ing|ant)?|1st\s+assist)\b"),
    ("Robotic Surgery", r"\b(?:da\s*vinci|robotic(?:s)?(?:\s+surgery|\s+assist(?:ed)?)?)\b"),
    ("Operating Room", r"\b(?:operating\s+room|\bor\b\s+(?:assisting|coverage|cases)|intra[\s-]?operative|perioperative)\b"),
    ("Trauma", r"\b(?:level\s+(?:i|1|ii|2)\s+trauma|trauma\s+(?:surgery|team|center|bay|service))\b"),
    ("ICU / Critical Care", r"\b(?:icu|intensive\s+care\s+unit|critical\s+care|sicu|micu|ccu|neuroicu)\b"),
    ("Inpatient", r"\b(?:inpatient|daily\s+rounds|rounding)\b"),
    ("Outpatient / Clinic", r"\b(?:outpatient|ambulatory\s+(?:care|clinic)|office[\s-]+based)\b"),
    ("Laceration / Suturing", r"\b(?:laceration\s+repair|suturing|suture|wound\s+closure)\b"),
    ("I&D / Abscess", r"\b(?:incision\s+(?:and|&)\s+drainage|\bi\s*&\s*d\b)\b"),
    ("Endoscopy / Laryngoscopy", r"\b(?:laryngoscopy|nasal\s+endoscopy|endoscopy|cerumen)\b"),
    ("Splinting / Casting", r"\b(?:splinting|casting|fracture\s+reduction)\b"),
    ("Ultrasound / POCUS", r"\b(?:pocus|point[\s-]+of[\s-]+care\s+ultrasound|bedside\s+ultrasound)\b"),
    ("Lines / Airway", r"\b(?:central\s+line|arterial\s+line|intubation|endotracheal|airway\s+management)\b"),
    ("Biopsies / Cryotherapy", r"\b(?:skin\s+biops|punch\s+biops|shave\s+biops|cryotherapy|excision)\b"),
    # EMR, language & schedule commitments
    ("Epic EMR", r"\bepic\b"),
    ("Cerner EMR", r"\bcerner\b"),
    ("Bilingual / Spanish", r"\b(?:bilingual|spanish[\s-]+speaking|spanish\s+preferred)\b"),
    ("On-Call", r"\b(?:on[\s-]+call|call\s+rotation|call\s+schedule|share\s+call|weekend\s+call|night\s+call)\b"),
    ("Weekend / Holiday", r"\b(?:weekend\s+(?:rotation|coverage|shift|shifts)|rotating\s+weekends|holiday\s+coverage)\b"),
]


def extract_posting_requirements(title: str = "", description: str = "", max_items: int = 8) -> List[str]:
    """
    Scan a specific job posting's title and description for real hospital requirements,
    certifications, procedures, EMRs, and call/schedule expectations.
    """
    raw = f"{title}\n{description}"
    if not raw.strip():
        return []
    clean = re.sub(r"<[^>]+>", " ", raw)
    clean = re.sub(r"\s+", " ", clean).lower()

    matched: List[str] = []
    for label, pat in POSTING_REQUIREMENT_PATTERNS:
        if re.search(pat, clean):
            matched.append(label)
            if len(matched) >= max_items:
                break
    return matched
