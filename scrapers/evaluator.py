import re
from typing import Tuple

# Non-new-grad / leadership titles to strictly exclude
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
]

# Valid PA / APP title markers
INCLUDE_TITLE_WORDS = [
    r"\bphysician assistant\b",
    r"\bpa-c\b",
    r"\bpa\b",
    r"\badvanced practice provider\b",
    r"\bapp\b",
]

# Explicit new-grad friendly signals in description or title
NEW_GRAD_FRIENDLY_PHRASES = [
    r"new grad(?:uate)?s? welcome",
    r"new grad(?:uate)?s? encouraged",
    r"will consider new grad(?:uate)?s?",
    r"open to new grad(?:uate)?s?",
    r"recent grad(?:uate)?s?",
    r"entry level",
    r"0-1\s*years?",
    r"0 to 1\s*years?",
    r"physician assistant\s+i\b",
    r"pa\s+i\b",
    r"no experience required",
]

# Hard experience blockers
HARD_EXPERIENCE_BLOCKERS = [
    r"minimum\s+(?:2|3|4|5)\+?\s*years?\s+(?:of\s+)?(?:clinical\s+)?experience",
    r"at least\s+(?:2|3|4|5)\s*years?\s+(?:of\s+)?(?:clinical\s+)?experience",
    r"requires\s+(?:2|3|4|5)\+?\s*years?",
    r"not open to new grads",
]

def is_title_eligible(title: str) -> bool:
    title_lower = title.lower()
    for pat in EXCLUDE_TITLE_WORDS:
        if re.search(pat, title_lower):
            return False
    for pat in INCLUDE_TITLE_WORDS:
        if re.search(pat, title_lower):
            return True
    return False

def evaluate_new_grad(title: str, description: str = "") -> Tuple[bool, str]:
    text = f"{title}\n{description}".lower()
    
    # Check explicit positive signals
    for pat in NEW_GRAD_FRIENDLY_PHRASES:
        m = re.search(pat, text)
        if m:
            return True, f"Explicit new-grad match: '{m.group(0)}'"

    # Check hard experience blockers
    for pat in HARD_EXPERIENCE_BLOCKERS:
        m = re.search(pat, text)
        if m:
            return False, f"Requires experienced candidate: '{m.group(0)}'"

    # Standard / default eligible (hospital standard boilerplate, no hard blocker)
    return True, "Standard PA listing (no experience blocker detected)"
