"""Memorial Sloan Kettering Cancer Center (MSKCC) PA/APP Scraper (Manhattan & NY Metro)."""

import re
from typing import Dict, List, Optional
from .models import JobPosting
from .workday_common import fetch_workday_jobs


def _mskcc_location_filter(title: str, loc_str: str, info: Dict) -> Optional[str]:
    blob = f"{title} {loc_str} {' '.join(info.get('additionalLocations') or [])}".lower()
    # Normalize "New York, NY" / Manhattan clinics vs suburban regional sites
    if re.search(r"\b(basking\s*ridge|middletown|montvale|bergen|new\s*jersey|\bnj\b)\b", blob):
        return f"{loc_str} (NJ Suburbs)"
    return loc_str


def fetch_mskcc_jobs() -> List[JobPosting]:
    """Fetch eligible Full-Time PA/APP postings from Memorial Sloan Kettering Cancer Center."""
    return fetch_workday_jobs(
        host="msk.wd108.myworkdayjobs.com",
        tenant="msk",
        site="MSKCC_Careers_Primary",
        hospital_name="Memorial Sloan Kettering (MSKCC)",
        id_prefix="MSKCC",
        search_terms=["physician assistant", "advanced practice provider"],
        max_per_term=100,
        default_location="New York, NY",
        location_filter=_mskcc_location_filter,
    )
