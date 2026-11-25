"""Montefiore Health System PA Scraper (Bronx Moses/Einstein/Wakefield + Westchester)."""

from typing import Dict, List, Optional
from .models import JobPosting
from .workday_common import fetch_workday_jobs

MONTEFIORE_BRONX_STREETS = {
    "111 east 210th street": "Bronx, NY (Moses Campus)",
    "1825 eastchester road": "Bronx, NY (Einstein / Weiler)",
    "1695 eastchester road": "Bronx, NY (Einstein Campus)",
    "1250 waters place": "Bronx, NY (Hutchinson Campus)",
    "3400 bainbridge avenue": "Bronx, NY (Montefiore Bronx)",
    "600 east 233rd street": "Bronx, NY (Wakefield Campus)",
}


def _montefiore_location_filter(title: str, loc_str: str, info: Dict) -> Optional[str]:
    low = loc_str.strip().lower()
    for street, label in MONTEFIORE_BRONX_STREETS.items():
        if street in low:
            return label
    return loc_str


def fetch_montefiore_jobs() -> List[JobPosting]:
    """Fetch eligible Full-Time PA postings from Montefiore Health System."""
    return fetch_workday_jobs(
        host="montefiore.wd12.myworkdayjobs.com",
        tenant="montefiore",
        site="MMC",
        hospital_name="Montefiore Health System",
        id_prefix="Montefiore",
        search_terms=["physician assistant"],
        max_per_term=160,
        default_location="Bronx, NY",
        location_filter=_montefiore_location_filter,
    )
