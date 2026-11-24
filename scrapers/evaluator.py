import re
from typing import Tuple

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
]

# Valid PA / APP title markers
INCLUDE_TITLE_WORDS = [
    r"\bphysician assistant\b",
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
