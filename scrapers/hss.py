"""Hospital for Special Surgery (HSS) PA Scraper (Manhattan + Tri-State)."""

import re
from typing import Dict, List, Optional
from .models import JobPosting
from .workday_common import fetch_workday_jobs


def _hss_location_filter(title: str, loc_str: str, info: Dict) -> Optional[str]:
    addl = info.get("additionalLocations") or []
    all_locs = [loc_str] + list(addl)
    blob = f"{title} {' '.join(all_locs)}".lower()

    # Strictly exclude Florida / out-of-region locations
    if re.search(r"\b(florida|\bfl\b|jupiter|west\s*palm|palm\s*beach|boca)\b", blob):
        # If there is also a NY location in additionalLocations, keep NY; otherwise skip
        ny_alt = [l for l in all_locs if re.search(r"(new\s*york|kellen|manhattan|white\s*plains|uniondale|\bny\b)", l, re.I)]
        if ny_alt:
            return ny_alt[0]
        return None

    if "kellen tower" in loc_str.lower() or "main campus" in loc_str.lower():
        return "Manhattan, NY (HSS Main Campus)"
    if "2 locations" in loc_str.lower() and addl:
        return ", ".join(addl[:2])
    return loc_str


def fetch_hss_jobs() -> List[JobPosting]:
    """Fetch eligible Full-Time NY/Tri-State PA postings from Hospital for Special Surgery."""
    return fetch_workday_jobs(
        host="hss.wd1.myworkdayjobs.com",
        tenant="hss",
        site="HSS_Careers",
        hospital_name="Hospital for Special Surgery (HSS)",
        id_prefix="HSS",
        search_terms=["physician assistant"],
        max_per_term=160,
        default_location="Manhattan, NY",
        location_filter=_hss_location_filter,
    )
